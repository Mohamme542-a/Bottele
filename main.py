import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from collections import defaultdict
import time

# ========== بياناتك ==========
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION_STRING = "1BJWap1wBu6w86ZCJ0lFSD6f1wa_1NbkQhLtatilciRQm6HONT7vBv2zgzOE_6qFh94jwxSaa4rYTcv6OZjlW7rzDZ8Do6jTyNrd4zSS4sBNVGmPEerohru1GHyCYXTfiOWI0j9KC0RTEJ-4zb3EKi3F6-kr-L8k7OLAFCSuUJJdqeE6lZmH_9JeB6nKVrY1n63f8eMrnmms3vw7TtdEjmNyYuvh0c5_4AfOnsza2kYYO1icXpAGv7pbTrM802LvbMJ688jVXrpHDU_rfngNSLIDs9Z7FnBdk1AwXfi3ampUryUIeLdrkFkmVrsLhT3dSWEmEWbQ72zjx6WnIv1LXBv-1_-QnD1A="


# ========== إعدادات الحظر التلقائي ==========
MAX_MESSAGES = 5  # 5 رسائل يؤدي للحظر
WARNING_LIMIT = 3  # عند 3 رسائل يطلع تحذير
COOLDOWN_SECONDS = 10  # خلال 10 ثواني (إذا أرسل 5 خلال 10 ثواني ينحظر)

# ========== ردود مخصصة ==========
CUSTOM = {
    "@Yaharp": "مرحبا حجي فرات العراقي تم تسليم رسالتك إلى أبو إبراهيم وسيتم الرد عليك قريبا نتشكرك على مراسلتك لنا",
    "aksn78": "⭐ سيتم الرد عليك لاحقا شكرا على التواصل",
}

DEFAULT = """✨ صاحب الحساب مشغول حاليا يرجى ترك رسالتك للرد عليها لاحقا ✨

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
💫 أنا بوت رد تلقائي
📨 راح أرد عليك قريباً
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"""

# ========== تخزين بيانات المستخدمين ==========
user_messages = defaultdict(list)  # user_id -> list of timestamps
blocked_users = set()  # المستخدمين المحظورين

# ========== دوال الحظر ==========
def check_spam(user_id):
    """ترجع (هل يعتبر سبام، عدد الرسائل خلال الفترة)"""
    now = time.time()
    # خذ الرسائل خلال آخر COOLDOWN_SECONDS ثانية
    recent = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
    user_messages[user_id] = recent  # نظف القديم
    return len(recent) >= MAX_MESSAGES, len(recent)

def add_message(user_id):
    """تسجيل رسالة جديدة"""
    user_messages[user_id].append(time.time())

# ========== إيموجيات تليجرام مميزة ==========
EMOJIS = {
    "hello": "👋🌺",
    "warn": "⚠️🧨",
    "block": "🔨🚫",
    "success": "✅✨",
    "star": "⭐🌟",
    "heart": "💖🌸",
    "fire": "🔥⚡",
    "cool": "😎🌀",
}

# ========== الكود الرئيسي ==========
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username or sender.first_name or ""
    
    # إذا كان محظور، لا ترد وامسح الرسالة (اختياري)
    if user_id in blocked_users:
        await event.delete()
        return
    
    # تسجيل الرسالة
    add_message(user_id)
    
    # التحقق من السبام
    is_spam, count = check_spam(user_id)
    
    # تحذير عند 3 رسائل
    if count == WARNING_LIMIT and not is_spam:
        warning_msg = f"""{EMOJIS['warn']} **تحذير من التكرار** {EMOJIS['warn']}
        
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
لقد أرسلت {count} رسائل خلال {COOLDOWN_SECONDS} ثانية

⚠️ إذا وصلت {MAX_MESSAGES} رسائل، سيتم **حظرك** تلقائياً
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
{EMOJIS['cool']} رجاءً انتظر قليلاً قبل إرسال رسائل جديدة"""
        await event.reply(warning_msg)
        print(f"⚠️ تحذير لـ {username}: {count} رسائل")
        return
    
    # حظر عند 5 رسائل
    if is_spam:
        blocked_users.add(user_id)
        block_msg = f"""{EMOJIS['block']} **تم حظرك تلقائياً** {EMOJIS['block']}
        
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🚫 سبب الحظر: إرسال {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية

📌 لن تصلك أي ردود من هذا البوت بعد الآن
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
{EMOJIS['heart']} للفك، تواصل مع المشرف"""
        await event.reply(block_msg)
        print(f"🔨 تم حظر {username}")
        return
    
    # رد عادي مع إيموجيات
    reply_text = CUSTOM.get(username, DEFAULT)
    
    # أضف إيموجي عشوائي أحياناً
    import random
    extra_emoji = random.choice([EMOJIS['star'], EMOJIS['heart'], EMOJIS['fire'], ""])
    
    if extra_emoji:
        reply_text = f"{extra_emoji}\n\n{reply_text}"
    
    await asyncio.sleep(2)
    await event.reply(reply_text)
    print(f"✅ رد على {username}")

async def main():
    await client.start()
    me = await client.get_me()
    print(f"🚀 TgAuto شغال 24 ساعة")
    print(f"👤 الحساب: {me.first_name} (@{me.username})")
    print(f"⚙️ إعدادات الحظر: {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية")
    print(f"⚠️ تحذير عند {WARNING_LIMIT} رسائل")
    await client.run_until_disconnected()

asyncio.run(main())
