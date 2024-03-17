from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bd.db import db
from sqlalchemy import select
from bd.models import Cases
from dateutil.relativedelta import relativedelta
scheduler = AsyncIOScheduler()


async def send_reminder(bot, case_id: int):
    # Получаем информацию о напоминании из базы данных
    case = db.sql_query(query=select(Cases).where(Cases.id == case_id), is_single=True)
    if case:
        await bot.send_message(chat_id=case.user_id, text=f"Напоминание: {case.name}")
        # Если напоминание повторяющееся, планируем следующее
        if case.repeat == "daily":
            next_date = case.start_date + relativedelta(days=1)
        elif case.repeat == "weekly":
            next_date = case.start_date + relativedelta(weeks=1)
        elif case.repeat == "monthly":
            next_date = case.start_date + relativedelta(months=1)
        else:
            return  # Если напоминание не повторяющееся, завершаем функцию
        # Планируем следующее напоминание
        scheduler.add_job(send_reminder, 'date', run_date=next_date, args=[bot, case_id])