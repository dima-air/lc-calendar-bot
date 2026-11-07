from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import add_user, get_user
from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    await add_user(message.from_user.id, message.from_user.username or "")

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n\n"
        "Я бот-календарь локального комитета.\n"
        "Здесь ты можешь:\n"
        "• Смотреть расписание мероприятий\n"
        "• Участвовать в опросах\n"
        "• Регистрироваться на события\n\n"
        "Выбери раздел в меню",
        reply_markup=main_menu_kb()
    )