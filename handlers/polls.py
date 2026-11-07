from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import get_active_polls, get_poll, vote_poll, get_poll_results
from keyboards import main_menu_kb

router = Router()


@router.message(F.text == "📊 Опросы")
async def show_polls(message: Message):
    polls_data = await get_active_polls()

    if not polls_data:
        await message.answer(
            "📊 Активные опросы:\n\n"
            "Пока нет активных опросов.\n\n"
            "Организаторы могут создать опрос через кнопку 'Я организатор' → 'Создать опрос'",
            reply_markup=main_menu_kb()
        )
        return

    # Показываем список опросов
    text = "📊 <b>Активные опросы:</b>\n\n"
    kb = InlineKeyboardBuilder()

    for item in polls_data:
        poll = item['poll']
        options_count = len(item['options'])
        text += f"🔹 <b>{poll['question']}</b> ({options_count} вариантов)\n"
        kb.button(text=f"📝 Голосовать: {poll['question'][:30]}", callback_data=f"poll:{poll['id']}")

    kb.button(text="🔙 В главное меню", callback_data="back_to_menu_from_polls")
    kb.adjust(1)

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("poll:"))
async def show_poll_vote(callback: CallbackQuery):
    poll_id = int(callback.data.split(":")[1])
    poll_data = await get_poll(poll_id)

    if not poll_data:
        await callback.answer("Опрос не найден", show_alert=True)
        return

    poll = poll_data['poll']
    options = poll_data['options']

    text = f"📊 <b>{poll['question']}</b>\n\nВыберите вариант:"

    kb = InlineKeyboardBuilder()
    for option in options:
        kb.button(text=option['option_text'], callback_data=f"vote:{poll_id}:{option['id']}")

    kb.button(text="📈 Результаты", callback_data=f"results:{poll_id}")
    kb.button(text="🔙 К списку опросов", callback_data="back_to_polls_list")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("vote:"))
async def handle_vote(callback: CallbackQuery):
    parts = callback.data.split(":")
    poll_id = int(parts[1])
    option_id = int(parts[2])

    success = await vote_poll(poll_id, option_id, callback.from_user.id)

    if success:
        await callback.answer("✅ Ваш голос принят!", show_alert=True)
    else:
        await callback.answer("⚠️ Вы уже голосовали в этом опросе", show_alert=True)

    # Показываем результаты
    poll_data = await get_poll(poll_id)
    poll = poll_data['poll']
    results = await get_poll_results(poll_id)

    text = f"📊 <b>{poll['question']}</b>\n\n📈 Результаты:\n\n"
    total_votes = sum(r['votes'] for r in results)

    for r in results:
        percentage = (r['votes'] / total_votes * 100) if total_votes > 0 else 0
        text += f"• {r['option_text']}: {r['votes']} голосов ({percentage:.1f}%)\n"

    text += f"\nВсего голосов: {total_votes}"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Проголосовать еще раз", callback_data=f"poll:{poll_id}")
    kb.button(text="🔙 К списку опросов", callback_data="back_to_polls_list")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("results:"))
async def show_results(callback: CallbackQuery):
    poll_id = int(callback.data.split(":")[1])
    poll_data = await get_poll(poll_id)
    poll = poll_data['poll']
    results = await get_poll_results(poll_id)

    text = f"📊 <b>{poll['question']}</b>\n\n📈 Результаты:\n\n"
    total_votes = sum(r['votes'] for r in results)

    for r in results:
        percentage = (r['votes'] / total_votes * 100) if total_votes > 0 else 0
        bar = "█" * int(percentage / 5)
        text += f"• {r['option_text']}: {r['votes']} ({percentage:.1f}%) {bar}\n"

    text += f"\nВсего голосов: {total_votes}"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Проголосовать", callback_data=f"poll:{poll_id}")
    kb.button(text="🔙 К списку опросов", callback_data="back_to_polls_list")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_polls_list")
async def back_to_polls_list(callback: CallbackQuery):
    polls_data = await get_active_polls()

    if not polls_data:
        await callback.message.edit_text(
            "📊 Активные опросы:\n\nПока нет активных опросов.",
            reply_markup=main_menu_kb()
        )
        return

    text = "📊 <b>Активные опросы:</b>\n\n"
    kb = InlineKeyboardBuilder()

    for item in polls_data:
        poll = item['poll']
        options_count = len(item['options'])
        text += f"🔹 <b>{poll['question']}</b> ({options_count} вариантов)\n"
        kb.button(text=f"📝 Голосовать: {poll['question'][:30]}", callback_data=f"poll:{poll['id']}")

    kb.button(text="🔙 В главное меню", callback_data="back_to_menu_from_polls")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_to_menu_from_polls")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите раздел:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()