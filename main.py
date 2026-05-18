# ===================================================================
# 💀 CYBER AI ENGINE - GIGA EDITION v2 💀
# ===================================================================
# - استخراج معلومات محسّن + كاش
# - لوحة تحكم ويب عملاقة (Dashboard) محمية بكلمة مرور
# - تحكم كامل: حظر / فك حظر / إعدادات / إرسال / سجل أحداث
# - API REST كامل
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

DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "cyber2026")

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
                    # دمج مع الافتراضي حتى لا تختفي مفاتيح جديدة
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
info_cache = {}  # user_id -> (timestamp, card_text)
phone_cache = {}  # user_id -> phone_str (لا نُكرر المحاولة)
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
        # حذف جهة الاتصال
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
    # كاش
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

        # الأسماء البديلة
        old_names = []
        for un in (getattr(user, "usernames", None) or []):
            uname = getattr(un, "username", None)
            if uname and uname != user.username:
                old_names.append(f"@{uname}")
        old_names_text = "\n".join(f"  • {n}" for n in old_names[:5]) or "  • لا يوجد"

        # عدد الصور (سريع)
        photos_count = 0
        try:
            photos = await client.get_profile_photos(user, limit=1)
            photos_count = getattr(photos, "total", len(photos))
        except Exception:
            pass

        # المجموعات المشتركة (الطريقة الصحيحة)
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

        # آخر ظهور
        status = getattr(user, "status", None)
        status_text = type(status).__name__.replace("UserStatus", "") if status else "غير معروف"

        # DC
        dc_id = getattr(user, "dc_id", "?") or "?"
        lang = getattr(user, "lang_code", "ar") or "ar"

        card = f"""
╔══════════════════════════════════╗
📋 【 بطاقة المعلومات الكاملة 】
╚══════════════════════════════════╝

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

    # وضع المحادثة (المالك يرد يدوياً)
    if user_id in talking_mode and time.time() - talking_mode[user_id] < s["talking_timeout"]:
        return

    # محظور
    if user_id in data.blocked_users:
        if not s["silent_mode"]:
            try: await event.reply("🚫 أنت محظور من هذا الحساب.")
            except: pass
        return

    # فحص السبام
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

    # بطاقة المعلومات
    if s["send_info_card"]:
        card = await build_info_card(user_id)
        if card:
            try: await event.reply(card)
            except Exception as e: data.log("ERROR", f"reply card: {e}")
            await asyncio.sleep(0.3)

    # الرد التلقائي
    if s["auto_reply"] and not s["silent_mode"]:
        await asyncio.sleep(s["reply_delay"])
        if username == s["special_username"] or name == s["special_username"]:
            reply_text = s["special_reply"]
        else:
            reply_text = random.choice(s["replies"]) if s["replies"] else "👋"
        try: await event.reply(reply_text)
        except Exception as e: data.log("ERROR", f"reply: {e}")

    # الإحصائيات
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
# 🌐 لوحة التحكم - Auth
# ===================================================================

active_tokens = set()

def make_token():
    t = _secrets.token_urlsafe(24)
    active_tokens.add(t)
    return t

def is_authed(request):
    tok = request.cookies.get("auth") or request.headers.get("X-Auth-Token") or request.query.get("token")
    return tok in active_tokens

def require_auth(handler):
    async def wrapper(request):
        if not is_authed(request):
            return web.json_response({"error": "unauthorized"}, status=401)
        return await handler(request)
    return wrapper

# ===================================================================
# 🌐 API
# ===================================================================

async def api_login(request):
    body = await request.json()
    if body.get("password") == DASHBOARD_PASSWORD:
        tok = make_token()
        resp = web.json_response({"ok": True, "token": tok})
        resp.set_cookie("auth", tok, max_age=86400, httponly=True, samesite="Lax")
        return resp
    return web.json_response({"ok": False, "error": "كلمة المرور خاطئة"}, status=401)

@require_auth
async def api_stats(request):
    today = datetime.now().strftime("%Y-%m-%d")
    today_msgs = sum(
        1 for ev in data.events_log if ev["type"] == "MSG" and ev["time"].startswith(today)
    )
    return web.json_response({
        "users": len(data.users),
        "blocked": len(data.blocked_users),
        "total_messages": sum(u.get("messages", 0) for u in data.users.values()),
        "today_messages": today_msgs,
        "uptime_seconds": int(time.time() - data.start_time),
        "talking_mode_count": len(talking_mode),
        "online": True,
    })

@require_auth
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

@require_auth
async def api_blocked(request):
    return web.json_response({"blocked": list(data.blocked_users)})

@require_auth
async def api_logs(request):
    return web.json_response({"logs": list(data.events_log)[-100:][::-1]})

@require_auth
async def api_settings_get(request):
    return web.json_response({"settings": data.settings})

@require_auth
async def api_settings_set(request):
    body = await request.json()
    for k, v in body.items():
        if k in DEFAULT_SETTINGS:
            data.settings[k] = v
    data.save()
    data.log("CFG", f"تحديث الإعدادات: {list(body.keys())}")
    return web.json_response({"ok": True, "settings": data.settings})

@require_auth
async def api_block(request):
    body = await request.json()
    uid = int(body["user_id"])
    data.blocked_users.add(uid)
    data.save()
    data.log("BLOCK", f"حظر يدوي: {uid}", uid)
    return web.json_response({"ok": True})

@require_auth
async def api_unblock(request):
    body = await request.json()
    uid = int(body["user_id"])
    data.blocked_users.discard(uid)
    data.save()
    data.log("UNBLOCK", f"فك حظر: {uid}", uid)
    return web.json_response({"ok": True})

@require_auth
async def api_unblock_all(request):
    n = len(data.blocked_users)
    data.blocked_users.clear()
    data.save()
    data.log("UNBLOCK", f"فك حظر جماعي: {n}")
    return web.json_response({"ok": True, "count": n})

@require_auth
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

@require_auth
async def api_clear_user(request):
    body = await request.json()
    uid = str(int(body["user_id"]))
    data.users.pop(uid, None)
    data.save()
    return web.json_response({"ok": True})

@require_auth
async def api_clear_all(request):
    data.users.clear()
    data.save()
    return web.json_response({"ok": True})

@require_auth
async def api_info_card(request):
    uid = int(request.query["user_id"])
    card = await build_info_card(uid)
    return web.json_response({"card": card or "تعذّر الجلب"})

async def api_export(request):
    if not is_authed(request):
        return web.Response(text="unauthorized", status=401)
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
# 🌐 صفحات HTML
# ===================================================================

LOGIN_HTML = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>🔐 Cyber Engine - دخول</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:radial-gradient(circle at 20% 20%,#1a0033,#000);color:#eee;
  min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0}
.box{background:rgba(20,20,40,.9);padding:40px;border-radius:20px;border:1px solid #7ef3;
  box-shadow:0 0 60px #7ef4;width:90%;max-width:380px;text-align:center}
h1{color:#7ef;margin:0 0 8px;font-size:28px}
p{color:#999;margin:0 0 24px;font-size:13px}
input{width:100%;padding:14px;border-radius:10px;border:1px solid #444;background:#0a0a18;color:#fff;
  font-size:16px;margin-bottom:14px;text-align:center}
input:focus{outline:none;border-color:#7ef;box-shadow:0 0 12px #7ef6}
button{width:100%;padding:14px;border-radius:10px;border:0;background:linear-gradient(135deg,#7ef,#5af);
  color:#000;font-weight:bold;font-size:16px;cursor:pointer;transition:.2s}
button:hover{transform:translateY(-2px);box-shadow:0 8px 20px #7ef6}
.err{color:#f66;margin-top:10px;font-size:13px;min-height:18px}
</style></head><body>
<div class="box">
  <h1>💀 CYBER ENGINE</h1>
  <p>لوحة التحكم المتقدمة</p>
  <input id="pw" type="password" placeholder="كلمة المرور" autofocus onkeydown="if(event.key==='Enter')login()">
  <button onclick="login()">دخول 🔓</button>
  <div class="err" id="err"></div>
</div>
<script>
async function login(){
  const pw=document.getElementById('pw').value;
  const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw})});
  const d=await r.json();
  if(d.ok){location.href='/dashboard'}
  else{document.getElementById('err').textContent=d.error||'خطأ'}
}
</script></body></html>"""


