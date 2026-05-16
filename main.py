import asyncio
import time
import random
from collections import defaultdict
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==================== بياناتك (خليها زي ما هي) ====================
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="

# ==================== روابط صور متحركة GIF (أنمي محتشم وجودة عالية) ====================
# روابط لصور متحركة من Tenor (كلها أنمي محترم)
ANIME_GIFS = [
    "https://media.tenor.com/mVv9yvKvX2sAAAAC/anime-peace.gif",      # سلام وتحية
    "https://media.tenor.com/-hxP9V3x6zMAAAAC/anime-welcome.gif",    # ترحيب
    "https://media.tenor.com/x8v1XHfZ9bQAAAAC/anime-thank-you.gif",  # شكر
    "https://media.tenor.com/Jv7qR6P8c4sAAAAC/anime-smile.gif",      # ابتسامة
    "https://media.tenor.com/6jQpJkZwQzMAAAAC/anime-hello.gif",      # مرحباً
    "https://media.tenor.com/G7f0rLvqx8oAAAAC/anime-cute.gif",       # لطيف
    "https://media.tenor.com/Y8Qz-qQqGK8AAAAC/anime-wave.gif",       # لوح بيدك
    "https://media.tenor.com/tP7Yq3zXQ9QAAAAC/anime-nice.gif",       # لطيف
]

# رابط خاص لـ Yaharp (صورة مميزة)
SPECIAL_GIF = "https://media.tenor.com/RfyX7xVqZ8YAAAAC/anime-respect.gif"  # احترام خاص

# ==================== ردود نصية ====================
DEFAULT_TEXT = """✨ **مرحباً! شكراً لتواصلك معنا** ✨

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📬 صاحب الحساب مشغول حالياً
⏰ سيتم الرد عليك في أقرب وقت
💫 _نشكرك على تفهمك_
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"""

SPECIAL_TEXT = """🌹✨ **مرحباً حجي فرات العراقي** ✨🌹

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📨 تم تسليم رسالتك بنجاح
⏳ سيتم الرد عليك لاحقاً
💚 نشكرك على التواصل معنا
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 _تحيات فريق الدعم_ 🌸"""

# ==================== إعدادات الحماية ====================
MAX_MESSAGES = 5
WARNING_LIMIT = 3
COOLDOWN_SECONDS = 60
REPLY_DELAY = 2

# قائمة الأصدقاء (لن يتم حظرهم)
FRIENDS = []

# ==================== تخزين البيانات ====================
user_messages = defaultdict(list)
blocked_users = set()
talking_with = {}
sleep_mode = False

def check_spam(user_id):
    now = time.time()
    recent = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
    user_messages[user_id] = recent
    return len(recent) >= MAX_MESSAGES, len(recent)

def add_message(user_id):
    user_messages[user_id].append(time.time())

# ==================== الكود الرئيسي ====================
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    global sleep_mode
    
    if not event.is_private:
        return
    
    if sleep_mode:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username or ""
    first_name = sender.first_name or ""
    
    # إذا كنت تتحدث معه حالياً
    if user_id in talking_with:
        if time.time() - talking_with[user_id] < 3600:  # ساعة
            return
    
    # إذا كان محظور
    if user_id in blocked_users:
        await event.reply("🚫 تم حظرك من هذا الحساب 🚫")
        return
    
    # التحقق من الأصدقاء (لن يتم حظرهم)
    is_friend = user_id in FRIENDS
    
    if not is_friend:
        add_message(user_id)
        is_spam, count = check_spam(user_id)
        
        if count == WARNING_LIMIT and not is_spam:
            await event.reply(f"⚠️ تحذير: وصلت {count} رسائل خلال {COOLDOWN_SECONDS} ثانية")
            return
        
        if is_spam:
            blocked_users.add(user_id)
            await event.reply(f"🔨 تم حظرك لإرسال {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية")
            print(f"🔨 تم حظر {first_name}")
            return
    
    # ========== إرسال الصور المتحركة ==========
    await asyncio.sleep(REPLY_DELAY)
    
    # لـ Yaharp: صورة مميزة + رد خاص
    if username == "Yaharp" or first_name == "Yaharp" or user_id == 123456789:
        await event.reply(SPECIAL_TEXT)
        await asyncio.sleep(0.5)
        await event.reply(file=SPECIAL_GIF)
        print(f"🎖️ صورة خاصة لـ {first_name}")
    
    # للباقي: صورة عشوائية + رد عام
    else:
        random_gif = random.choice(ANIME_GIFS)
        await event.reply(DEFAULT_TEXT)
        await asyncio.sleep(0.5)
        await event.reply(file=random_gif)
        print(f"✅ صورة لـ {first_name}")

@client.on(events.NewMessage(outgoing=True))
async def my_message_handler(event):
    if not event.is_private:
        return
    chat_id = event.chat_id
    talking_with[chat_id] = time.time()
    
    # تنظيف الإدخالات القديمة
    now = time.time()
    expired = [uid for uid, ts in talking_with.items() if now - ts > 3600]
    for uid in expired:
        del talking_with[uid]

@client.on(events.NewMessage(pattern=r'^/sleep$', outgoing=True))
async def sleep_mode_cmd(event):
    global sleep_mode
    sleep_mode = True
    await event.reply("😴 **وضع النوم مفعل** - لن يرد البوت على أي رسالة")

@client.on(events.NewMessage(pattern=r'^/wake$', outgoing=True))
async def wake_mode_cmd(event):
    global sleep_mode
    sleep_mode = False
    await event.reply("🔥 **وضع النوم معطل** - البوت يرد تلقائياً")

async def main():
    await client.start()
    me = await client.get_me()
    print("=" * 50)
    print("💀 **المطور المدمر - نسخة الصور المتحركة** 💀")
    print(f"👤 الحساب: {me.first_name}")
    print(f"🖼️ عدد الصور المتاحة: {len(ANIME_GIFS)}")
    print("🎖️ صورة خاصة لـ Yaharp")
    print("=" * 50)
    await client.run_until_disconnected()

asyncio.run(main())
