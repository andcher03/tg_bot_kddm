from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    consent = State()
    full_name = State()
    birth_date = State()
    education = State()
    confirm = State()
