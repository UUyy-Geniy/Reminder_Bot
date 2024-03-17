from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from filters.callback_data import NewCaseInterfaceCallback


NEW_CASE = [
    ('Да', NewCaseInterfaceCallback(set_new_case=False, set_new_case_files=True, finish_case=False,
                                    skip_case_description=False, set_case_description=False)),
    ('Нет', NewCaseInterfaceCallback(set_new_case=True, set_new_case_files=False, finish_case=False,
                                     skip_case_description=False, set_case_description=False))
]

CASE_DESCRIPTION = [
    ('Да', NewCaseInterfaceCallback(set_case_description=True, skip_case_description=False, set_new_case=False,
                                    set_new_case_files=False, finish_case=False)),
    ('Нет', NewCaseInterfaceCallback(skip_case_description=True, set_case_description=False, set_new_case=False,
                                     set_new_case_files=False,
                                     finish_case=False))
]

DONE_KEY = [('Готово', NewCaseInterfaceCallback(finish_case=True, set_new_case=False, set_new_case_files=False, skip_case_description=False, set_case_description=False))]


def get_new_case_files_interface() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for title, callback_data in NEW_CASE:
        builder.button(text=title, callback_data=callback_data)
    builder.adjust(1, 1)
    return builder


def set_case_description_interface() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for title, callback_data in CASE_DESCRIPTION:
        builder.button(text=title, callback_data=callback_data)
    builder.adjust(1, 1)
    return builder


def set_new_case_interface() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for title, callback_data in DONE_KEY:
        builder.button(text=title, callback_data=callback_data)
    builder.adjust(1)
    return builder


def get_repeat_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Ежедневно", callback_data="repeat:daily")
    builder.button(text="Еженедельно", callback_data="repeat:weekly")
    builder.button(text="Ежемесячно", callback_data="repeat:monthly")
    builder.button(text="Не повторять", callback_data="repeat:none")
    builder.adjust(1)  # Если хотите, чтобы каждая кнопка была в своем ряду
    return builder.as_markup()