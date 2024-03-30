from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from attachements import messages as msg
from attachements import keyboards as kb
from filters.callback_data import NewCaseInterfaceCallback, RepeatCallback
from filters.states import NewCaseStates
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiogram.filters.callback_data import CallbackData
from datetime import datetime
from bd.db import db
from bd.models import Cases, File
from Scheduler.scheduler import scheduler, send_reminder

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
    await state.set_state(NewCaseStates.set_case_date)


@router.message(NewCaseStates.set_case_description)
async def set_case_date(message: Message, state: FSMContext, bot=Bot):
    await state.update_data(description=message.text)
    await bot.send_message(chat_id=message.from_user.id, text="Отлично!\n"
                                                              "Теперь давай определим, на какое время ты хочешь "
                                                              " его назначить",
                           reply_markup=await SimpleCalendar(
                               locale=await get_user_locale(message.from_user)).start_calendar())
    await state.set_state(NewCaseStates.set_case_date)


@router.callback_query(NewCaseStates.set_case_date, SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext,
                                  bot=Bot):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}'
        )
        await bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.message_id)
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Выберите как часто вы хотите повторять напоминание",
            reply_markup=kb.get_repeat_keyboard()
        )
        await state.set_state(NewCaseStates.set_repeat)
    # else:
    #     await calendar.process_selection(callback_query, callback_data)


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
    case = db.create_object(
        Cases(user_id=user_id, name=info["name"], start_date=datetime.now(), description=info["description"],
              deadline_date=info["selected_date"], repeat=info["repeat"]))
    # scheduler.add_job(send_reminder, 'date', run_date=datetime.now().replace(hour=20, minute=40, second=0,
    # microsecond=0), args=[bot, case])
    scheduler.add_job(send_reminder, 'date', run_date=info["selected_date"], args=[bot, case])
    await bot.send_message(chat_id=query.from_user.id, text="Напоминание добавлено!\n"
                                                            "Хотите еще? - /new_case")
    await state.clear()


@router.callback_query(NewCaseStates.attachment, NewCaseInterfaceCallback.filter(F.set_new_case_files == True))
async def case_files(query: CallbackQuery, state: FSMContext, bot=Bot):
    await bot.send_message(chat_id=query.from_user.id, text="Перенесите нужные файлы в чат")
    many_files = False
    await state.update_data(many_files=many_files)
    await state.set_state(NewCaseStates.set_files)


@router.message(NewCaseStates.set_files)
async def set_files(message: Message, state: FSMContext, bot=Bot):
    user_data = await state.get_data()
    attachments = user_data["attachments"]
    many_files = user_data["many_files"]

    if message.document:
        # Добавляем file_id документа в список вложений
        file_id = message.document.file_id
        file_name = message.document.file_name
        attachment_info = f"{file_name}:{file_id}"
        attachments.append(attachment_info)
        # Обновляем состояние с новым списком вложений
        if not many_files:
            await state.update_data(many_files=True)
            await bot.send_message(
                chat_id=message.from_user.id,
                text="Вложение добавлено. Отправьте еще файл или завершите добавление, нажав кнопку ниже.",
                reply_markup=kb.set_new_case_interface().as_markup()
            )
        await state.update_data(attachments=attachments)
    else:
        await bot.send_message(
            chat_id=message.from_user.id,
            text="Пожалуйста, прикрепите файл или завершите добавление, нажав кнопку ниже.",
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
        file_name, file_url = attachment_info.split(":")
        db.create_object(File(file_name=file_name, file_url=file_url, case_id=case))
    scheduler.add_job(send_reminder, 'date', run_date=info["selected_date"], args=[bot, case])

    await bot.send_message(chat_id=query.from_user.id, text="Напоминание добавлено!\nХотите еще? - /new_case")
    await state.clear()
