"""منع تكرار الرد على نفس الشخص خلال فترة قصيرة."""
import time

_last_reply = {}  # user_id -> timestamp


def can_reply(user_id, cooldown_seconds):
    now = time.time()
    last = _last_reply.get(user_id, 0)
    if now - last < cooldown_seconds:
        return False
    _last_reply[user_id] = now
    return True
