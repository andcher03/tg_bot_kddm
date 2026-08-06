from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    edit_education = State()
    edit_full_name = State()
    edit_birth_date = State()