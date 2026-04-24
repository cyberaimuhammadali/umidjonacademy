from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


SUBJECTS = [
    "Data Science",
    "Web Development",
    "English Language",
    "Digital Marketing",
]

LEVELS = ["School", "University", "Self-Learner"]


def language_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Uzbek 🇺🇿"), KeyboardButton(text="English 🇬🇧")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def level_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="School 🏫"), KeyboardButton(text="University 🎓")],
            [KeyboardButton(text="Self-Learner 📚")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def subject_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SUBJECTS[0]), KeyboardButton(text=SUBJECTS[1])],
            [KeyboardButton(text=SUBJECTS[2]), KeyboardButton(text=SUBJECTS[3])],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    if language == "uz":
        lessons, progress, settings = "Mening darslarim", "Mening natijam", "Sozlamalar"
    else:
        lessons, progress, settings = "My Lessons", "My Progress", "Settings"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=lessons, callback_data="menu:lessons"))
    builder.row(InlineKeyboardButton(text=progress, callback_data="menu:progress"))
    builder.row(InlineKeyboardButton(text=settings, callback_data="menu:settings"))
    return builder.as_markup()


def lesson_actions_keyboard(language: str, lesson_id: int) -> InlineKeyboardMarkup:
    completed = "Bu darsni tugatdim ✅" if language == "uz" else "I Completed This Lesson ✅"
    back = "Orqaga 🔙" if language == "uz" else "Back 🔙"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=completed, callback_data=f"lesson:completed:{lesson_id}")],
            [InlineKeyboardButton(text=back, callback_data="menu:main")],
        ]
    )


def settings_keyboard(language: str) -> InlineKeyboardMarkup:
    if language == "uz":
        lang, level, subject, back = "Til", "Daraja", "Fan", "Orqaga"
    else:
        lang, level, subject, back = "Language", "Level", "Subject", "Back"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=lang, callback_data="settings:language")],
            [InlineKeyboardButton(text=level, callback_data="settings:level")],
            [InlineKeyboardButton(text=subject, callback_data="settings:subject")],
            [InlineKeyboardButton(text=back, callback_data="menu:main")],
        ]
    )


def quiz_options_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A", callback_data=f"quiz:answer:{question_id}:a"),
                InlineKeyboardButton(text="B", callback_data=f"quiz:answer:{question_id}:b"),
            ],
            [
                InlineKeyboardButton(text="C", callback_data=f"quiz:answer:{question_id}:c"),
                InlineKeyboardButton(text="D", callback_data=f"quiz:answer:{question_id}:d"),
            ],
        ]
    )


def retake_quiz_keyboard(lesson_id: int, language: str) -> InlineKeyboardMarkup:
    text = "Testni qayta topshirish" if language == "uz" else "Retake Quiz"
    back = "Asosiy menyu" if language == "uz" else "Main Menu"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=f"lesson:completed:{lesson_id}")],
            [InlineKeyboardButton(text=back, callback_data="menu:main")],
        ]
    )
