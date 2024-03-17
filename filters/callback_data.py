from aiogram.filters.callback_data import CallbackData


class UserInterfaceCallback(CallbackData, prefix='user-ui'):
    pass


class UserBackCallback(CallbackData, prefix='user_back'):
    is_back: bool


class NewCaseInterfaceCallback(CallbackData, prefix='new_case-ui'):
    set_new_case: bool
    set_new_case_files: bool
    finish_case: bool
    skip_case_description: bool
    set_case_description: bool


class RepeatCallback(CallbackData, prefix="repeat"):
    repeat_option: str
