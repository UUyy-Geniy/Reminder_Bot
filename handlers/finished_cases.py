from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters.command import Command
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

from attachements.keyboards import create_files_keyboard, create_cases_keyboard, \
    create_finished_case_management_keyboard
from filters.states import FinishedCasesStates
from bd.db import db
from sqlalchemy import select, update
from bd.models import Cases, File
from filters.callback_data import FileCallback, CurrentCaseCallBack, ManageCaseCallback
from datetime import datetime

router = Router()


@router.message(Command(commands=['finished_cases']))
async def get_current_cases(message: Message, state: FSMContext, bot: Bot):
    data = db.sql_query(select(Cases).where(Cases.user_id == str(message.from_user.id),
                                            Cases.is_finished == 'true').order_by(Cases.deadline_date), is_single=False)
    cases_keyboard = create_cases_keyboard(data)
    if not data:
        await bot.send_message(chat_id=message.from_user.id, text="У вас нет выполненных напоминаний.")
        return
    await bot.send_message(chat_id=message.from_user.id, text='Ваши завершенные напоминания',
                           reply_markup=cases_keyboard)
    await state.set_state(FinishedCasesStates.get_current_cases)


@router.callback_query(FinishedCasesStates.get_current_cases, CurrentCaseCallBack.filter())
async def download_file(query: CallbackQuery, callback_data: FileCallback, bot: Bot, state: FSMContext):
    case_id = callback_data.case_id
    case = db.sql_query(select(Cases).where(Cases.id == case_id), is_single=True)
    reminders_msg = f"Дата: {case.deadline_date}\nНазвание: {case.name}\nОписание: {case.description}\nПовторение: {case.repeat}\n"
    management_keyboard = create_finished_case_management_keyboard(case_id)
    await bot.send_message(chat_id=query.from_user.id, text=reminders_msg, reply_markup=management_keyboard)
    await state.set_state(FinishedCasesStates.get_case_action)


@router.callback_query(FinishedCasesStates.get_case_action, ManageCaseCallback.filter(F.action == "files"))
async def show_files(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot):
    case_id = callback_data.case_id
    files = db.sql_query(select(File).where(File.case_id == case_id), is_single=False)
    if files:
        files_keyboard = create_files_keyboard(files)
        await bot.send_message(chat_id=query.from_user.id, text="Файлы по кейсу:", reply_markup=files_keyboard)
    else:
        await bot.send_message(chat_id=query.from_user.id, text="У этого напоминания нет вложений :(")


@router.callback_query(FinishedCasesStates.get_case_action, ManageCaseCallback.filter(F.action == "restore"))
async def ask_restore_date(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot, state: FSMContext):
    case_id = callback_data.case_id
    await state.update_data(case_id=case_id)
    await query.message.answer("На какую дату вы хотите восстановить напоминание?",
                               reply_markup=await SimpleCalendar(
                                   locale=await get_user_locale(query.from_user)).start_calendar())
    await state.set_state(FinishedCasesStates.waiting_for_restore_date)


@router.callback_query(FinishedCasesStates.waiting_for_restore_date, SimpleCalendarCallback.filter())
async def restore_case_with_date(query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext,
                                 bot: Bot):
    selected, date = await SimpleCalendar().process_selection(
        query, callback_data)
    if selected:
        await query.message.answer(
            "Вы выбрали дату: {}\nТеперь введите время в формате ЧЧ:ММ, например 15:30".format(
                date.strftime("%d/%m/%Y")),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await state.set_state(FinishedCasesStates.select_time)


@router.message(FinishedCasesStates.select_time, F.text)
async def process_time(message: Message, state: FSMContext, bot: Bot):
    time_str = message.text
    data = await state.get_data()
    selected_date = data.get("selected_date")
    case_id = (await state.get_data()).get('case_id')
    try:
        selected_time = datetime.strptime(time_str, "%H:%M").time()
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        full_datetime = datetime.combine(selected_date, selected_time)
        await state.update_data(selected_date=full_datetime.strftime("%Y-%m-%d %H:%M"))
        db.sql_query(
            update(Cases).where(Cases.id == case_id).values(is_finished=False, deadline_date=full_datetime),
            is_update=True)
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"Кейс {case_id} восстановлен на дату {full_datetime}.")
    except ValueError:
        await message.answer("Формат времени неверный. Введите время в формате ЧЧ:ММ, например 15:30.")
    await state.clear()
