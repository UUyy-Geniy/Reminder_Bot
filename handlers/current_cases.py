from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaDocument
from aiogram.filters.command import Command
from filters.states import CurrentCasesStates
from bd.db import db
from sqlalchemy import select
from bd.models import Cases

router = Router()


@router.message(Command(commands=['current_cases']))
async def get_current_cases(message: Message, state: FSMContext, bot: Bot):
    data = db.sql_query(select(Cases).where(Cases.user_id == str(message.from_user.id)), is_single=False)
    if not data:
        await bot.send_message(chat_id=message.from_user.id, text="У вас нет активных напоминаний.")
        return

    for row in data:
        case = row[0]  # Получаем объект Cases из первого элемента кортежа
        reminders_msg = f"Дата: {case.deadline_date}\nНазвание: {case.name}\n"
        await bot.send_message(chat_id=message.from_user.id, text=reminders_msg)

        # if case.attachment:
        #     attachments = case.attachment.split(",")
        #     media = [InputMediaDocument(media=attach) for attach in attachments]
        #     await bot.send_media_group(chat_id=message.from_user.id, media=media)

    await state.set_state(CurrentCasesStates.get_current_cases)
