from aiogram import Router
from . import start, calendar, polls, organizer

def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(calendar.router)
    root.include_router(polls.router)
    root.include_router(organizer.router)
    return root