from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bd.db import db
from sqlalchemy import select, update
from bd.models import Cases
from dateutil.relativedelta import relativedelta

scheduler = AsyncIOScheduler(executors={'default': AsyncIOExecutor()})


async def send_reminder(bot, case_id: int):
    case = db.sql_query(query=select(Cases).where(Cases.id == case_id), is_single=True)
    if case:
        await bot.send_message(chat_id=case.user_id, text=f"Напоминание: {case.name}")
        if case.repeat == "daily":
            next_date = case.deadline_date + relativedelta(days=1)
        elif case.repeat == "weekly":
            next_date = case.deadline_date + relativedelta(weeks=1)
        elif case.repeat == "monthly":
            next_date = case.deadline_date + relativedelta(months=1)
        else:
            return
        db.sql_query(update(Cases).where(Cases.id == case_id).values(deadline_date=next_date), is_update=True)
        scheduler.add_job(send_reminder, 'date', run_date=next_date, args=[bot, case_id])
