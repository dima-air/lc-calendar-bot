from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import date
import calendar

from database import get_events_by_month  # Импорт функции из БД


async def calendar_kb(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    if year is None or month is None:
        today = date.today()
        year, month = today.year, today.month

    kb = InlineKeyboardBuilder()

    # Заголовок с месяцем и годом
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    month_name = month_names[month - 1]
    kb.button(text=f"📅 {month_name} {year}", callback_data="ignore")

    # Дни недели
    days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for day in days_of_week:
        kb.button(text=day, callback_data="ignore")

    # Получаем даты с мероприятиями из БД (асинхронно!)
    event_dates = await get_events_by_month(year, month)

    # Дни месяца
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        for day in week:
            if day == 0:
                kb.button(text=" ", callback_data="ignore")
            else:
                date_key = f"{year}-{month:02d}-{day:02d}"
                # Если есть мероприятия, добавляем точку
                if date_key in event_dates:
                    kb.button(text=f"🔴{day}", callback_data=f"day:{date_key}")
                else:
                    kb.button(text=str(day), callback_data=f"day:{date_key}")

    # Навигация по месяцам
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    kb.button(text="⬅️", callback_data=f"month:{prev_year}-{prev_month:02d}")
    kb.button(text="Сегодня", callback_data=f"month:{date.today().year}-{date.today().month:02d}")
    kb.button(text="➡️", callback_data=f"month:{next_year}-{next_month:02d}")

    kb.adjust(7)
    return kb.as_markup()


def day_calendar_kb(date_str: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Назад к календарю", callback_data="back_to_calendar")
    return kb.as_markup()