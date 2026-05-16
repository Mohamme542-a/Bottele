import asyncio
import time
import random
import re
from collections import defaultdict
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import ChannelPrivateError

# ==================== بياناتك ====================
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="

# ==================== روابط صور متحركة (GIF عالية الجودة) ====================
ANIME_GIFS = [
    "https://media.tenor.com/mVv9yvKvX2sAAAAC/anime-peace.gif",
    "https://media.tenor.com/-hxP9V3x6zMAAAAC/anime-welcome.gif",
    "https://media.tenor.com/x8v1XHfZ9bQAAAAC/anime-thank-you.gif",
    "https://media.tenor.com/Jv7qR6P8c4sAAAAC/anime-smile.gif",
]

SPECIAL_GIF = "https://media.tenor.com/RfyX7xVqZ8YAAAAC/anime-respect.gif"

# ==================== إعدادات الحماية ====================
MAX_MESSAGES = 5
WARNING_LIMIT = 3
COOLDOWN_SECONDS = 60
TALKING_TIMEOUT = 3600  # ساعة

# قائمة الأصدقاء (لن يتم حظرهم)
FRIENDS = []

# ==================== تخزين البيانات ====================
user_messages = defaultdict(list)
blocked_users = set()
talking_with = {}
user_names_history = defaultdict(set)
user_common_chats = defaultdict(list)

# ==================== دوال تحليل ====================
def analyze_mood(text):
    """تحليل المزاج من النص"""
    happy = ["حب", "شكر", "ممتاز", "جميل", "رائع", "❤️", "😊", "الله"]
    angry = ["غلط", "حرام", "زعل", "غبي", "حمق", "😡", "🤬", "تكفى"]
    h = sum(1 for w in happy if w in text.lower())
    a = sum(1 for w in angry if w in text.lower())
    if h > a:
        return "😊 **مهذب وسعيد**", "green"
    elif a > h:
        return "😠 **غاضب أو منزعج**", "red"
    return "😐 **عادي ومحايد**", "blue"

def detect_links(text):
    """كشف الروابط"""
    urls = re.findall(r'(https?://[^\s]+|t\.me/[^\s]+|@[^\s]+)', text)
    dangerous = ["t.me/joinchat", "t.me/+", "bit.ly", "goo.gl"]
    if urls:
        for url in urls:
            for d in dangerous:
                if d in url:
                    return urls, True  # روابط خطرة
        return urls, False
    return None, False

# ==================== دالة جلب المجموعات المشتركة ====================
async def get_common_chats(user_id):
    """جلب المجموعات والقنوات المشتركة مع المستخدم"""
    common = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    participant = await client(GetParticipantRequest(dialog.entity, user_id))
                    if participant:
                        common.append(dialog.name)
                except:
                    continue
    except:
        pass
    return common[:10]  # أقصى 10 نتائج

# ==================== دالة جلب الأسماء القديمة ====================
async def get_name_history(user_id):
    """جلب تاريخ أسماء المستخدم"""
    try:
        full = await client(GetFullUserRequest(user_id))
        user = full.user
        names = set()
        if user.first_name:
            names.add(user.first_name)
        if user.last_name:
            names.add(user.last_name)
        if user.username:
            names.add(f"@{user.username}")
        return list(names)
    except:
        return []

