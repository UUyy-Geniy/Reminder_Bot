import aiogram
import asyncio
from config import BOT_TOKEN
from handlers import user, new_case, any, active_cases, finished_cases, today_cases
from Scheduler.scheduler import scheduler

bot = aiogram.Bot(token=BOT_TOKEN)
dp = aiogram.Dispatcher()


dp.include_router(user.router)
dp.include_router(new_case.router)
dp.include_router(today_cases.router)
dp.include_router(active_cases.router)
dp.include_router(finished_cases.router)

dp.include_router(any.router)


async def main():
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        scheduler.shutdown()
