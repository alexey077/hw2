import asyncio
import random
import time
from typing import Callable, Optional

from fastapi import FastAPI

app = FastAPI(title="четвертый номер")


class AsyncTimer:
    """
    Время сохраняется в self.elapsed и логируется через self.logger.
    """

    def __init__(self, label: str = "AsyncTimer", logger: Optional[Callable[[str], None]] = None):
        self.label = label
        self.logger = logger or print
        self.start: float | None = None
        self.elapsed: float | None = None

    async def __aenter__(self) -> "AsyncTimer":
        self.start = time.perf_counter()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if self.start is None:
            self.elapsed = 0.0
        else:
            self.elapsed = time.perf_counter() - self.start

        self.logger(f"[{self.label}] elapsed: {self.elapsed:.4f} sec")

        return False


@app.get("/random-sleep")
async def random_sleep():
    """
    Засыпает на случайное время от 2 до 3 секунд
    """
    delay = random.uniform(2, 3.0) 

    async with AsyncTimer(label=f"/random-sleep delay={delay:.2f}s") as timer:
        await asyncio.sleep(delay)

    return {
        "requested_delay": round(delay, 2),
        "time_measured": round(timer.elapsed or 0.0, 4),
        "message": "OK",
    }


@app.get("/fixed-sleep/{seconds}")
async def fixed_sleep(seconds: float):
    """
    спим ровно столько сколько надо
    """
    async with AsyncTimer(label=f"/fixed-sleep {seconds:.2f}s") as timer:
        await asyncio.sleep(seconds)

    return {
        "requested_delay": seconds,
        "time_measured": round(timer.elapsed or 0.0, 4),
        "message": "OK",
    }
    


#ручка считает сколько времени выполнялась
#решил сделать 2. Первая засыпает на рандомной число секунд, вторая на фиксированное