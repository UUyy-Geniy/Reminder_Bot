from aiogram import Router
from aiogram.types import Message
from aiogram.filters.command import Command
from sqlalchemy import select
from bd.models import Users
from bd.db import db


router = Router()


@router.message(Command(commands="start"))
async def start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    existing_user = db.sql_query(query=select(Users).where(Users.id == user_id), is_single=True)

    if not existing_user:
        db.create_object(Users(id=user_id, username=username, first_name=first_name, last_name=last_name))
        await message.answer(text="Привет, я помогу тебе с созданием напоминаний!\n"
                                  "Добавить напоминание - /new_case\n"
                                  "Напоминания на сегодня - /today_cases\n"
                                  "Все напоминания - /active_cases\n"
                                  "Выполненные напоминания - /finished_cases")
    else:
        await message.answer(text="С возвращением!\n"
                                  "Добавить напоминание - /new_case\n"
                                  "Напоминания на сегодня - /today_cases\n"
                                  "Все напоминания - /active_cases\n"
                                  "Выполненные напоминания - /finished_cases")
