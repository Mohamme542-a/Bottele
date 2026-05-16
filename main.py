# ===================================================================
# 💀 CYBER ENGINE - ULTRA STABLE EDITION 💀
# ===================================================================

import asyncio
import random
import time
import os
import json

from datetime import datetime
from collections import defaultdict

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from aiohttp import web

# ===================================================================
# ✅ بيانات الحساب
# ===================================================================

API_ID = 34082021
API_HASH = "ضع_الهاش"
SESSION = "ضع_السيشن"
OWNER_ID = 8676210788

# ===================================================================
# ⚙️ الإعدادات
# ===================================================================

MAX_MESSAGES = 8
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
REPLY_DELAY = 0.6

# ===================================================================
# 💬 الردود
# ===================================================================

REPLIES = [
    "أهلاً بك 🌸",
    "تم استلام رسالتك ✅",
    "شكراً لتواصلك 💙",
    "وصلت رسالتك بنجاح ✨",
]

# ===================================================================
# 📂 إدارة البيانات
# ===================================================================

class DataManager:
    def __init__(self):
        self.users = {}
        self.blocked_users = set()
        self.load()

    def load(self):
        try:
            if os.path.exists("users.json"):
                with open("users.json", "r", encoding="utf-8") as f:
                    self.users = json.load(f)

            if os.path.exists("blocked.json"):
                with open("blocked.json", "r") as f:
                    self.blocked_users = set(json.load(f))

        except Exception as e:
            print("LOAD ERROR:", e)

    def save(self):
        try:
            with open("users.json", "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)

            with open("blocked.json", "w") as f:
                json.dump(list(self.blocked_users), f)

        except Exception as e:
            print("SAVE ERROR:", e)

data = DataManager()

# ===================================================================
# 🚀 تشغيل العميل
# ===================================================================

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)

# ===================================================================
# 🛡️ مكافحة السبام
# ===================================================================

user_timestamps = defaultdict(list)

async def check_spam(user_id):
    now = time.time()

    user_timestamps[user_id] = [
        ts for ts in user_timestamps[user_id]
        if now - ts < COOLDOWN_SECONDS
    ]

    user_timestamps[user_id].append(now)

    return len(user_timestamps[user_id])

# ===================================================================
# 🔍 جلب معلومات المستخدم
# ===================================================================

async def get_user_info(user_id):

    result = {
        "name": "غير معروف",
        "username": "لا يوجد",
        "id": user_id,
        "phone": "مخفي",
        "premium": "❌",
        "verified": "❌",
        "bot": "❌",
        "scam": "❌",
        "fake": "❌",
        "photos": 0,
        "bio": "لا يوجد",
        "common_groups": []
    }

    try:

        full = await client(GetFullUserRequest(user_id))
        user = full.user

        result["name"] = (
            f"{user.first_name or ''} "
            f"{user.last_name or ''}"
        ).strip()

        result["username"] = (
            f"@{user.username}"
            if user.username else "لا يوجد"
        )

        result["phone"] = (
            user.phone if user.phone else "مخفي"
        )

        result["premium"] = (
            "✅" if getattr(user, "premium", False) else "❌"
        )

        result["verified"] = (
            "✅" if getattr(user, "verified", False) else "❌"
        )

        result["bot"] = (
            "✅" if user.bot else "❌"
        )

        result["scam"] = (
            "⚠️" if getattr(user, "scam", False) else "❌"
        )

        result["fake"] = (
            "⚠️" if getattr(user, "fake", False) else "❌"
        )

        result["bio"] = (
            full.about[:120]
            if full.about else "لا يوجد"
        )

        # ===== الصور =====

        try:
            photos = 0

            async for _ in client.iter_profile_photos(user_id, limit=10):
                photos += 1

            result["photos"] = photos

        except Exception as e:
            print("PHOTO ERROR:", e)

        # ===== المجموعات المشتركة =====

        try:

            groups = []

            async for dialog in client.iter_dialogs():

                if not (dialog.is_group or dialog.is_channel):
                    continue

                try:
                    await client(
                        GetParticipantRequest(
                            dialog.entity,
                            user_id
                        )
                    )

                    groups.append(dialog.name[:30])

                    if len(groups) >= 5:
                        break

                except:
                    continue

            result["common_groups"] = groups

        except Exception as e:
            print("GROUP ERROR:", e)

    except Exception as e:
        print("INFO ERROR:", e)

    return result

