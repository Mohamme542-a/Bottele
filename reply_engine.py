"""منطق اختيار الرد المناسب."""
import random


def pick_reply(config_data, sender_id, text):
    text_lower = (text or "").lower().strip()

    # 1. contact override
    for c in config_data.get("contacts", []):
        if c["telegram_user_id"] == sender_id:
            return c["custom_reply"], "contact_override"

    # 2. keyword rules (sorted by priority desc)
    for k in config_data.get("keywords", []):
        kw = k["keyword"].lower()
        mt = k.get("match_type", "contains")
        match = (
            (mt == "contains" and kw in text_lower)
            or (mt == "equals" and kw == text_lower)
            or (mt == "starts_with" and text_lower.startswith(kw))
        )
        if match:
            return k["reply_text"], f"keyword:{k['keyword']}"

    # 3. random from auto_replies (weighted)
    replies = config_data.get("replies", [])
    if replies:
        weights = [max(1, r.get("weight", 1)) for r in replies]
        chosen = random.choices(replies, weights=weights, k=1)[0]
        return chosen["text"], "random"

    # 4. default
    cfg = config_data.get("config") or {}
    return cfg.get("default_reply_text") or "مرحباً! سأرد عليك قريباً.", "default"
