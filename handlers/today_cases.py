from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaDocument, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from attachements.keyboards import create_files_keyboard, create_cases_keyboard
from filters.states import CurrentCasesStates
from bd.db import db
from sqlalchemy import select
from bd.models import Cases, File
from filters.callback_data import FileCallback, CurrentCaseCallBack
from datetime import datetime

router = Router()


@router.message(Command(commands=['today_cases']))
async def get_current_cases(message: Message, state: FSMContext, bot: Bot):
    data = db.sql_query(select(Cases).where(Cases.user_id == str(message.from_user.id), Cases.is_finished == 'false',
                                            Cases.deadline_date == datetime.today().date()),
                        is_single=False)
    cases_keyboard = create_cases_keyboard(data)
    if not data:
        await bot.send_message(chat_id=message.from_user.id, text="У вас нет активных напоминаний на сегодня.")
        return
    await bot.send_message(chat_id=message.from_user.id, text='Ващи текущие напоминания', reply_markup=cases_keyboard)
    await state.set_state(CurrentCasesStates.get_current_cases)


@router.callback_query(CurrentCaseCallBack.filter())
async def download_file(query: CallbackQuery, callback_data: CurrentCaseCallBack, bot: Bot):
    case_id = callback_data.case_id
    case = db.sql_query(select(Cases).where(Cases.id == case_id), is_single=True)
    reminders_msg = f"Дата: {case.deadline_date}\nНазвание: {case.name}\nОписание: {case.description}\nПовторение: {case.repeat}\n"
    files = db.sql_query(select(File).where(File.case_id == case.id), is_single=False)
    files_keyboard = create_files_keyboard(files)
    await bot.send_message(chat_id=query.from_user.id, text=reminders_msg, reply_markup=files_keyboard)


@router.callback_query(FileCallback.filter())
async def download_file(query: CallbackQuery, callback_data: FileCallback, bot: Bot):
    file_id = callback_data.file_id
    file = db.sql_query(select(File).where(File.id == file_id), is_single=True)
    file_url = file.file_url
    await bot.send_document(chat_id=query.from_user.id, document=file_url)
