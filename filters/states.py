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
