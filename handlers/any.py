from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from bd.db import db
from sqlalchemy import select, update
from bd.models import Cases, File
from filters.callback_data import FileCallback

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
