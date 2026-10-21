from aiogram.fsm.state import State, StatesGroup


class ReviewState(StatesGroup):
    comment = State()
