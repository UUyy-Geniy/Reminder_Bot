from datetime import datetime
import os
from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from attachements.keyboards import create_files_keyboard, create_cases_keyboard, create_case_management_keyboard, \
    create_case_editing_keyboard, get_repeat_keyboard
from filters.states import CurrentCasesStates, EditCaseStates
from bd.db import db
from sqlalchemy import select, update, delete
from bd.models import Cases, File
from filters.callback_data import FileCallback, CurrentCaseCallBack, ManageCaseCallback, EditCaseCallback, \
    RepeatCallback
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiogram.filters.callback_data import CallbackData

from handlers.new_case import upload_file_to_drive, get_credentials

router = Router()


@router.message(Command(commands=['active_cases']))
async def get_current_cases(message: Message, state: FSMContext, bot: Bot):
    data = db.sql_query(select(Cases).where(Cases.user_id == str(message.from_user.id),
                                            Cases.is_finished == 'false').order_by(Cases.deadline_date), is_single=False)
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
    await bot.send_message(chat_id=query.from_user.id, text=f"Напоминание отмечено как выполненное.")


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
    await bot.send_message(chat_id=query.from_user.id, text=f"Редактирование напоминания", reply_markup=settings)
    await state.set_state(EditCaseStates.waiting_for_field_choice)

#TODO фото при редактировании

@router.callback_query(EditCaseStates.waiting_for_field_choice, EditCaseCallback.filter())
async def process_field_choice(query: CallbackQuery, state: FSMContext, bot: Bot):
    action, field, case_id = query.data.split(':')
    await state.update_data(case_id=case_id)
    await state.update_data(field=field)
    await state.update_data(many_files=False)

    if field == 'deadline_date':
        await bot.send_message(chat_id=query.from_user.id, text="Выберите новую дату начала:",
                               reply_markup=await SimpleCalendar(
                                   locale=await get_user_locale(query.from_user)).start_calendar())
        await state.set_state(EditCaseStates.waiting_for_new_date)
    elif field == 'repeat':
        await bot.send_message(chat_id=query.from_user.id, text="Выберите новую периодичность:",
                               reply_markup=get_repeat_keyboard())
        await state.set_state(EditCaseStates.waiting_for_new_repeat)
    elif field == 'files':
        await bot.send_message(chat_id=query.from_user.id, text="Отправьте новые файлы для замены старых.")
        await state.set_state(EditCaseStates.editing_files)
    else:
        await query.message.edit_text(
            text=f"Введите новое значение для '{field}'"
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
            await message.answer(text=f"Название напоминания было обновлено.")
        else:
            await message.answer(text="Введите корректное название.")
    elif field == 'description':
        new_value = message.text.strip()
        if is_valid_text(new_value):
            db.sql_query(update(Cases).where(Cases.id == case_id).values(description=new_value), is_update=True)
            await message.answer(text=f"Описание напоминания было обновлено.")
        else:
            await message.answer(text="Введите корректное описание.")


@router.message(EditCaseStates.editing_files)
async def receive_new_files(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    case_id = data['case_id']
    many_files = data["many_files"]
    new_attachments = (await state.get_data()).get('new_attachments', [])
    credentials = get_credentials()

    if message.document:
        if not os.path.exists('tmp'):
            os.makedirs('tmp')
        file_info = await message.bot.get_file(message.document.file_id)
        file_path = f'tmp/{file_info.file_path}'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_name = message.document.file_name
        await message.bot.download_file(file_info.file_path, file_path)
        try:
            drive_file_url = upload_file_to_drive(file_name, file_path, credentials)
            new_attachments = data.get('new_attachments', [])
            attachment_info = f"{file_name}@@@{drive_file_url}"
            new_attachments.append(attachment_info)
            await state.update_data(new_attachments=new_attachments)

            await message.answer("Файл успешно загружен на Google Drive.")

            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            await message.answer("Произошла ошибка при загрузке файла на Google Drive.")
            print(e)
        if not many_files:
            await state.update_data(many_files=True)
            await message.answer(
                "Можете загрузить ещё файлы или завершить процесс, нажав соответствующую кнопку.",
                reply_markup=get_done_editing_files_keyboard(case_id)
            )
    else:
        await message.answer(
            "Пожалуйста, прикрепите файл или завершите добавление, нажав кнопку ниже.",
            reply_markup=get_done_editing_files_keyboard(case_id)
        )


@router.callback_query(EditCaseStates.editing_files, EditCaseCallback.filter(F.action == "done_editing_files"))
async def finish_editing_files(query: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    case_id = data.get('case_id')
    new_attachments = data.get('new_attachments', [])

    if new_attachments:
        db.sql_query(delete(File).where(File.case_id == case_id), is_delete=True)
        for attachment_info in new_attachments:
            file_name, file_url = attachment_info.split('@@@')
            new_file = File(file_name=file_name, file_url=file_url, case_id=case_id)
            db.create_object(new_file)
        await query.message.answer(text="Все файлы были обновлены.")
    else:
        await query.message.answer(text="Не было добавлено ни одного файла.")

    await state.clear()


@router.callback_query(EditCaseStates.waiting_for_new_date, SimpleCalendarCallback.filter())
async def process_new_date_selection(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    selected, date = await SimpleCalendar(locale=await get_user_locale(callback_query.from_user)).process_selection(
        callback_query, callback_data)
    if selected:
        await state.update_data(new_date=date.strftime('%Y-%m-%d'))
        await callback_query.message.answer("Теперь введите новое время напоминания в формате ЧЧ:ММ.")
        await state.set_state(EditCaseStates.awaiting_new_time)
    else:
        await callback_query.message.answer(text="Пожалуйста, выберите дату.")


@router.message(EditCaseStates.awaiting_new_time, F.text)
async def new_time_chosen(message: Message, state: FSMContext):
    data = await state.get_data()
    case_id = data['case_id']
    new_date_str = data.get('new_date')
    new_time_str = message.text.strip()
    try:
        new_datetime = datetime.strptime(f'{new_date_str} {new_time_str}', '%Y-%m-%d %H:%M')
        db.sql_query(update(Cases).where(Cases.id == case_id).values(deadline_date=new_datetime), is_update=True)
        await message.answer(text=f"Дата напоминания обновлена на {new_datetime}.")
        await state.clear()
    except ValueError:
        await message.answer("Время введено неправильно. Попробуйте еще раз в формате ЧЧ:ММ.")


@router.callback_query(EditCaseStates.waiting_for_new_repeat, RepeatCallback.filter())
async def process_new_repeat_selection(query: CallbackQuery, callback_data: RepeatCallback, state: FSMContext):
    repeat_option = callback_data.repeat_option
    case_id = (await state.get_data())['case_id']
    db.sql_query(update(Cases).where(Cases.id == case_id).values(repeat=repeat_option), is_update=True)
    await query.message.answer(text=f"Периодичность напоминания обновлена на {repeat_option}.")
    await state.clear()


def is_valid_text(text):
    return isinstance(text, str) and text != ""


def get_done_editing_files_keyboard(case_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="Готово", callback_data=f"edit_case:done_editing_files:{case_id}")
    builder.adjust(1)
    return builder.as_markup()
