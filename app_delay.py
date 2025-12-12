import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/delay/{seconds}")

async def delay(seconds: int):

    # задержка на указанное количество секунд

    await asyncio.sleep(seconds)

    return {"message": f"закончил ждать {seconds} секондс"}
