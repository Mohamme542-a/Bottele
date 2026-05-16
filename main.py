import asyncio
import time
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

# ==================== بياناتك ====================
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="

# ==================== إعدادات الحظر ====================
MAX_MESSAGES = 5
WARNING_LIMIT = 3
COOLDOWN_SECONDS = 10

# ==================== ردود مخصصة ====================
CUSTOM = {
    "Yaharp": "🌹 مرحبا !حجي فرات العراقي تم تسليم رسالتك وسيتم الرد عليك في أقرب وقت🏴 ",
    "aksn78": "🌹 مرحبا !حجي فرات العراقي تم تسليم رسالتك وسيتم الرد عليك في أقرب وقت🏴 ",
}
DEFAULT_REPLY = "✨ مرحباً! تم تسليم رسالتك وسيتم الرد عليك في أقرب وقت إن شاء الله 🏴✨"

# ==================== الكود ====================
user_messages = defaultdict(list)
blocked_users = set()

def check_spam(user_id):
    now = time.time()
    recent = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
    user_messages[user_id] = recent
    return len(recent) >= MAX_MESSAGES, len(recent)

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    sender = await event.get_sender()
    uid = sender.id
    name = sender.username or sender.first_name or ""
    if uid in blocked_users:
        return
    user_messages[uid].append(time.time())
    is_spam, count = check_spam(uid)
    if count == WARNING_LIMIT and not is_spam:
        await event.reply(f"⚠️ تحذير: وصلت {count} رسائل خلال {COOLDOWN_SECONDS} ثانية")
        return
    if is_spam:
        blocked_users.add(uid)
        await event.reply(f"🔨 تم حظرك لإرسال {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية")
        return
    reply = CUSTOM.get(name, DEFAULT_REPLY)
    await asyncio.sleep(2)
    await event.reply(reply)

async def main():
    await client.start()
    me = await client.get_me()
    print(f"🚀 شغال: @{me.username}")
    await client.run_until_disconnected()

asyncio.run(main())
