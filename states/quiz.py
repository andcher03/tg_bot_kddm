from aiogram.fsm.state import State, StatesGroup


class QuizState(StatesGroup):
    answering = State()
