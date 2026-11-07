from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Календарь")],
            [KeyboardButton(text="📊 Опросы")],
            [KeyboardButton(text="👤 Я организатор")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )