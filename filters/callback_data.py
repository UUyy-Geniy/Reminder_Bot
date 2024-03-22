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


class FileCallback(CallbackData, prefix='file'):
    file_id: int


class CurrentCaseCallBack(CallbackData, prefix='cur_case'):
    case_id: int


class ManageCaseCallback(CallbackData, prefix="manage_case"):
    action: str
    case_id: int
