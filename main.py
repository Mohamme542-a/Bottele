# ===================================================================
# 💀 CYBER AI ENGINE - NO AUTH EDITION 💀
# ===================================================================
# تحذير: لوحة التحكم مفتوحة للجميع. لا تستخدمها في بيئة حساسة.
# ===================================================================

import asyncio
import random
import time
import os
import json
import secrets as _secrets
from datetime import datetime
from collections import defaultdict, deque

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetCommonChatsRequest
from telethon.tl.functions.contacts import (
    ImportContactsRequest,
    DeleteContactsRequest,
    GetContactsRequest,
)
from telethon.tl.types import InputPhoneContact, InputUser
from aiohttp import web

# ===================================================================
# ✅ بياناتك الأساسية
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="
OWNER_ID = 8676210788

# ===================================================================
# ⚙️ الإعدادات الافتراضية (قابلة للتعديل من اللوحة)
# ===================================================================

DEFAULT_SETTINGS = {
    "max_messages": 8,
    "warning_limit": 4,
    "cooldown_seconds": 60,
    "reply_delay": 0.5,
    "talking_timeout": 3600,
    "auto_reply": True,
    "send_info_card": True,
    "auto_block": True,
    "silent_mode": False,
    "special_username": "Yaharp",
    "special_reply": "🌹 مرحباً حجي فرات العراقي 🌹\n📨 تم استلام رسالتك\n⏳ سيتم الرد قريباً",
    "replies": [
        "مرحباً! شكراً لتواصلك 🌸",
        "أهلاً بك، رسالتك وصلت ✅",
        "شكراً لك، سأرد عليك قريباً 💫",
        "تم استلام رسالتك، شكراً جزيلاً 🌹",
        "أهلاً وسهلاً، رسالتك بأمان 💙",
    ],
}

# ===================================================================
# 📦 إدارة البيانات
# ===================================================================

class DataManager:
    def __init__(self):
        self.users = {}
        self.blocked_users = set()
        self.settings = dict(DEFAULT_SETTINGS)
        self.events_log = deque(maxlen=500)
        self.start_time = time.time()
        self.load()

    def load(self):
        try:
            if os.path.exists("users_data.json"):
                with open("users_data.json", "r", encoding="utf-8") as f:
                    self.users = json.load(f).get("users", {})
            if os.path.exists("blocked_users.json"):
                with open("blocked_users.json", "r") as f:
                    self.blocked_users = set(json.load(f))
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.settings = {**DEFAULT_SETTINGS, **saved}
        except Exception as e:
            print(f"[DataManager.load] {e}")

    def save(self):
        try:
            with open("users_data.json", "w", encoding="utf-8") as f:
                json.dump({"users": self.users}, f, ensure_ascii=False, indent=2)
            with open("blocked_users.json", "w") as f:
                json.dump(list(self.blocked_users), f)
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DataManager.save] {e}")

    def log(self, event_type, msg, user_id=None):
        self.events_log.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "msg": msg,
            "user_id": user_id,
        })
        print(f"[{event_type}] {msg}")


data = DataManager()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

user_timestamps = defaultdict(list)
talking_mode = {}
info_cache = {}
phone_cache = {}
INFO_CACHE_TTL = 300

# ===================================================================
# 🔍 جلب رقم الهاتف (مع كاش)
# ===================================================================

async def try_extract_phone(user_obj):
    uid = user_obj.id
    if uid in phone_cache:
        return phone_cache[uid]

    if getattr(user_obj, "phone", None):
        phone_cache[uid] = "+" + user_obj.phone
        return phone_cache[uid]

    phone = "غير مرئي (الخصوصية)"
    try:
        fake_phone = "+1555" + str(int(time.time() * 1000))[-7:]
        contact = InputPhoneContact(
            client_id=0,
            phone=fake_phone,
            first_name=(user_obj.first_name or "T")[:30],
            last_name=str(uid),
        )
        res = await client(ImportContactsRequest([contact]))
        for u in res.users:
            if u.id == uid and getattr(u, "phone", None):
                phone = "+" + u.phone
                break
        try:
            await client(DeleteContactsRequest(id=[uid]))
        except Exception:
            pass
    except FloodWaitError as e:
        phone = f"FloodWait {e.seconds}s"
    except Exception:
        pass

    phone_cache[uid] = phone
    return phone

# ===================================================================
# 🔍 بطاقة المعلومات الكاملة
# ===================================================================

