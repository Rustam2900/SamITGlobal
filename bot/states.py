from aiogram.fsm.state import State, StatesGroup


class UserRegistrationState(StatesGroup):
    full_name = State()
    contact_info = State()



