from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from bd.db import db
from sqlalchemy import select, delete
from bd.models import Cases, File
from filters.callback_data import FileCallback, ManageCaseCallback

router = Router()


@router.message()
async def any_message(message: Message, bot=Bot):
    await bot.send_message(chat_id=message.from_user.id, text="Вы неправильно ввели :(")


@router.callback_query(FileCallback.filter())
async def download_file(query: CallbackQuery, callback_data: FileCallback, bot: Bot):
    file_id = callback_data.file_id
    file = db.sql_query(select(File).where(File.id == file_id), is_single=True)
    file_url = file.file_url
    await bot.send_document(chat_id=query.from_user.id, document=file_url)


@router.callback_query(ManageCaseCallback.filter(F.action == "delete"))
async def delete_case(query: CallbackQuery, callback_data: ManageCaseCallback, bot: Bot, state: FSMContext):
    case_id = callback_data.case_id
    # Сначала удаляем все связанные файлы
    db.sql_query(delete(File).where(File.case_id == case_id), is_delete=True)
    # Затем удаляем сам кейс
    db.sql_query(delete(Cases).where(Cases.id == case_id), is_delete=True)
    await bot.send_message(chat_id=query.from_user.id, text=f"Кейс {case_id} удален.")
    await state.clear()