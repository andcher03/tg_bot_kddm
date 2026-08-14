from aiogram.fsm.state import State, StatesGroup


class AfishaSearchState(StatesGroup):
    scale = State()
    organizer = State()
    company = State()
    activity = State()


class ReviewState(StatesGroup):
    comment = State()