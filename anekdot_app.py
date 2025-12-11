from __future__ import annotations

import locale
import re
from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

BASE_URL = "https://www.anekdot.ru"
BEST_DAY_URL = BASE_URL + "/release/anekdot/day/{date}/"
RANDOM_URL = BASE_URL + "/random/anekdot/"

app = FastAPI(title="HW2 – anekdot.ru proxy")


class Joke(BaseModel):
    text: str
    autor_profile: Optional[str] = None
    rating: Optional[int] = None


class JokesResponse(BaseModel):
    jokes: List[Joke]


async def fetch_html(url: str) -> str:
    """Асинхронно забираем HTML с anekdot.ru."""
    timeout = httpx.Timeout(10.0, read=10.0)

    async with httpx.AsyncClient(
        timeout=timeout,
        headers={"User-Agent": "hw2-anekdot-client"}
    ) as client:

        resp = await client.get(url)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"anekdot.ru вернул статус {resp.status_code}",
            )
        return resp.text


def _set_en_locale() -> Optional[str]:
    """ LC_TIME меняем на en_US, чтобы разобрать '01-January-2025'."""

    try:
        current = locale.setlocale(locale.LC_TIME)

    except locale.Error:
        current = None

    try:
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")

    except locale.Error:
        pass

    return current


def _restore_locale(old: Optional[str]) -> None:

    if not old:
        return

    try:

        locale.setlocale(locale.LC_TIME, old)

    except locale.Error:
        pass


def parse_input_date(date_str: str) -> str:
    old_locale = _set_en_locale()

    try:
        dt = datetime.strptime(date_str, "%d-%B-%Y")

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail="Неверный формат даты - ожидаемый формате '01-January-2025'",
        ) from e

    finally:
        _restore_locale(old_locale)

    return dt.strftime("%Y-%m-%d")



def _normalize_profile_url(href: str) -> str:

    if href.startswith("//"):
        return "https:" + href

    if href.startswith("/"):
        return BASE_URL + href
        
    return href



def _guess_author_name_from_joke(joke: Joke) -> Optional[str]:

    if not joke.text:
        return None

    lines = joke.text.split("\n")
    if not lines:
        return None

    first = lines[0].strip()
    if not first:
        return None

    first = first.rstrip("★").strip()
    if not first:
        return None

    if first[0] in "-—\"«" or first.endswith("..."):
        return None

    if len(first) > 40:
        return None

    return first


def _attach_author_profiles(jokes: List[Joke], soup: BeautifulSoup) -> None:
    for joke in jokes:
        if joke.autor_profile:  
            continue

        name = _guess_author_name_from_joke(joke)

        if not name:
            continue

        # Ищем ссылку вида <a>ИмяАвтора</a>
        a = soup.find("a", string=lambda s: s and s.strip() == name)

        if not a:
            continue

        href = a.get("href")

        if not href:
            continue

        joke.autor_profile = _normalize_profile_url(href)



def _parse_jokes_by_ratings(text: str) -> List[Joke]:
    lines = [ln.strip() for ln in text.split("\n")]
    # убираем пустые строки
    lines = [ln for ln in lines if ln]

    jokes: List[Joke] = []
    current_lines: List[str] = []

    def flush(rating_val: int | None):

        nonlocal current_lines

        if not current_lines:
            return

        text_block = "\n".join(current_lines).strip()

        if not text_block:
            current_lines = []
            return

        # отфильтруем явные служебные блоки
        if text_block.startswith("Анекдоты:"):
            current_lines = []
            return

        jokes.append(Joke(text=text_block, rating=rating_val))
        current_lines = []

    for line in lines:

        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", line):
            continue

        # заголовки и служебные фразы
        if "Самые смешные анекдоты за день" in line:
            continue
        if "упорядоченные по результатам голосования пользователей" in line:
            continue
        if "Случайные анекдоты" in line:
            continue
        if "Подборка случайных анекдотов формируется" in line:
            continue
        if "Послать донат автору" in line:
            continue

        # чистое число - это рейтинг
        if line.isdigit():
            flush(int(line))
            continue

        current_lines.append(line)

    # на случай, если в самом конце есть текст без рейтинга
    flush(None)

    return jokes


def parse_best_html(html: str) -> List[Joke]:
    soup = BeautifulSoup(html, "lxml")
    full = soup.get_text("\n", strip=True)

    marker1 = "Самые смешные анекдоты за день!"
    idx = full.find(marker1)

    if idx != -1:
        full = full[idx + len(marker1):]

    marker2 = "упорядоченные по результатам голосования пользователей"
    idx = full.find(marker2)

    if idx != -1:
        full = full[idx + len(marker2):]

    jokes = _parse_jokes_by_ratings(full)

    _attach_author_profiles(jokes, soup)

    return jokes


def parse_random_html(html: str) -> List[Joke]:

    soup = BeautifulSoup(html, "lxml")
    full = soup.get_text("\n", strip=True)

    # отсечём шапку
    marker = "Случайные анекдоты"
    idx = full.find(marker)

    if idx != -1:
        full = full[idx + len(marker):]

    tail_marker = "Подборка случайных анекдотов формируется"
    idx = full.find(tail_marker)

    if idx != -1:
        full = full[:idx]

    jokes = _parse_jokes_by_ratings(full)

    _attach_author_profiles(jokes, soup)

    return jokes


@app.get("/best", response_model=JokesResponse)
async def best(
    date: str = Query(
        ...,
        description="Дата в формате '01-January-2025' (день-месяц-год на американском)",
    )
):
    date_for_url = parse_input_date(date)
    url = BEST_DAY_URL.format(date=date_for_url)
    html = await fetch_html(url)
    jokes = parse_best_html(html)

    if not jokes:

        raise HTTPException(status_code=404, detail="Анекдоты для этой даты не найдены")

    # сортируем по rating по убыванию
    jokes_sorted = sorted(
        jokes,
        key=lambda j: (j.rating is None, -(j.rating or 0)),
    )

    return JokesResponse(jokes=jokes_sorted)


@app.get("/random", response_model=JokesResponse)

async def random_jokes(
    count: int = Query(
        5,
        ge=1,
        le=50,
        description="",
    )
):
    html = await fetch_html(RANDOM_URL)
    jokes = parse_random_html(html)

    if not jokes:

        raise HTTPException(
            status_code=502,
            detail="Не получилось распарсить anekdot.ru"
        )

    jokes_sorted = sorted(
        jokes,
        key=lambda j: (j.rating is None, -(j.rating or 0)),
    )

    return JokesResponse(jokes=jokes_sorted[:count])


#Сделал два эндпоинта: /best берёт лучшие анекдоты за конкретный день (дату даю в формате 01-January-2025), 
#а /random вытаскивает случайные шутки. Страницы я забираю асинхронно через httpx, дальше 
#парсю HTML с помощью BeautifulSoup: из текста вытаскиваю сам анекдот, рейтинг и, по возможности, ссылку на автора (ищу ник в первой строке и сопоставляю его с <a> на странице). 
#Там, где ссылки реально нет, autor_profile оставляю null. 
###Ответы описал через Pydantic-модели и перед возвратом сортирую анекдоты по рейтингу по убыванию, чтобы сверху были самые залайканные.