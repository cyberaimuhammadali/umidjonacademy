from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Add Lesson", callback_data="admin:add_lesson")],
            [InlineKeyboardButton(text="View Stats", callback_data="admin:view_stats")],
            [InlineKeyboardButton(text="Broadcast Message", callback_data="admin:broadcast")],
            [InlineKeyboardButton(text="Add Quiz JSON", callback_data="admin:add_quiz")],
        ]
    )


def yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Yes", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="No", callback_data=f"{prefix}:no"),
            ]
        ]
    )
