from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command

from attachements import messages as msg
from attachements import keyboards as kb
from filters.callback_data import NewCaseInterfaceCallback, RepeatCallback
from filters.states import NewCaseStates
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from datetime import datetime
from bd.db import db
from bd.models import Cases, File
from Scheduler.scheduler import scheduler, send_reminder

import os.path
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

router = Router()


@router.message(Command('new_case'))
async def enter(message: Message, state: FSMContext, bot=Bot):
    await bot.send_message(chat_id=message.from_user.id, text="Для начала введите название напоминания")
    await state.set_state(NewCaseStates.set_case_name)


@router.message(NewCaseStates.set_case_name, F.text)
async def choose_case_description(message: Message, state: FSMContext, bot=Bot):
    await state.update_data(name=message.text)
    attachments = []
    await state.update_data(attachments=attachments)
    await bot.send_message(chat_id=message.from_user.id, text="Отлично!\n"
                                                              "Хотите добавить описание?",
                           reply_markup=kb.set_case_description_interface().as_markup())
    await state.set_state(NewCaseStates.choose_case_description)


@router.callback_query(NewCaseStates.choose_case_description,
                       NewCaseInterfaceCallback.filter(F.set_case_description == True))
async def set_case_description(query: CallbackQuery, state: FSMContext, bot=Bot):
    await bot.send_message(chat_id=query.from_user.id, text="Напишите описание к напоминанию")
    await state.set_state(NewCaseStates.set_case_description)


@router.callback_query(NewCaseStates.choose_case_description,
                       NewCaseInterfaceCallback.filter(F.skip_case_description == True))
async def skip_case_description(query: CallbackQuery, state: FSMContext, bot=Bot):
    description = ''
    await state.update_data(description=description)
    await bot.send_message(chat_id=query.from_user.id, text="Без описания - так без описания :(\n"
                                                            "Теперь давай определим, на какое время ты хочешь "
                                                            " его назначить",
                           reply_markup=await SimpleCalendar(
                               locale=await get_user_locale(query.from_user)).start_calendar())
    await state.set_state(NewCaseStates.select_date)


@router.message(NewCaseStates.set_case_description)
async def set_case_date(message: Message, state: FSMContext, bot=Bot):
    await state.update_data(description=message.text)
    await bot.send_message(chat_id=message.from_user.id, text="Отлично!\n"
                                                              "Теперь давай определим, на какое время ты хочешь "
                                                              " его назначить",
                           reply_markup=await SimpleCalendar(
                               locale=await get_user_locale(message.from_user)).start_calendar())
    await state.set_state(NewCaseStates.select_date)


@router.callback_query(NewCaseStates.select_date, SimpleCalendarCallback.filter())
async def process_calendar(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            "Вы выбрали дату: {}\nТеперь введите время в формате ЧЧ:ММ, например 15:30".format(
                date.strftime("%d/%m/%Y")),
            reply_markup=ReplyKeyboardRemove()
        )
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await state.set_state(NewCaseStates.select_time)


@router.message(NewCaseStates.select_time, F.text)
async def process_time(message: Message, state: FSMContext, bot: Bot):
    time_str = message.text
    data = await state.get_data()
    selected_date = data.get("selected_date")
    try:
        selected_time = datetime.strptime(time_str, "%H:%M").time()
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        full_datetime = datetime.combine(selected_date, selected_time)
        await state.update_data(selected_date=full_datetime.strftime("%Y-%m-%d %H:%M"))
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Выберите как часто вы хотите повторять напоминание",
            reply_markup=kb.get_repeat_keyboard()
        )
        await state.set_state(NewCaseStates.set_repeat)

    except ValueError:
        await message.answer("Формат времени неверный. Введите время в формате ЧЧ:ММ, например 15:30.")


@router.callback_query(NewCaseStates.set_repeat, RepeatCallback.filter())
async def set_repeat(query: CallbackQuery, callback_data: RepeatCallback, state: FSMContext, bot=Bot):
    repeat_option = callback_data.repeat_option  # Получаем выбранный вариант повторения из callback_data
    await state.update_data(repeat=repeat_option)
    await bot.send_message(chat_id=query.from_user.id, text=f"Вы выбрали повторение: {repeat_option}")
    await bot.send_message(chat_id=query.from_user.id, text=msg.NEW_CASE_FILES,
                           reply_markup=kb.get_new_case_files_interface().as_markup())
    await state.set_state(NewCaseStates.attachment)


@router.callback_query(NewCaseStates.attachment, NewCaseInterfaceCallback.filter(F.set_new_case == True))
async def new_case(query: CallbackQuery, state: FSMContext, bot=Bot):
    user_id = query.from_user.id
    info = await state.get_data()
    selected_date = info["selected_date"]
    run_date = datetime.strptime(selected_date, "%Y-%m-%d %H:%M")
    print(info["selected_date"])
    case = db.create_object(
        Cases(user_id=user_id, name=info["name"], start_date=datetime.now(), description=info["description"],
              deadline_date=run_date, repeat=info["repeat"]))
    scheduler.add_job(send_reminder, 'date', run_date=run_date, args=[bot, case])
    await bot.send_message(chat_id=query.from_user.id, text="Напоминание добавлено!\n"
                                                            "Хотите еще? - /new_case")
    await state.clear()


@router.callback_query(NewCaseStates.attachment, NewCaseInterfaceCallback.filter(F.set_new_case_files == True))
async def case_files(query: CallbackQuery, state: FSMContext, bot=Bot):
    await bot.send_message(chat_id=query.from_user.id,
                           text="Перенесите нужные файлы в чат и дождитесь загрузки всех вложений")
    many_files = False
    await state.update_data(many_files=many_files)
    await state.set_state(NewCaseStates.set_files)


def get_credentials():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def upload_file_to_drive(file_name, file_path, credentials):
    folder_id = os.getenv("FOLDER_ID")
    service = build('drive', 'v3', credentials=credentials)
    file_metadata = {'name': file_name,
                     'parents': [folder_id]}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id, parents').execute()

    file_id = file.get('id')
    return file_id


@router.message(NewCaseStates.set_files)
async def set_files(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    many_files = data["many_files"]
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
            attachments = data.get('attachments', [])
            attachment_info = f"{file_name}@@@{drive_file_url}"
            attachments.append(attachment_info)
            await state.update_data(attachments=attachments)

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
                reply_markup=kb.set_new_case_interface().as_markup()
            )

    else:
        await message.answer(
            "Пожалуйста, прикрепите файл или завершите добавление, нажав кнопку ниже.",
            reply_markup=kb.set_new_case_interface().as_markup()
        )


@router.callback_query(NewCaseStates.set_files, NewCaseInterfaceCallback.filter(F.finish_case == True))
async def finish_case_creation(query: CallbackQuery, state: FSMContext, bot=Bot):
    await bot.delete_message(chat_id=query.from_user.id, message_id=query.message.message_id)
    info = await state.get_data()
    user_id = query.from_user.id
    case = db.create_object(
        Cases(user_id=user_id, name=info["name"], start_date=datetime.now(), description=info["description"],
              deadline_date=info["selected_date"], repeat=info["repeat"]))
    for attachment_info in info["attachments"]:
        file_name, file_url = attachment_info.split('@@@')
        db.create_object(File(file_name=file_name, file_url=file_url, case_id=case))
    scheduler.add_job(send_reminder, 'date', run_date=info["selected_date"], args=[bot, case])

    await bot.send_message(chat_id=query.from_user.id, text="Напоминание добавлено!\nХотите еще? - /new_case")
    await state.clear()
