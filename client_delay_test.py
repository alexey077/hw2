import asyncio
import random
import time

import httpx

BASE_URL = "http://127.0.0.1:8000/delay/{seconds}"
REQUESTS_COUNT = 100
MIN_SEC = 1
MAX_SEC = 60


async def make_request(client: httpx.AsyncClient, seconds: int, idx: int):

    start = time.perf_counter()

    resp = await client.get(BASE_URL.format(seconds=seconds))
    
    elapsed = time.perf_counter() - start

    print(f"[{idx:03}] delay={seconds:2d}s, status={resp.status_code}, "
          f"elapsed={elapsed:.2f}s")

    return elapsed


async def main():

    delays = [random.randint(MIN_SEC, MAX_SEC) for _ in range(REQUESTS_COUNT)]

    print("Первые задержки", delays[:10], "\n")

    t0 = time.perf_counter()

    async with httpx.AsyncClient(

        timeout=70.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=100),

    ) as client:

        tasks = [
            make_request(client, seconds, idx)
            for idx, seconds in enumerate(delays, start=1)
        ]

        per_request_times = await asyncio.gather(*tasks)

    total = time.perf_counter() - t0

    print("\nВсего запросов =", REQUESTS_COUNT)

    print(f"Общее время  {total:.2f} сек")

    print(f"Максимальное время : {max(per_request_times):.2f} сек")

    print(f"Максимальная задержка : {max(delays)} сек")


if __name__ == "__main__":

    asyncio.run(main())
