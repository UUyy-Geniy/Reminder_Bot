from datetime import datetime, timedelta

from aiogram.types import CallbackQuery
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from attachements.keyboards import create_sending_case_management_keyboard, create_files_keyboard
from bd.db import db
from sqlalchemy import select, update
from dateutil.relativedelta import relativedelta
from aiogram import Router, Bot, F
from bd.models import Cases, File

from filters.callback_data import ManageSendingCaseCallback

scheduler = AsyncIOScheduler(executors={'default': AsyncIOExecutor()})
router = Router()


async def check_and_send_reminders(bot):
    now = datetime.now()
    window = now + timedelta(seconds=30)
    cases = db.sql_query(query=select(Cases).where(Cases.deadline_date >= now, Cases.deadline_date <= window,
                                                   Cases.is_finished == 'false'), is_single=False)
    for case in cases:
        case = case[0]
        management_keyboard = create_sending_case_management_keyboard(case.id)
        reminder_msg = (
            f"Дата и время: {case.deadline_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Название: {case.name}\n"
            f"Описание: {case.description}\n"
            f"Повтор: {case.repeat}\n"
        )
        await bot.send_message(chat_id=case.user_id, text=reminder_msg, reply_markup=management_keyboard)
        if case.repeat == "daily":
            next_date = case.deadline_date + relativedelta(days=1)
        elif case.repeat == "weekly":
            next_date = case.deadline_date + relativedelta(weeks=1)
        elif case.repeat == "monthly":
            next_date = case.deadline_date + relativedelta(months=1)
        else:
            return
        db.sql_query(update(Cases).where(Cases.id == case.id).values(deadline_date=next_date), is_update=True)


@router.callback_query(ManageSendingCaseCallback.filter(F.action == "complete"))
async def complete_case(query: CallbackQuery, callback_data: ManageSendingCaseCallback, bot: Bot):
    case_id = callback_data.case_id
    db.sql_query(query=update(Cases).where(Cases.id == case_id).values(is_finished=True), is_update=True)
    await bot.send_message(chat_id=query.from_user.id, text=f"Напоминание отмечено как выполненное.")


@router.callback_query(ManageSendingCaseCallback.filter(F.action == "files"))
async def show_files(query: CallbackQuery, callback_data: ManageSendingCaseCallback, bot: Bot):
    case_id = callback_data.case_id
    files = db.sql_query(select(File).where(File.case_id == case_id), is_single=False)
    if files:
        files_keyboard = create_files_keyboard(files)
        await bot.send_message(chat_id=query.from_user.id, text="Файлы по кейсу:", reply_markup=files_keyboard)
    else:
        await bot.send_message(chat_id=query.from_user.id, text="У этого напоминания нет вложений :(")