async def build_info_card(user_id):
    cached = info_cache.get(user_id)
    if cached and time.time() - cached[0] < INFO_CACHE_TTL:
        return cached[1]

    try:
        entity = await client.get_entity(user_id)
        full = await client(GetFullUserRequest(entity))
        user = next((u for u in full.users if u.id == user_id), entity)
        full_user = full.full_user

        phone = await try_extract_phone(user)

        first = user.first_name or "غير معروف"
        last = user.last_name or ""
        username = f"@{user.username}" if user.username else "لا يوجد"
        link = f"t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

        premium = "✅" if getattr(user, "premium", False) else "❌"
        is_bot = "✅" if user.bot else "❌"
        verified = "✅" if getattr(user, "verified", False) else "❌"
        scam = "⚠️" if getattr(user, "scam", False) else "❌"
        fake = "⚠️" if getattr(user, "fake", False) else "❌"
        contact = "✅" if getattr(user, "contact", False) else "❌"
        mutual = "✅" if getattr(user, "mutual_contact", False) else "❌"
        deleted = "⚠️" if getattr(user, "deleted", False) else "❌"
        restricted = "⚠️" if getattr(user, "restricted", False) else "❌"

        old_names = []
        for un in (getattr(user, "usernames", None) or []):
            uname = getattr(un, "username", None)
            if uname and uname != user.username:
                old_names.append(f"@{uname}")
        old_names_text = "\n".join(f"  • {n}" for n in old_names[:5]) or "  • لا يوجد"

        photos_count = 0
        try:
            photos = await client.get_profile_photos(user, limit=1)
            photos_count = getattr(photos, "total", len(photos))
        except Exception:
            pass

        groups = []
        try:
            input_user = InputUser(user_id=user.id, access_hash=user.access_hash or 0)
            common = await client(GetCommonChatsRequest(user_id=input_user, max_id=0, limit=20))
            for c in common.chats:
                title = getattr(c, "title", None) or "?"
                groups.append(title[:40])
        except Exception:
            pass
        groups_text = "\n".join(f"  • {g}" for g in groups) or "  • لا توجد"

        about = (getattr(full_user, "about", None) or "لا يوجد")[:250]

        status = getattr(user, "status", None)
        status_text = type(status).__name__.replace("UserStatus", "") if status else "غير معروف"

        dc_id = getattr(user, "dc_id", "?") or "?"
        lang = getattr(user, "lang_code", "ar") or "ar"

        card = f"""
╔══════════════════════════════╗
📋 【 بطاقة المعلومات الكاملة 】
╚══════════════════════════════╝

👤 الاسم: {first} {last}
🆔 اليوزر: {username}
🔢 الـ ID: `{user.id}`
🔗 الرابط: {link}
🌐 اللغة: {lang}  |  📡 DC: {dc_id}
🕐 الحالة: {status_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📞 الهاتف: {phone}
🖼️ عدد الصور: {photos_count}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
💎 بريميوم: {premium}   🤖 بوت: {is_bot}
✅ موثق: {verified}     🚨 مشبوه: {scam}
🎭 مزيف: {fake}         🗑️ محذوف: {deleted}
📞 جهة اتصال: {contact}  🔄 متبادل: {mutual}
🚷 مقيد: {restricted}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📜 الأسماء البديلة:
{old_names_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📢 المجموعات المشتركة:
{groups_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📝 البايو:
{about}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        info_cache[user_id] = (time.time(), card)
        return card

    except FloodWaitError as e:
        data.log("ERROR", f"FloodWait {e.seconds}s on get info {user_id}")
        return None
    except Exception as e:
        data.log("ERROR", f"build_info_card({user_id}): {e}")
        return None

# ===================================================================
# 🛡️ فحص السبام
# ===================================================================

async def check_spam(user_id):
    now = time.time()
    cd = data.settings["cooldown_seconds"]
    user_timestamps[user_id] = [t for t in user_timestamps[user_id] if now - t < cd]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    try:
        sender = await event.get_sender()
    except Exception:
        return
    if sender is None or sender.bot:
        return

    user_id = sender.id
    if user_id == OWNER_ID:
        return

    name = sender.first_name or sender.username or "مجهول"
    username = sender.username or ""
    text = event.raw_text or ""
    s = data.settings

    if user_id in talking_mode and time.time() - talking_mode[user_id] < s["talking_timeout"]:
        return

    if user_id in data.blocked_users:
        if not s["silent_mode"]:
            try: await event.reply("🚫 أنت محظور من هذا الحساب.")
            except: pass
        return

    count = await check_spam(user_id)
    if count == s["warning_limit"]:
        try: await event.reply("⚠️ تنبيه: إرسال سريع، رجاءً تمهل.")
        except: pass
        data.log("WARN", f"تحذير سبام: {name}", user_id)
        return
    if count >= s["max_messages"]:
        if s["auto_block"]:
            data.blocked_users.add(user_id)
            data.save()
            try: await event.reply(f"🚫 تم حظرك ({s['max_messages']} رسائل خلال {s['cooldown_seconds']}ث)")
            except: pass
            data.log("BLOCK", f"حظر تلقائي: {name}", user_id)
        return

    if s["send_info_card"]:
        card = await build_info_card(user_id)
        if card:
            try: await event.reply(card)
            except Exception as e: data.log("ERROR", f"reply card: {e}")
            await asyncio.sleep(0.3)

    if s["auto_reply"] and not s["silent_mode"]:
        await asyncio.sleep(s["reply_delay"])
        if username == s["special_username"] or name == s["special_username"]:
            reply_text = s["special_reply"]
        else:
            reply_text = random.choice(s["replies"]) if s["replies"] else "👋"
        try: await event.reply(reply_text)
        except Exception as e: data.log("ERROR", f"reply: {e}")

    uid = str(user_id)
    u = data.users.setdefault(uid, {"messages": 0, "name": name, "username": username})
    u["messages"] += 1
    u["name"] = name
    u["username"] = username
    u["last_seen"] = datetime.now().isoformat()
    u["last_text"] = text[:80]
    data.save()
    data.log("MSG", f"{name} (@{username}): {text[:60]}", user_id)


@client.on(events.NewMessage(outgoing=True))
async def track_owner(event):
    if event.is_private:
        talking_mode[event.chat_id] = time.time()


async def clean_talking_loop():
    while True:
        await asyncio.sleep(300)
        now = time.time()
        expired = [u for u, t in talking_mode.items() if now - t > data.settings["talking_timeout"]]
        for u in expired:
            talking_mode.pop(u, None)

# ===================================================================
# 🌐 API (بدون مصادقة)
# ===================================================================

async def api_stats(request):
    today = datetime.now().strftime("%Y-%m-%d")
    today_msgs = sum(1 for ev in data.events_log if ev["type"] == "MSG" and ev["time"].startswith(today))
    return web.json_response({
        "users": len(data.users),
        "blocked": len(data.blocked_users),
        "total_messages": sum(u.get("messages", 0) for u in data.users.values()),
        "today_messages": today_msgs,
        "uptime_seconds": int(time.time() - data.start_time),
        "talking_mode_count": len(talking_mode),
        "online": True,
    })

async def api_users(request):
    rows = []
    for uid, u in data.users.items():
        rows.append({
            "id": uid,
            "name": u.get("name", "مجهول"),
            "username": u.get("username", ""),
            "messages": u.get("messages", 0),
            "last_seen": u.get("last_seen", ""),
            "last_text": u.get("last_text", ""),
            "blocked": int(uid) in data.blocked_users,
            "talking": int(uid) in talking_mode,
        })
    rows.sort(key=lambda x: x["last_seen"], reverse=True)
    return web.json_response({"users": rows})

async def api_blocked(request):
    return web.json_response({"blocked": list(data.blocked_users)})

async def api_logs(request):
    return web.json_response({"logs": list(data.events_log)[-100:][::-1]})

async def api_settings_get(request):
    return web.json_response({"settings": data.settings})

async def api_settings_set(request):
    body = await request.json()
    for k, v in body.items():
        if k in DEFAULT_SETTINGS:
            data.settings[k] = v
    data.save()
    data.log("CFG", f"تحديث الإعدادات: {list(body.keys())}")
    return web.json_response({"ok": True, "settings": data.settings})

async def api_block(request):
    body = await request.json()
    uid = int(body["user_id"])
    data.blocked_users.add(uid)
    data.save()
    data.log("BLOCK", f"حظر يدوي: {uid}", uid)
    return web.json_response({"ok": True})

async def api_unblock(request):
    body = await request.json()
    uid = int(body["user_id"])
    data.blocked_users.discard(uid)
    data.save()
    data.log("UNBLOCK", f"فك حظر: {uid}", uid)
    return web.json_response({"ok": True})

async def api_unblock_all(request):
    n = len(data.blocked_users)
    data.blocked_users.clear()
    data.save()
    data.log("UNBLOCK", f"فك حظر جماعي: {n}")
    return web.json_response({"ok": True, "count": n})

async def api_send(request):
    body = await request.json()
    uid = int(body["user_id"])
    text = body["text"]
    try:
        await client.send_message(uid, text)
        data.log("SEND", f"إرسال إلى {uid}: {text[:50]}", uid)
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def api_clear_user(request):
    body = await request.json()
    uid = str(int(body["user_id"]))
    data.users.pop(uid, None)
    data.save()
    return web.json_response({"ok": True})

async def api_clear_all(request):
    data.users.clear()
    data.save()
    return web.json_response({"ok": True})

async def api_info_card(request):
    uid = int(request.query["user_id"])
    card = await build_info_card(uid)
    return web.json_response({"card": card or "تعذّر الجلب"})

async def api_export(request):
    payload = {
        "users": data.users,
        "blocked": list(data.blocked_users),
        "settings": data.settings,
    }
    return web.Response(
        text=json.dumps(payload, ensure_ascii=False, indent=2),
        content_type="application/json",
        headers={"Content-Disposition": "attachment; filename=cyber_export.json"},
    )

# ===================================================================
# 🌐 صفحات HTML و الويب
# ===================================================================

# (نفس HTML كما في ملفك الأصلي – لوحة التحكم و شاشة الدخول اختيارية، لكن سنعيد توجيه /login إلى dashboard)
LOGIN_HTML = """<!doctype html>..."""   # اختصاراً، استخدم نفس الـ HTML الذي لديك، أو يمكنك توجيه /login إلى dashboard

# لعدم إطالة الرد، سأفترض أنك تحتفظ بنفس محتوى DASHBOARD_HTML و LOGIN_HTML السابقة، ولكننا نعدل المسارات فقط.

async def page_login(request):
    # إعادة توجيه مباشرة إلى dashboard (بدون كلمة سر)
    raise web.HTTPFound("/dashboard")

async def page_dashboard(request):
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")

async def page_root(request):
    raise web.HTTPFound("/dashboard")

async def page_health(request):
    return web.Response(text=f"OK | users={len(data.users)} | blocked={len(data.blocked_users)}")

# ===================================================================
# 🌐 تشغيل خادم الويب
# ===================================================================

async def start_web():
    app = web.Application()
    app.router.add_get("/", page_root)
    app.router.add_get("/login", page_login)
    app.router.add_get("/dashboard", page_dashboard)
    app.router.add_get("/health", page_health)
    # API
    app.router.add_get("/api/stats", api_stats)
    app.router.add_get("/api/users", api_users)
    app.router.add_get("/api/blocked", api_blocked)
    app.router.add_get("/api/logs", api_logs)
    app.router.add_get("/api/settings", api_settings_get)
    app.router.add_post("/api/settings", api_settings_set)
    app.router.add_post("/api/block", api_block)
    app.router.add_post("/api/unblock", api_unblock)
    app.router.add_post("/api/unblock_all", api_unblock_all)
    app.router.add_post("/api/send", api_send)
    app.router.add_post("/api/clear_user", api_clear_user)
    app.router.add_post("/api/clear_all", api_clear_all)
    app.router.add_get("/api/info_card", api_info_card)
    app.router.add_get("/api/export", api_export)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 لوحة التحكم (بدون كلمة سر): http://0.0.0.0:{port}")
    print(f"🔓 تحذير: جميع الصفحات و API مفتوحة للعموم")

# ===================================================================
# 🚀 التشغيل
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 CYBER AI ENGINE - NO AUTH EDITION 💀")
    print("⚠️  تم تعطيل المصادقة. كل من لديه الرابط يستطيع التحكم.")
    print("=" * 60)
    await client.start()
    me = await client.get_me()
    asyncio.create_task(start_web())
    asyncio.create_task(clean_talking_loop())
    print(f"✅ الحساب: {me.first_name} ({me.id})")
    print(f"🛡️ الحماية: {data.settings['max_messages']} رسائل = حظر")
    print(f"📊 المستخدمين المخزّنين: {len(data.users)}")
    print(f"🚫 المحظورين: {len(data.blocked_users)}")
    print("=" * 60)
    data.log("BOOT", "تم تشغيل البوت (بدون كلمة سر)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
