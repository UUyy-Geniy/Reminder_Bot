from aiogram import Router, Bot
from aiogram.types import Message

router = Router()


@router.message()
async def any_message(message: Message, bot=Bot):
    await bot.send_message(chat_id=message.from_user.id, text="Вы неправильно ввели")
