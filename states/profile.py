from aiogram.fsm.state import State, StatesGroup


class ProfileState(StatesGroup):
    edit_university = State()
    edit_full_name = State()