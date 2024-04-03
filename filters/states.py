from aiogram.fsm.state import State, StatesGroup


class NewCaseStates(StatesGroup):
    set_case_name = State()
    choose_case_description = State()
    set_case_description = State()
    set_case_date = State()
    set_case_type = State()
    attachment = State()
    set_files = State()
    finish_case = State()
    set_repeat = State()


class CurrentCasesStates(StatesGroup):
    get_current_cases = State()
    get_case_action = State()


class TodayCasesStates(StatesGroup):
    get_current_cases = State()
    get_case_action = State()


class FinishedCasesStates(StatesGroup):
    get_current_cases = State()
    get_case_action = State()
    waiting_for_restore_date = State()


class EditCaseStates(StatesGroup):
    waiting_for_new_files = State()
    editing_files = State()
    waiting_for_new_date = State()
    waiting_for_new_repeat = State()
    waiting_for_field_choice = State()
    waiting_for_new_value = State()