# ===================================================================
# 📋 بناء البطاقة
# ===================================================================

def build_card(info):

    groups = "\n".join(
        [f"• {g}" for g in info["common_groups"]]
    ) if info["common_groups"] else "لا يوجد"

    text = f"""
💀 معلومات الحساب 💀

👤 الاسم:
{info['name']}

🆔 المعرف:
{info['id']}

🔗 اليوزر:
{info['username']}

📞 الهاتف:
{info['phone']}

🖼️ الصور:
{info['photos']}

💎 بريميوم:
{info['premium']}

✅ موثق:
{info['verified']}

🤖 بوت:
{info['bot']}

🚨 مشبوه:
{info['scam']}

🎭 مزيف:
{info['fake']}

📜 النبذة:
{info['bio']}

📢 مجموعات مشتركة:
{groups}

⏰ الوقت:
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return text

# ===================================================================
# 📩 استقبال الرسائل
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def handler(event):

    if not event.is_private:
        return

    sender = await event.get_sender()

    user_id = sender.id

    if user_id == OWNER_ID:
        return

    # ===== محظور =====

    if user_id in data.blocked_users:
        return

    # ===== سبام =====

    count = await check_spam(user_id)

    if count == WARNING_LIMIT:
        await event.reply("⚠️ الرجاء التخفيف قليلاً")
        return

    if count >= MAX_MESSAGES:

        data.blocked_users.add(user_id)
        data.save()

        await event.reply(
            f"🚫 تم حظرك بسبب السبام"
        )

        return

    # ===== المعلومات =====

    info = await get_user_info(user_id)

    try:

        await event.reply(
            build_card(info),
            parse_mode=None
        )

    except Exception as e:
        print("CARD ERROR:", e)

    # ===== الرد التلقائي =====

    await asyncio.sleep(REPLY_DELAY)

    try:

        await event.reply(
            random.choice(REPLIES)
        )

    except Exception as e:
        print("REPLY ERROR:", e)

    # ===== حفظ =====

    uid = str(user_id)

    if uid not in data.users:
        data.users[uid] = {
            "name": info["name"],
            "messages": 0
        }

    data.users[uid]["messages"] += 1
    data.users[uid]["last_seen"] = datetime.now().isoformat()

    data.save()

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"{info['name']}"
    )

# ===================================================================
# 🌐 السيرفر
# ===================================================================

async def dashboard(request):

    html = f"""
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>CYBER ENGINE</title>

        <style>

        body {{
            background: #0f0f0f;
            color: white;
            font-family: sans-serif;
            padding: 20px;
        }}

        .box {{
            background: #1b1b1b;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}

        </style>

    </head>

    <body>

        <div class="box">
            <h1>💀 CYBER ENGINE 💀</h1>

            <p>👥 المستخدمين: {len(data.users)}</p>

            <p>🚫 المحظورين: {len(data.blocked_users)}</p>

            <p>⏰ الوقت:
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>

    </body>
    </html>
    """

    return web.Response(
        text=html,
        content_type="text/html"
    )

async def health(request):

    return web.Response(
        text="OK"
    )

async def start_web():

    app = web.Application()

    app.router.add_get("/", dashboard)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)

    await runner.setup()

    # ⚠️ لم نغير البورت
    site = web.TCPSite(
        runner,
        "0.0.0.0",
        8080
    )

    await site.start()

    print("🌐 WEB STARTED :8080")

# ===================================================================
# 🚀 MAIN
# ===================================================================

async def main():

    print("=" * 50)
    print("💀 CYBER ENGINE STARTING 💀")
    print("=" * 50)

    await client.start()

    me = await client.get_me()

    print(f"✅ Logged as: {me.first_name}")

    asyncio.create_task(start_web())

    print("🚀 SYSTEM ONLINE")

    await client.run_until_disconnected()

# ===================================================================

if __name__ == "__main__":
    asyncio.run(main())