DASHBOARD_HTML = r"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>💀 Cyber Engine Dashboard</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:#070710;color:#e6e6f0;margin:0;padding:0}
header{background:linear-gradient(90deg,#1a0033,#0a0a20);padding:18px 28px;border-bottom:1px solid #7ef3;
  display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}
header h1{margin:0;color:#7ef;font-size:22px}
header .live{display:flex;align-items:center;gap:8px;font-size:13px;color:#9f9}
header .dot{width:10px;height:10px;border-radius:50%;background:#0f0;box-shadow:0 0 10px #0f0;animation:p 1.5s infinite}
@keyframes p{50%{opacity:.3}}
main{padding:24px;max-width:1400px;margin:0 auto}
.tabs{display:flex;gap:6px;margin-bottom:20px;flex-wrap:wrap;background:#0f0f20;padding:6px;border-radius:12px}
.tab{padding:10px 18px;border-radius:8px;cursor:pointer;color:#aaa;font-weight:500;transition:.2s;border:0;background:transparent}
.tab:hover{color:#fff;background:#1a1a30}
.tab.active{background:linear-gradient(135deg,#7ef,#5af);color:#000}
.panel{display:none}
.panel.active{display:block;animation:fade .3s}
@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1}}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}
.card{background:linear-gradient(135deg,#161628,#0e0e1c);padding:18px;border-radius:14px;border:1px solid #2a2a44;
  position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;right:0;width:60px;height:60px;
  background:radial-gradient(circle,#7ef3,transparent);border-radius:50%}
.card .label{color:#999;font-size:12px;margin-bottom:6px}
.card .val{font-size:30px;font-weight:bold;color:#7ef}
.card.green .val{color:#5f9}
.card.red .val{color:#f66}
.card.yellow .val{color:#fc6}
.box{background:#0f0f1e;border:1px solid #2a2a44;border-radius:14px;padding:18px;margin-bottom:18px}
.box h2{margin:0 0 14px;color:#7ef;font-size:18px;border-bottom:1px solid #2a2a44;padding-bottom:10px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 8px;border-bottom:1px solid #1f1f35;text-align:right}
th{background:#15152a;color:#7ef;font-weight:600;position:sticky;top:0}
tr:hover{background:#15152a}
.btn{padding:7px 12px;border-radius:7px;border:0;cursor:pointer;font-size:12px;font-weight:600;margin:2px;transition:.2s}
.btn:hover{transform:translateY(-1px)}
.btn-block{background:#c33;color:#fff}
.btn-unblock{background:#393;color:#fff}
.btn-info{background:#369;color:#fff}
.btn-clear{background:#555;color:#fff}
.btn-primary{background:linear-gradient(135deg,#7ef,#5af);color:#000}
input,textarea,select{background:#0a0a18;border:1px solid #2a2a44;color:#fff;padding:9px 12px;border-radius:8px;
  font-size:14px;width:100%;font-family:inherit}
input:focus,textarea:focus{outline:none;border-color:#7ef}
.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:12px}
.row label{display:block;color:#9aa;font-size:12px;margin-bottom:4px}
.search{margin-bottom:12px}
.badge{padding:3px 8px;border-radius:5px;font-size:11px;font-weight:bold}
.badge.b{background:#c33;color:#fff}
.badge.t{background:#fc6;color:#000}
.badge.a{background:#393;color:#fff}
.toggle{display:flex;align-items:center;gap:10px;padding:10px;background:#0a0a18;border-radius:8px;cursor:pointer}
.toggle input{width:auto;margin:0}
.log{font-family:'Courier New',monospace;font-size:12px;max-height:500px;overflow-y:auto;background:#000;padding:12px;border-radius:8px}
.log .l{padding:4px 8px;border-bottom:1px solid #111;display:flex;gap:10px}
.log .l .t{color:#666;min-width:75px}
.log .l .y{min-width:70px;font-weight:bold}
.log .y.MSG{color:#7ef}.log .y.BLOCK{color:#f66}.log .y.WARN{color:#fc6}
.log .y.SEND{color:#5f9}.log .y.UNBLOCK{color:#5f9}.log .y.ERROR{color:#f33}.log .y.CFG{color:#a8f}
pre{background:#000;color:#7ef;padding:14px;border-radius:8px;overflow-x:auto;font-size:12px;white-space:pre-wrap}
.actions{display:flex;gap:8px;flex-wrap:wrap}
#toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#7ef;color:#000;padding:12px 24px;
  border-radius:10px;font-weight:bold;display:none;z-index:100;box-shadow:0 4px 20px #7ef6}
</style></head><body>
<header>
  <h1>💀 CYBER ENGINE - لوحة التحكم</h1>
  <div class="live"><span class="dot"></span><span id="status">متصل</span> · <span id="uptime">-</span></div>
</header>
<main>
<div class="tabs">
  <button class="tab active" data-tab="overview">📊 نظرة عامة</button>
  <button class="tab" data-tab="users">👥 المستخدمين</button>
  <button class="tab" data-tab="blocked">🚫 المحظورين</button>
  <button class="tab" data-tab="settings">⚙️ الإعدادات</button>
  <button class="tab" data-tab="send">📤 إرسال</button>
  <button class="tab" data-tab="logs">📜 السجل</button>
  <button class="tab" data-tab="tools">🛠️ أدوات</button>
</div>

<div class="panel active" id="overview">
  <div class="cards" id="stats-cards"></div>
  <div class="box"><h2>📜 آخر الأحداث</h2><div class="log" id="recent-log"></div></div>
</div>

<div class="panel" id="users">
  <div class="box">
    <h2>👥 جميع المستخدمين</h2>
    <input class="search" id="usearch" placeholder="🔍 ابحث بالاسم أو ID أو @يوزر..." oninput="renderUsers()">
    <div style="max-height:600px;overflow-y:auto">
      <table id="utable"><thead><tr>
        <th>الاسم</th><th>اليوزر</th><th>ID</th><th>رسائل</th><th>آخر ظهور</th><th>الحالة</th><th>إجراءات</th>
      </tr></thead><tbody></tbody></table>
    </div>
  </div>
</div>

<div class="panel" id="blocked">
  <div class="box">
    <h2>🚫 قائمة المحظورين</h2>
    <div class="actions" style="margin-bottom:14px">
      <button class="btn btn-unblock" onclick="unblockAll()">فك حظر الجميع</button>
      <input id="manual-block" placeholder="ID للحظر اليدوي" style="max-width:200px">
      <button class="btn btn-block" onclick="manualBlock()">حظر</button>
    </div>
    <div id="blocked-list"></div>
  </div>
</div>

<div class="panel" id="settings">
  <div class="box"><h2>⚙️ الإعدادات الحية</h2>
    <div class="row">
      <div><label>الحد الأقصى للرسائل قبل الحظر</label><input id="s_max_messages" type="number"></div>
      <div><label>حد التحذير</label><input id="s_warning_limit" type="number"></div>
      <div><label>فترة التبريد (ثانية)</label><input id="s_cooldown_seconds" type="number"></div>
      <div><label>تأخير الرد (ثانية)</label><input id="s_reply_delay" type="number" step="0.1"></div>
      <div><label>مهلة وضع المحادثة (ثانية)</label><input id="s_talking_timeout" type="number"></div>
      <div><label>اليوزر الخاص</label><input id="s_special_username"></div>
    </div>
    <div class="row">
      <label class="toggle"><input id="s_auto_reply" type="checkbox"> الرد التلقائي</label>
      <label class="toggle"><input id="s_send_info_card" type="checkbox"> إرسال بطاقة المعلومات</label>
      <label class="toggle"><input id="s_auto_block" type="checkbox"> الحظر التلقائي</label>
      <label class="toggle"><input id="s_silent_mode" type="checkbox"> الوضع الصامت</label>
    </div>
    <div style="margin-top:14px">
      <label>الرد الخاص (لليوزر المميز)</label>
      <textarea id="s_special_reply" rows="4"></textarea>
    </div>
    <div style="margin-top:14px">
      <label>قائمة الردود التلقائية (سطر لكل رد)</label>
      <textarea id="s_replies" rows="6"></textarea>
    </div>
    <button class="btn btn-primary" style="margin-top:14px" onclick="saveSettings()">💾 حفظ الإعدادات</button>
  </div>
</div>

<div class="panel" id="send">
  <div class="box"><h2>📤 إرسال رسالة</h2>
    <div class="row">
      <div><label>User ID</label><input id="send-uid" placeholder="مثلاً: 123456789"></div>
    </div>
    <label>الرسالة</label>
    <textarea id="send-text" rows="5" placeholder="اكتب رسالتك هنا..."></textarea>
    <button class="btn btn-primary" style="margin-top:12px" onclick="sendMsg()">📨 إرسال</button>
  </div>
</div>

<div class="panel" id="logs">
  <div class="box">
    <h2>📜 سجل الأحداث المباشر</h2>
    <div class="log" id="full-log"></div>
  </div>
</div>

<div class="panel" id="tools">
  <div class="box"><h2>🛠️ أدوات إدارية</h2>
    <div class="actions">
      <a class="btn btn-primary" href="/api/export" download>⬇️ تصدير كل البيانات (JSON)</a>
      <button class="btn btn-block" onclick="if(confirm('متأكد؟ سيتم مسح جميع إحصائيات المستخدمين'))clearAll()">🗑️ مسح كل الإحصائيات</button>
    </div>
    <div style="margin-top:20px">
      <h3 style="color:#7ef">🔍 عرض بطاقة معلومات يدوياً</h3>
      <div class="row">
        <input id="info-uid" placeholder="User ID">
        <button class="btn btn-info" onclick="loadCard()">جلب البطاقة</button>
      </div>
      <pre id="info-result">—</pre>
    </div>
  </div>
</div>

</main>
<div id="toast"></div>

<script>
let usersData=[],settingsData={};
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',2500)}
async function api(p,o={}){const r=await fetch(p,{...o,headers:{'Content-Type':'application/json',...(o.headers||{})}});if(r.status===401){location.href='/login';return}return r.json()}
function fmt(s){if(!s)return'-';return s.replace('T',' ').slice(0,16)}
function upt(s){const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return `${h}س ${m}د`}

document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');document.getElementById(t.dataset.tab).classList.add('active');
});

async function loadStats(){
  const d=await api('/api/stats');if(!d)return;
  const c=document.getElementById('stats-cards');
  c.innerHTML=`
    <div class="card"><div class="label">المستخدمين</div><div class="val">${d.users}</div></div>
    <div class="card red"><div class="label">المحظورين</div><div class="val">${d.blocked}</div></div>
    <div class="card green"><div class="label">إجمالي الرسائل</div><div class="val">${d.total_messages}</div></div>
    <div class="card yellow"><div class="label">رسائل اليوم</div><div class="val">${d.today_messages}</div></div>
    <div class="card"><div class="label">وضع محادثة نشط</div><div class="val">${d.talking_mode_count}</div></div>
    <div class="card green"><div class="label">مدة التشغيل</div><div class="val" style="font-size:20px">${upt(d.uptime_seconds)}</div></div>
  `;
  document.getElementById('uptime').textContent='⏱️ '+upt(d.uptime_seconds);
}

async function loadUsers(){const d=await api('/api/users');if(!d)return;usersData=d.users;renderUsers()}
function renderUsers(){
  const q=document.getElementById('usearch').value.toLowerCase();
  const tb=document.querySelector('#utable tbody');
  tb.innerHTML='';
  usersData.filter(u=>!q||u.name.toLowerCase().includes(q)||u.username.toLowerCase().includes(q)||u.id.includes(q)).forEach(u=>{
    let badge=u.blocked?'<span class="badge b">محظور</span>':u.talking?'<span class="badge t">محادثة</span>':'<span class="badge a">نشط</span>';
    tb.innerHTML+=`<tr>
      <td>${u.name}</td><td>${u.username?'@'+u.username:'-'}</td><td>${u.id}</td>
      <td>${u.messages}</td><td>${fmt(u.last_seen)}</td><td>${badge}</td>
      <td>
        ${u.blocked?`<button class="btn btn-unblock" onclick="unblock(${u.id})">فك</button>`:`<button class="btn btn-block" onclick="block(${u.id})">حظر</button>`}
        <button class="btn btn-info" onclick="quickCard(${u.id})">بطاقة</button>
        <button class="btn btn-clear" onclick="clearUser(${u.id})">مسح</button>
      </td></tr>`;
  });
}

async function loadBlocked(){
  const d=await api('/api/blocked');if(!d)return;
  const el=document.getElementById('blocked-list');
  if(!d.blocked.length){el.innerHTML='<p style="color:#999">لا يوجد محظورين</p>';return}
  el.innerHTML='<table><thead><tr><th>ID</th><th>إجراء</th></tr></thead><tbody>'+
    d.blocked.map(id=>`<tr><td>${id}</td><td><button class="btn btn-unblock" onclick="unblock(${id})">فك الحظر</button></td></tr>`).join('')+'</tbody></table>';
}

async function loadSettings(){
  const d=await api('/api/settings');if(!d)return;settingsData=d.settings;
  for(const k in d.settings){
    const el=document.getElementById('s_'+k);if(!el)continue;
    if(el.type==='checkbox')el.checked=d.settings[k];
    else if(k==='replies')el.value=d.settings[k].join('\n');
    else el.value=d.settings[k];
  }
}
async function saveSettings(){
  const payload={};
  ['max_messages','warning_limit','cooldown_seconds','talking_timeout'].forEach(k=>payload[k]=+document.getElementById('s_'+k).value);
  payload.reply_delay=parseFloat(document.getElementById('s_reply_delay').value);
  ['auto_reply','send_info_card','auto_block','silent_mode'].forEach(k=>payload[k]=document.getElementById('s_'+k).checked);
  payload.special_username=document.getElementById('s_special_username').value;
  payload.special_reply=document.getElementById('s_special_reply').value;
  payload.replies=document.getElementById('s_replies').value.split('\n').filter(x=>x.trim());
  await api('/api/settings',{method:'POST',body:JSON.stringify(payload)});
  toast('✅ تم الحفظ');
}

async function loadLogs(elId='full-log',limit=null){
  const d=await api('/api/logs');if(!d)return;
  let logs=d.logs;if(limit)logs=logs.slice(0,limit);
  document.getElementById(elId).innerHTML=logs.map(l=>`<div class="l"><span class="t">${l.time.slice(11)}</span><span class="y ${l.type}">${l.type}</span><span>${l.msg}</span></div>`).join('');
}

async function block(id){await api('/api/block',{method:'POST',body:JSON.stringify({user_id:id})});toast('🚫 محظور');loadUsers();loadStats();loadBlocked()}
async function unblock(id){await api('/api/unblock',{method:'POST',body:JSON.stringify({user_id:id})});toast('✅ فُك الحظر');loadUsers();loadStats();loadBlocked()}
async function unblockAll(){if(!confirm('فك حظر الجميع؟'))return;await api('/api/unblock_all',{method:'POST',body:'{}'});toast('✅');loadBlocked();loadStats();loadUsers()}
async function manualBlock(){const id=document.getElementById('manual-block').value;if(!id)return;await block(+id);document.getElementById('manual-block').value=''}
async function clearUser(id){if(!confirm('مسح إحصائيات هذا المستخدم؟'))return;await api('/api/clear_user',{method:'POST',body:JSON.stringify({user_id:id})});loadUsers();loadStats()}
async function clearAll(){await api('/api/clear_all',{method:'POST',body:'{}'});toast('🗑️ تم المسح');loadUsers();loadStats()}
async function sendMsg(){
  const uid=document.getElementById('send-uid').value,text=document.getElementById('send-text').value;
  if(!uid||!text)return toast('املأ الحقول');
  const r=await api('/api/send',{method:'POST',body:JSON.stringify({user_id:+uid,text})});
  toast(r.ok?'📨 أُرسلت':'❌ '+r.error);
  if(r.ok)document.getElementById('send-text').value='';
}
async function quickCard(id){document.querySelector('[data-tab=tools]').click();document.getElementById('info-uid').value=id;loadCard()}
async function loadCard(){
  const id=document.getElementById('info-uid').value;if(!id)return;
  document.getElementById('info-result').textContent='⏳ جاري الجلب...';
  const r=await api('/api/info_card?user_id='+id);
  document.getElementById('info-result').textContent=r.card;
}

function refreshAll(){loadStats();loadLogs('recent-log',15);loadLogs('full-log')}
loadStats();loadUsers();loadBlocked();loadSettings();loadLogs('recent-log',15);loadLogs('full-log');
setInterval(refreshAll,5000);
setInterval(loadUsers,15000);
</script></body></html>"""


async def page_login(request):
    return web.Response(text=LOGIN_HTML, content_type="text/html")

async def page_dashboard(request):
    if not is_authed(request):
        raise web.HTTPFound("/login")
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")

async def page_root(request):
    raise web.HTTPFound("/dashboard" if is_authed(request) else "/login")

async def page_health(request):
    return web.Response(text=f"OK | users={len(data.users)} | blocked={len(data.blocked_users)}")

# ===================================================================
# 🌐 تشغيل خادم الويب
# ===================================================================

async def start_web():
    app = web.Application()
    # صفحات
    app.router.add_get("/", page_root)
    app.router.add_get("/login", page_login)
    app.router.add_get("/dashboard", page_dashboard)
    app.router.add_get("/health", page_health)
    # API
    app.router.add_post("/api/login", api_login)
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
    print(f"🌐 لوحة التحكم: http://0.0.0.0:{port}")
    print(f"🔐 كلمة المرور: {DASHBOARD_PASSWORD}")

# ===================================================================
# 🚀 التشغيل
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 CYBER AI ENGINE - GIGA EDITION v2 💀")
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
    data.log("BOOT", "تم تشغيل البوت")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
