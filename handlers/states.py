from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    choosing_language = State()
    choosing_level = State()
    choosing_subject = State()


class AdminStates(StatesGroup):
    waiting_lesson_video = State()
    waiting_lesson_meta = State()
    waiting_quiz_lesson_id = State()
    waiting_quiz_json = State()
    waiting_broadcast_text = State()


class SettingsStates(StatesGroup):
    change_language = State()
    change_level = State()
    change_subject = State()
