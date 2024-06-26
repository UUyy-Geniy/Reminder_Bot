import aiogram
import asyncio
import os
from dotenv import load_dotenv
from handlers import user, new_case, any, active_cases, finished_cases, today_cases
from Scheduler.scheduler import scheduler, router
from Scheduler.scheduler import check_and_send_reminders

bot = aiogram.Bot(os.getenv("BOT_TOKEN"))
dp = aiogram.Dispatcher()

dp.include_router(user.router)
dp.include_router(new_case.router)
# dp.include_router(today_cases.router)
dp.include_router(active_cases.router)
dp.include_router(finished_cases.router)

dp.include_router(any.router)
dp.include_router(router)


async def main():
    scheduler.add_job(check_and_send_reminders, 'interval', seconds=30, args=[bot])
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        scheduler.shutdown()
