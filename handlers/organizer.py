from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import get_user_role
from keyboards import main_menu_kb
from database import add_event
from database import add_poll

router = Router()


class EventForm(StatesGroup):
    title = State()
    date = State()
    time = State()
    location = State()
    description = State()


@router.message(F.text == "👤 Я организатор")
async def organizer_menu(message: Message):
    role = await get_user_role(message.from_user.id)

    if role == 'user':
        await message.answer(
            "⛔️⛔️⛔️ Эта функция доступна только организаторам.\n\n"
            "Если вы вице-президент или тимлидер, обратитесь к администратору бота "
            "для назначения роли."
        )
        return

    await message.answer(
        "👤 Панель организатора\n\n"
        "Выберите действие:",
        reply_markup=organizer_menu_kb()
    )


def organizer_menu_kb():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить мероприятие")],
            [KeyboardButton(text="📊 Создать опрос")],
            [KeyboardButton(text="🔙 Назад в меню")],
        ],
        resize_keyboard=True
    )


@router.message(F.text == "➕ Добавить мероприятие")
async def add_event_start(message: Message, state: FSMContext):
    role = await get_user_role(message.from_user.id)
    if role == 'user':
        await message.answer("⛔️ У вас нет прав для создания мероприятий ⛔️")
        return

    await state.set_state(EventForm.title)
    await message.answer("Введите название мероприятия:")


@router.message(EventForm.title)
async def event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(EventForm.date)
    await message.answer(
        "Введите дату мероприятия в формате ДД.ММ.ГГГГ\n"
        "Например: 15.11.2024"
    )


@router.message(EventForm.date)
async def event_date(message: Message, state: FSMContext):
    # Здесь можно добавить валидацию даты
    await state.update_data(date=message.text)
    await state.set_state(EventForm.time)
    await message.answer(
        "Введите время мероприятия в формате ЧЧ:ММ\n"
        "Например: 18:30"
    )


@router.message(EventForm.time)
async def event_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(EventForm.location)
    await message.answer(
        "Введите место проведения (или напишите 'Онлайн'):"
    )


@router.message(EventForm.location)
async def event_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(EventForm.description)
    await message.answer(
        "Введите описание мероприятия (или напишите 'Пропустить'):"
    )


@router.message(EventForm.description)
async def event_description(message: Message, state: FSMContext):
    data = await state.get_data()

    # Сохраняем мероприятие в БД
    event_id = await add_event(
        title=data['title'],
        description=message.text if message.text != 'Пропустить' else '',
        event_date=data['date'],
        event_time=data['time'],
        location=data['location'],
        organizer_id=message.from_user.id
    )

    await message.answer(
        f"✅ Мероприятие создано!\n\n"
        f"Название: {data['title']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Место: {data['location']}\n"
        f"Описание: {message.text if message.text != 'Пропустить' else 'Нет описания'}",
        reply_markup=main_menu_kb()
    )
    await state.clear()


@router.message(F.text == "🔙 Назад в меню")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu_kb()
    )


@router.message(F.text == "📊 Создать опрос")
async def create_poll_start(message: Message, state: FSMContext):
    role = await get_user_role(message.from_user.id)
    if role == 'user':
        await message.answer("⛔️ У вас нет прав для создания опросов ⛔️")
        return

    await state.set_state(PollForm.question)
    await message.answer(
        "Введите вопрос для опроса:\n\n"
        "Например: Какое время встречи вам удобнее?"
    )


class PollForm(StatesGroup):
    question = State()
    options = State()


@router.message(PollForm.question)
async def poll_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(PollForm.options)
    await message.answer(
        "Введите варианты ответов через запятую:\n\n"
        "Например: 10:00, 14:00, 18:00, 20:00"
    )


@router.message(PollForm.options)
async def poll_options(message: Message, state: FSMContext):
    data = await state.get_data()
    options = [opt.strip() for opt in message.text.split(',')]

    if len(options) < 2:
        await message.answer("Нужно минимум 2 варианта ответа. Попробуй еще раз:")
        return

    # Сохраняем опрос в БД
    poll_id = await add_poll(
        question=data['question'],
        created_by=message.from_user.id,
        options=options
    )

    await message.answer(
        f"Опрос создан! (ID: {poll_id})\n\n"
        f"Вопрос: {data['question']}\n"
        f"Варианты: {', '.join(options)}\n\n"
        f"Теперь все участники могут проголосовать через меню 'Опросы'",
        reply_markup=main_menu_kb()
    )
    await state.clear()