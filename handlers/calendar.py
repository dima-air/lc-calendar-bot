from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from keyboards.calendar_kb import calendar_kb, day_calendar_kb
from database import get_events_by_date

router = Router()


@router.message(F.text == "📅 Календарь")
async def show_calendar(message: Message):
    await message.answer(
        "📅 Выберите дату:",
        reply_markup=await calendar_kb()  # <-- Добавили await
    )


@router.callback_query(F.data.startswith("month:"))
async def change_month(callback: CallbackQuery):
    year_month = callback.data.split(":")[1]
    year, month = map(int, year_month.split("-"))

    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=await calendar_kb(year, month)  # <-- Добавили await
    )
    await callback.answer()


@router.callback_query(F.data.startswith("day:"))
async def show_day_events(callback: CallbackQuery):
    date_str = callback.data.split(":")[1]

    # Получаем мероприятия из БД
    events = await get_events_by_date(date_str)

    if not events:
        await callback.message.edit_text(
            f"📅 Мероприятия на {date_str}\n\n"
            "Пока нет запланированных событий.\n\n"
            "Организаторы могут добавить мероприятие через кнопку 'Я организатор'",
            reply_markup=day_calendar_kb(date_str)
        )
    else:
        text = f"📅 Мероприятия на {date_str}:\n\n"
        for event in events:
            text += f"🎯 <b>{event['title']}</b>\n"
            text += f"🕒 {event['event_time']}\n"
            text += f"📍 {event['location']}\n"
            if event['description']:
                text += f"📝 {event['description']}\n"
            text += "\n"

        await callback.message.edit_text(
            text,
            reply_markup=day_calendar_kb(date_str),
            parse_mode="HTML"
        )

    await callback.answer()


@router.callback_query(F.data == "back_to_calendar")
async def back_to_calendar(callback: CallbackQuery):
    await callback.message.edit_text(
        "📅 Выберите дату:",
        reply_markup=await calendar_kb()  # <-- Добавили await
    )
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()