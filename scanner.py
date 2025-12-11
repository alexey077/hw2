import asyncio
from typing import List, Tuple

import aiohttp
from tqdm import tqdm

URLS_FILE = "urls.txt"
RESULTS_FILE = "результаты.txt"

#читаем файл
def read_urls(filename: str) -> List[str]:
    urls: List[str] = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            url = line.strip()
            if not url or url.startswith("#"):
                continue
            urls.append(url)
    return urls


#ввод
def ask_limit() -> int:
    while True:
        raw = input("Введите число запросов").strip()

        if not raw:
            print("Возьму 4 по умолчанию.")
            return 5

        try:

            value = int(raw)
            if value <= 0:
                print("Нужно положительное число, попробуй ещё раз.")
                continue
            return value
            
        except ValueError:
            print("Нужно целое число, попробуй ещё раз.")


async def check_url(
    session: aiohttp.ClientSession,
    url: str,
    sem: asyncio.Semaphore,
    pbar: tqdm,
) -> Tuple[str, str]:

    async with sem:
        try:
            async with session.get(url) as resp:
                if 200 <= resp.status < 300:
                    status = f"OK ({resp.status})"
                else:
                    status = f"BAD ({resp.status})"
        except asyncio.TimeoutError:
            status = "ERROR (timeout)"
        except aiohttp.ClientError as e:
            status = f"ERROR ({type(e).__name__})"
        except Exception as e:
            status = f"ERROR ({type(e).__name__})"

    pbar.update(1) 
    return url, status



async def main(limit: int):
    urls = read_urls(URLS_FILE)
    if not urls:

        print(f"В файле {URLS_FILE} нет урлов, нечего проверять.")
        return

    print(f"Нашёл {len(urls)} URL, буду проверять по {limit} штук одновременно.\n")


    timeout = aiohttp.ClientTimeout(total=10)

    sem = asyncio.Semaphore(limit)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        with tqdm(total=len(urls), desc="Проверяем сайты", ncols=80) as pbar:
            tasks = [
                asyncio.create_task(check_url(session, url, sem, pbar))
                for url in urls
            ]
            results = await asyncio.gather(*tasks)


    ok_count = 0

    bad_count = 0

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        for url, status in results:
            f.write(f"{url} - {status}\n")
            if status.startswith("OK"):
                ok_count += 1
            else:
                bad_count += 1




    print("\nГотово.")
    print(f"Всего урлов: {len(results)}")
    print(f"Доступны : {ok_count}")
    print(f"Недоступны с ошибками: {bad_count}")
    print(f"Результаты записаны в {RESULTS_FILE}")




if __name__ == "__main__":
    limit = ask_limit()
    asyncio.run(main(limit))

#тут даже не знаю что комментировать
# расписал кейсы ввода подробно
#подробно прописал кейсы ошибок