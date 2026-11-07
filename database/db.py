import sqlite3
import asyncio
from contextlib import asynccontextmanager
from config import DB_PATH, ADMIN_IDS


@asynccontextmanager
async def get_connection():
    conn = await asyncio.to_thread(lambda: sqlite3.connect(DB_PATH, check_same_thread=False))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        await asyncio.to_thread(conn.commit)
    except Exception:
        await asyncio.to_thread(conn.rollback)
        raise
    finally:
        await asyncio.to_thread(conn.close)


async def init_db():
    async with get_connection() as conn:
        await asyncio.to_thread(conn.executescript, """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            role TEXT DEFAULT 'user' CHECK(role IN ('user', 'organizer', 'vp', 'teamlead'))
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT NOT NULL,
            event_time TEXT,
            location TEXT,
            organizer_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rsvps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            tg_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('going', 'not_going')),
            UNIQUE(event_id, tg_id)
        );

        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS poll_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
            option_text TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS poll_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL REFERENCES polls(id) ON DELETE CASCADE,
            option_id INTEGER NOT NULL REFERENCES poll_options(id) ON DELETE CASCADE,
            tg_id INTEGER NOT NULL,
            UNIQUE(poll_id, tg_id)
        );
        """)


async def get_user(tg_id: int):
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
            "SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        result = await asyncio.to_thread(cursor.fetchone)
        return result


async def add_user(tg_id: int, username: str):
    # Если твой ID есть в .env, сразу даем роль 'vp' (вице-президент), иначе 'user'
    role = 'vp' if tg_id in ADMIN_IDS else 'user'

    async with get_connection() as conn:
        # 1. Пытаемся добавить пользователя с нужной ролью
        await asyncio.to_thread(conn.execute,
                                "INSERT OR IGNORE INTO users (tg_id, username, role) VALUES (?, ?, ?)",
                                (tg_id, username, role))

        # 2. Если ты админ, принудительно обновляем роль
        # (это исправит ситуацию, если ты уже нажимал /start ранее и записался как 'user')
        if tg_id in ADMIN_IDS:
            await asyncio.to_thread(conn.execute,
                                    "UPDATE users SET role = 'vp' WHERE tg_id = ?", (tg_id,))


async def get_user_role(tg_id: int) -> str:
    user = await get_user(tg_id)
    return user['role'] if user else 'user'


async def set_user_role(tg_id: int, role: str):
    async with get_connection() as conn:
        await asyncio.to_thread(conn.execute,
                                "UPDATE users SET role = ? WHERE tg_id = ?", (role, tg_id))

async def add_event(
    title: str,
    description: str,
    event_date: str,
    event_time: str,
    location: str,
    organizer_id: int
):
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
            """INSERT INTO events (title, description, event_date, event_time, location, organizer_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, event_date, event_time, location, organizer_id))
        await asyncio.to_thread(conn.commit)
        return cursor.lastrowid


async def get_events_by_date(date_str: str):
    """date_str в формате YYYY-MM-DD, конвертируем в ДД.ММ.ГГГГ для поиска"""
    # Конвертируем YYYY-MM-DD в ДД.ММ.ГГГГ
    parts = date_str.split('-')
    if len(parts) == 3:
        db_date_format = f"{parts[2]}.{parts[1]}.{parts[0]}"
    else:
        db_date_format = date_str

    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
                                         "SELECT * FROM events WHERE event_date = ? ORDER BY event_time",
                                         (db_date_format,))
        return await asyncio.to_thread(cursor.fetchall)
async def get_events_by_month(year: int, month: int):
    """Возвращает список дат с мероприятиями в формате YYYY-MM-DD"""
    async with get_connection() as conn:
        # Формат даты в БД: ДД.ММ.ГГГГ, поэтому ищем по подстроке
        month_str = f".{month:02d}.{year}"
        cursor = await asyncio.to_thread(conn.execute,
            "SELECT DISTINCT event_date FROM events WHERE event_date LIKE ?",
            (f"%{month_str}",))
        rows = await asyncio.to_thread(cursor.fetchall)
        # Преобразуем ДД.ММ.ГГГГ в YYYY-MM-DD
        dates = []
        for row in rows:
            parts = row['event_date'].split('.')
            if len(parts) == 3:
                dates.append(f"{parts[2]}-{parts[1]}-{parts[0]}")
        return dates


async def add_poll(question: str, created_by: int, options: list[str]) -> int:
    """Создает опрос с вариантами ответов, возвращает id опроса"""
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
                                         "INSERT INTO polls (question, created_by) VALUES (?, ?)",
                                         (question, created_by))
        poll_id = cursor.lastrowid

        # Добавляем варианты ответов
        for option_text in options:
            await asyncio.to_thread(conn.execute,
                                    "INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)",
                                    (poll_id, option_text))

        await asyncio.to_thread(conn.commit)
        return poll_id


async def get_active_polls() -> list:
    """Возвращает все активные опросы с вариантами"""
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
                                         "SELECT * FROM polls WHERE is_active = 1 ORDER BY created_at DESC")
        polls = await asyncio.to_thread(cursor.fetchall)

        result = []
        for poll in polls:
            # Получаем варианты для каждого опроса
            cursor2 = await asyncio.to_thread(conn.execute,
                                              "SELECT * FROM poll_options WHERE poll_id = ?", (poll['id'],))
            options = await asyncio.to_thread(cursor2.fetchall)
            result.append({
                'poll': poll,
                'options': options
            })
        return result


async def get_poll(poll_id: int):
    """Возвращает опрос с вариантами"""
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
                                         "SELECT * FROM polls WHERE id = ?", (poll_id,))
        poll = await asyncio.to_thread(cursor.fetchone)

        if not poll:
            return None

        cursor2 = await asyncio.to_thread(conn.execute,
                                          "SELECT * FROM poll_options WHERE poll_id = ?", (poll_id,))
        options = await asyncio.to_thread(cursor2.fetchall)

        return {'poll': poll, 'options': options}


async def vote_poll(poll_id: int, option_id: int, tg_id: int) -> bool:
    """Голосует за вариант. Возвращает True если успешно."""
    async with get_connection() as conn:
        try:
            await asyncio.to_thread(conn.execute,
                                    "INSERT INTO poll_votes (poll_id, option_id, tg_id) VALUES (?, ?, ?)",
                                    (poll_id, option_id, tg_id))
            await asyncio.to_thread(conn.commit)
            return True
        except sqlite3.IntegrityError:
            # Пользователь уже голосовал
            return False


async def get_poll_results(poll_id: int) -> dict:
    """Возвращает результаты голосования"""
    async with get_connection() as conn:
        cursor = await asyncio.to_thread(conn.execute,
                                         """SELECT po.id, po.option_text, COUNT(pv.id) as votes
                                            FROM poll_options po
                                            LEFT JOIN poll_votes pv ON po.id = pv.option_id
                                            WHERE po.poll_id = ?
                                            GROUP BY po.id""", (poll_id,))
        return await asyncio.to_thread(cursor.fetchall)