# ==================== الكود الرئيسي ====================
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username or "لا يوجد"
    first_name = sender.first_name or "لا يوجد"
    last_name = sender.last_name or ""
    text = event.message.message or ""
    
    # وضع المحادثة (إذا رديت على الشخص)
    if user_id in talking_with:
        if time.time() - talking_with[user_id] < TALKING_TIMEOUT:
            return
    
    # التحقق من الحظر
    if user_id in blocked_users:
        return
    
    # تسجيل الرسائل للسبام
    is_friend = user_id in FRIENDS
    if not is_friend:
        now = time.time()
        user_messages[user_id] = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
        user_messages[user_id].append(now)
        count = len(user_messages[user_id])
        
        if count == WARNING_LIMIT:
            await event.reply(f"⚠️🧨 **تحذير!** 🧨⚠️\n\nلقد أرسلت {count} رسائل خلال {COOLDOWN_SECONDS} ثانية\nإذا وصلت {MAX_MESSAGES} سيتم حظرك")
            return
        
        if count >= MAX_MESSAGES:
            try:
                await client(BlockRequest(id=user_id))
                blocked_users.add(user_id)
                await event.reply(f"🔨🚫 **تم حظرك تلقائياً** 🚫🔨\n\nالسبب: إرسال {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية")
                return
            except:
                pass
    
    # ========== جلب جميع المعلومات ==========
    await asyncio.sleep(1)
    
    # 1. جلب الأسماء القديمة
    name_history = await get_name_history(user_id)
    
    # 2. جلب المجموعات المشتركة
    common_chats = await get_common_chats(user_id)
    
    # 3. تحليل المزاج
    mood, mood_color = analyze_mood(text)
    
    # 4. كشف الروابط
    links, is_dangerous = detect_links(text)
    
    # ========== بطاقة المعلومات الكاملة ==========
    info_card = f"""🕵️‍♂️ **【 معلومات المرسل 】** 🕵️‍♂️

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
👤 **الاسم الحالي:** {first_name} {last_name}
🆔 **اسم المستخدم:** @{username}
🔢 **المعرف (ID):** `{user_id}`

📜 **الأسماء السابقة:**
{chr(10).join([f'  • {n}' for n in name_history[:5]]) if name_history else '  • لا توجد أسماء سابقة'}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
💬 **تحليل الرسالة:**
{mood}

📎 **الروابط:**
{chr(10).join([f'  • {link}' for link in links]) if links else '  • لا توجد روابط'}
{'  ⚠️ **تحذير: روابط خطرة مكتشفة!** ⚠️' if is_dangerous else ''}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📢 **المجموعات/القنوات المشتركة:**
{chr(10).join([f'  • {chat}' for chat in common_chats]) if common_chats else '  • لا توجد مجموعات مشتركة'}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 **عدد رسائل اليوم:** {len(user_messages[user_id])}
"""
    
    # إرسال المعلومات
    await event.reply(info_card)
    await asyncio.sleep(1.5)
    
    # ========== إرسال الرد + الصورة ==========
    if username == "Yaharp" or first_name == "Yaharp":
        reply_text = """🌹✨ **مرحباً حجي فرات العراقي** ✨🌹

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📨 تم تسليم رسالتك بنجاح
⏳ سيتم الرد عليك لاحقاً
💚 نشكرك على التواصل معنا
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 _تحيات فريق الدعم_ 🌸"""
        await event.reply(reply_text)
        await asyncio.sleep(0.5)
        await event.reply(file=SPECIAL_GIF)
        print(f"🎖️ رد خاص لـ {first_name} مع صورة مميزة")
    
    else:
        # ردود عشوائية متنوعة
        random_replies = [
            "😊✨ شكراً لتواصلك! سنرد عليك قريباً ✨😊",
            "🌸 مرحباً! رسالتك وصلت، نشكرك على صبرك 🌸",
            "💫 أهلاً بك! الحساب مشغول حالياً، سيتم الرد لاحقاً 💫",
            "🍃 تم استلام رسالتك، شكراً لتواصلك معنا 🍃",
            "⭐ رسالتك بأمان، سنعود إليك في أقرب وقت ⭐",
        ]
        reply_text = random.choice(random_replies)
        random_gif = random.choice(ANIME_GIFS)
        await event.reply(reply_text)
        await asyncio.sleep(0.5)
        await event.reply(file=random_gif)
        print(f"✅ رد عام لـ {first_name} مع صورة متحركة")

@client.on(events.NewMessage(outgoing=True))
async def my_message_handler(event):
    """تتبع رسائلك أنت لمنع الرد أثناء المحادثة"""
    if not event.is_private:
        return
    talking_with[event.chat_id] = time.time()

async def main():
    await client.start()
    me = await client.get_me()
    print("=" * 55)
    print("💀 **المطور المدمر - النسخة الكاملة** 💀")
    print(f"👤 الحساب: {me.first_name} (@{me.username})")
    print(f"🖼️ صور متحركة: {len(ANIME_GIFS)} صورة")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print("=" * 55)
    await client.run_until_disconnected()

asyncio.run(main())
