from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from attachements.keyboards import create_files_keyboard, create_cases_keyboard, create_case_management_keyboard, \
    create_case_editing_keyboard, get_repeat_keyboard
from filters.states import CurrentCasesStates, EditCaseStates
from bd.db import db
from sqlalchemy import select, update
from bd.models import Cases, File
from filters.callback_data import FileCallback, CurrentCaseCallBack, ManageCaseCallback, EditCaseCallback, \
    RepeatCallback
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiogram.filters.callback_data import CallbackData

router = Router()


@router.message(Command(commands=['active_cases']))
async def get_current_cases(message: Message, state: FSMContext, bot: Bot):
    data = db.sql_query(select(Cases).where(Cases.user_id == str(message.from_user.id), Cases.is_finished == 'false'),
                        is_single=False)
    cases_keyboard = create_cases_keyboard(data)
    if not data:
        await bot.send_message(chat_id=message.from_user.id, text="У вас нет активных напоминаний.")
        return
    await bot.send_message(chat_id=message.from_user.id, text='Ваши текущие напоминания', reply_markup=cases_keyboard)
    await state.set_state(CurrentCasesStates.get_current_cases)


@router.callback_query(CurrentCasesStates.get_current_cases, CurrentCaseCallBack.filter())
async def download_file(query: CallbackQuery, callback_data: FileCallback, bot: Bot, state: FSMContext):
    case_id = callback_data.case_id
    case = db.sql_query(select(Cases).where(Cases.id == case_id), is_single=True)
    reminders_msg = f"Дата: {case.deadline_date}\nНазвание: {case.name}\nОписание: {case.description}\nПовторение: {case.repeat}\n"
    management_keyboard = create_case_management_keyboard(case_id)
    await bot.send_message(chat_id=query.from_user.id, text=reminders_msg, reply_markup=management_keyboard)
    await state.set_state(CurrentCasesStates.get_case_action)


@router.callback_query(CurrentCasesStates.get_case_action, ManageCaseCallback.filter(F.action == "complete"))
async def complete_case(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot):
    case_id = callback_data.case_id
    db.sql_query(query=update(Cases).where(Cases.id == case_id).values(is_finished=True), is_update=True)
    await bot.send_message(chat_id=query.from_user.id, text=f"Кейс {case_id} отмечен как выполненный.")


@router.callback_query(CurrentCasesStates.get_case_action, ManageCaseCallback.filter(F.action == "files"))
async def show_files(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot):
    case_id = callback_data.case_id
    files = db.sql_query(select(File).where(File.case_id == case_id), is_single=False)
    if files:
        files_keyboard = create_files_keyboard(files)
        await bot.send_message(chat_id=query.from_user.id, text="Файлы по кейсу:", reply_markup=files_keyboard)
    else:
        await bot.send_message(chat_id=query.from_user.id, text="У этого напоминания нет вложений :(")


@router.callback_query(CurrentCasesStates.get_case_action, ManageCaseCallback.filter(F.action == "edit"))
async def edit_case(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot, state: FSMContext):
    case_id = callback_data.case_id
    settings = create_case_editing_keyboard(case_id=case_id)
    await bot.send_message(chat_id=query.from_user.id, text=f"Редактирование кейса {case_id}.", reply_markup=settings)
    await state.set_state(EditCaseStates.waiting_for_field_choice)


@router.callback_query(EditCaseStates.waiting_for_field_choice, EditCaseCallback.filter())
async def process_field_choice(query: CallbackQuery, state: FSMContext, bot: Bot):
    action, field, case_id = query.data.split(':')
    await state.update_data(case_id=case_id)
    await state.update_data(field=field)

    if field == 'deadline_date':
        await bot.send_message(chat_id=query.from_user.id, text="Выберите новую дату начала:",
                               reply_markup=await SimpleCalendar(
                                   locale=await get_user_locale(query.from_user)).start_calendar())
        await state.set_state(EditCaseStates.waiting_for_new_date)
    elif field == 'repeat':
        await bot.send_message(chat_id=query.from_user.id, text="Выберите новую периодичность:",
                               reply_markup=get_repeat_keyboard())
        await state.set_state(EditCaseStates.waiting_for_new_repeat)
    else:
        await query.message.edit_text(
            text=f"Введите новое значение для поля '{field}' кейса {case_id}:"
        )
        await state.set_state(EditCaseStates.waiting_for_new_value)


@router.message(EditCaseStates.waiting_for_new_value)
async def update_case_field(message: Message, state: FSMContext):
    data = await state.get_data()
    case_id = data['case_id']
    field = data['field']

    if field == 'name':
        new_value = message.text.strip()
        if is_valid_text(new_value):
            db.sql_query(update(Cases).where(Cases.id == case_id).values(name=new_value), is_update=True)
            await message.answer(text=f"Название кейса {case_id} было обновлено.")
        else:
            await message.answer(text="Введите корректное название.")
    elif field == 'description':
        new_value = message.text.strip()
        if is_valid_text(new_value):
            db.sql_query(update(Cases).where(Cases.id == case_id).values(description=new_value), is_update=True)
            await message.answer(text=f"Описание кейса {case_id} было обновлено.")
        else:
            await message.answer(text="Введите корректное описание.")


@router.callback_query(EditCaseStates.waiting_for_new_date, SimpleCalendarCallback.filter())
async def process_new_date_selection(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    selected, date = await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).process_selection(
        callback_query, callback_data)
    if selected:
        case_id = (await state.get_data())['case_id']
        new_date = date.strftime("%Y-%m-%d")
        db.sql_query(update(Cases).where(Cases.id == case_id).values(deadline_date=new_date), is_update=True)
        await callback_query.message.answer(text=f"Дата начала кейса {case_id} обновлена на {new_date}.")
        await state.clear()
    # else:
    #     await callback_query.message.answer(text="Пожалуйста, выберите дату.")


@router.callback_query(EditCaseStates.waiting_for_new_repeat, RepeatCallback.filter())
async def process_new_repeat_selection(query: CallbackQuery, callback_data: RepeatCallback, state: FSMContext):
    repeat_option = callback_data.repeat_option
    case_id = (await state.get_data())['case_id']
    db.sql_query(update(Cases).where(Cases.id == case_id).values(repeat=repeat_option), is_update=True)
    await query.message.answer(text=f"Периодичность кейса {case_id} обновлена на {repeat_option}.")
    await state.clear()


def is_valid_text(text):
    return isinstance(text, str) and text != ""
