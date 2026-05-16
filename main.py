"""TgAuto Userbot Worker — الرد التلقائي على رسائل Telegram الواردة لحسابك الشخصي."""
import os
import asyncio
import time
from dotenv import load_dotenv
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from config_client import get_config, log_reply, heartbeat
from reply_engine import pick_reply
from anti_spam import can_reply
from scheduler import is_active_now

load_dotenv()

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION = os.getenv("TG_SESSION") or open("session.txt").read().strip()

START_TIME = time.time()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        # only private chats (not groups/channels)
        if not event.is_private:
            return

        cfg = get_config()
        bot_cfg = cfg.get("config") or {}

        if not bot_cfg.get("enabled"):
            return

        sender = await event.get_sender()
        if not sender:
            return

        # ignore bots
        if bot_cfg.get("ignore_bots", True) and getattr(sender, "bot", False):
            return

        # ignore old messages
        if bot_cfg.get("ignore_old_messages", True):
            msg_time = event.message.date.timestamp()
            if msg_time < START_TIME:
                return

        sender_id = sender.id

        # blacklist
        if sender_id in cfg.get("blacklist", []):
            return

        # excluded
        if sender_id in cfg.get("excluded", []):
            return

        # whitelist-only mode
        if bot_cfg.get("whitelist_only_mode"):
            allowed_ids = {c["telegram_user_id"] for c in cfg.get("contacts", [])}
            if sender_id not in allowed_ids:
                return

        # schedule
        if not is_active_now(cfg.get("schedule")):
            return

        # anti-spam
        cooldown = bot_cfg.get("anti_spam_cooldown_seconds", 300)
        if not can_reply(sender_id, cooldown):
            return

        text = event.message.message or ""
        reply_text, matched = pick_reply(cfg, sender_id, text)

        # delay
        delay = bot_cfg.get("reply_delay_seconds", 3)
        if delay > 0:
            await asyncio.sleep(delay)

        await event.reply(reply_text)

        log_reply({
            "telegram_user_id": sender_id,
            "username": getattr(sender, "username", None),
            "incoming_text": text[:500],
            "reply_text": reply_text[:500],
            "matched_rule": matched,
        })
        print(f"✅ Replied to {sender_id} ({matched})")
    except Exception as e:
        print(f"❌ Error: {e}")


async def heartbeat_loop():
    while True:
        try:
            heartbeat()
        except Exception as e:
            print(f"[hb] {e}")
        await asyncio.sleep(60)


async def status(_req):
    me = await client.get_me()
    html = f"""<!doctype html><html lang=ar dir=rtl><meta charset=utf-8>
<title>TgAuto Worker</title>
<style>body{{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:grid;place-items:center;height:100vh;margin:0}}
.card{{background:#1e293b;padding:2rem 3rem;border-radius:1rem;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,.4)}}
.dot{{display:inline-block;width:12px;height:12px;background:#10b981;border-radius:50%;margin-left:8px;animation:p 1.5s infinite}}
@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}h1{{margin:0 0 .5rem}}p{{color:#94a3b8;margin:.25rem 0}}</style>
<div class=card><h1><span class=dot></span>Worker يعمل</h1>
<p>الحساب: <b>{me.first_name}</b> (@{me.username or '-'})</p>
<p>الوقت: {int(time.time()-START_TIME)}s منذ التشغيل</p></div></html>"""
    return web.Response(text=html, content_type="text/html")


async def health(_req):
    return web.json_response({"ok": True, "uptime": int(time.time() - START_TIME)})


async def start_web():
    app = web.Application()
    app.router.add_get("/", status)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"🌐 Status page on :{port}")


async def main():
    await client.start()
    me = await client.get_me()
    print(f"🚀 TgAuto Worker started — logged in as {me.first_name} (@{me.username})")
    print(f"📡 API: {os.getenv('API_BASE_URL')}")
    asyncio.create_task(heartbeat_loop())
    await start_web()
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
