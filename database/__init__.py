from .db import (
    init_db, get_user, add_user, get_user_role, set_user_role,
    add_event, get_events_by_date, get_events_by_month,
    add_poll, get_active_polls, get_poll, vote_poll, get_poll_results
)