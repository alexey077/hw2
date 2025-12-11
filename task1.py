import asyncio
import time
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# До какого числа считаем сумму квадратов
N = 1_000_000



def sum_of_squares_range(start: int, end: int) -> int:

    return sum(i * i for i in range(start, end + 1))


def sum_of_squares_formula(n: int) -> int:

    return n * (n + 1) * (2 * n + 1) // 6


def split_range(n: int, chunks: int):

    if chunks <= 0:

        raise ValueError("Чанки должны быть больше 0")

    step = n // chunks
    ranges = []
    start = 1

    for i in range(chunks):

        end = start + step - 1

        if i == chunks - 1:
            end = n  # последний чанк забирает остаток

        ranges.append((start, end))
        start = end + 1

    return ranges

#синхрон
async def run_sync():

    t0 = time.perf_counter()

    result = sum_of_squares_range(1, N)

    dt = time.perf_counter() - t0

    return result, dt


#с потоками
async def run_threads(num_workers: int):

    ranges = split_range(N, num_workers)
    loop = asyncio.get_running_loop()

    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_workers) as executor:

        tasks = [
            loop.run_in_executor(executor, sum_of_squares_range, start, end)
            for (start, end) in ranges
        ]

        partial_results = await asyncio.gather(*tasks)

    result = sum(partial_results)
    dt = time.perf_counter() - t0

    return result, dt, num_workers


#с процессами
async def run_processes(num_workers: int):

    ranges = split_range(N, num_workers)

    loop = asyncio.get_running_loop()

    t0 = time.perf_counter()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:

        tasks = [
            loop.run_in_executor(executor, sum_of_squares_range, start, end)
            for (start, end) in ranges
        ]
        partial_results = await asyncio.gather(*tasks)

    result = sum(partial_results)
    dt = time.perf_counter() - t0
    return result, dt, num_workers


async def main():
    expected = sum_of_squares_formula(N)
    
    # Синхрон
    sync_result, sync_time = await run_sync()

    print(f"\n Результат правильный: {sync_result == expected}") # проверка что все норм посчиталось, необязательно но красиво

    print(f" Выполнилось за {sync_time:.4f} сек")

    cpu_workers = os.cpu_count() or 4
    candidate_workers = {1, 2, 4, 8, cpu_workers}
    worker_values = sorted(w for w in candidate_workers if w > 0)

    print(worker_values)

  # для сравнения
    for workers in worker_values:

        # Потоки
        threads_result, threads_time, threads_workers = await run_threads(workers)

        print(f" Число потоков: {threads_workers}")
        print(f" Результат корректен: {threads_result == expected}")
        print(f" Время выполнения: {threads_time:.4f} сек")

        # Процессы
        processes_result, processes_time, processes_workers = await run_processes(workers)

        print(f" Число процессов: {processes_workers}")
        print(f"Проверка результата: {processes_result == expected}")
        print(f" Время выполнения: {processes_time:.4f} сек")

        all_equal = (
            sync_result == threads_result == processes_result == expected
        )

        print("\n выполнилось при num_workers =", workers)
        print(f"  Синхронно : {sync_time:.4f}")
        print(f"  Потоки    : {threads_time:.4f}")
        print(f"  Процессы  : {processes_time:.4f}")



if __name__ == "__main__":
    asyncio.run(main())


#Asyncio использовал как “обёртку”, чтобы удобно запускать все варианты, а для распараллеливания взял ThreadPoolExecutor (потоки) и ProcessPoolExecutor (процессы).

#По времени у меня вышло так: синхронный код занял примерно 0.036 секунды, потоки с разным количеством (1, 2, 4, 8) 
#дали примерно то же время, а процессы оказались заметно медленнее. 
#В итоге вывод такой: для такой небольшой вычислительной задачи проще и быстрее всего обычный синхронный вариант, 
#потоки не помогают из-за GIL, а процессы тут не окупаются из-за накладных расходов на их создание и обмен данными.

