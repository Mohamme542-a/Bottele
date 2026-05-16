# =========================================
# ☠️ CYBER AI - النسخة الخرافية ☠️
# =========================================
# صُممت لتعمل 24/7 بدون نوم أبداً
# =========================================

import asyncio
import random
import time
import re
import os
import json
from datetime import datetime
from collections import defaultdict
import aiohttp
from aiohttp import web

import google.generativeai as genai
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import BlockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.errors import FloodWaitError

# =========================================
# ✅ بياناتك (كلها مضبوطة)
# =========================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="
OWNER_ID = 8676210788
BOT_TOKEN = "8287042088:AAEpixAz5SRHplVPMmKnJlA0l884-FF72DI"

# =========================================
# 🤖 إعدادات Gemini AI
# =========================================

GEMINI_API = "AIzaSyD7sV8wXyZq2r5x9cFgHjKlQwErTyUiOp"
genai.configure(api_key=GEMINI_API)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="""أنت ذكاء اصطناعي سيبراني. رد بشكل قوي واحترافي ومختصر. استخدم الإيموجيات المناسبة."""
)

# =========================================
# ⚙️ إعدادات الحماية
# =========================================

MAX_MESSAGES = 6
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
AI_ENABLED = True
TALKING_TIMEOUT = 3600  # ساعة

# =========================================
# 🗂️ تخزين البيانات
# =========================================

user_messages = defaultdict(list)
blocked_users = set()
known_users = {}
talking_with = {}
user_names_history = defaultdict(set)

# =========================================
# 🖼️ صور متحركة (GIF)
# =========================================

CYBER_GIFS = [
    "https://media.tenor.com/mVv9yvKvX2sAAAAC/anime-peace.gif",
    "https://media.tenor.com/-hxP9V3x6zMAAAAC/anime-welcome.gif",
    "https://media.tenor.com/x8v1XHfZ9bQAAAAC/anime-thank-you.gif",
    "https://media.tenor.com/RfyX7xVqZ8YAAAAC/anime-respect.gif",
]

# =========================================
# 🚀 تشغيل العميل
# =========================================

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# =========================================
# 🔍 دوال التحليل
# =========================================

def analyze_mood(text):
    text = text.lower()
    happy = ["شكرا", "حب", "رائع", "جميل", "❤️"]
    angry = ["غبي", "زفت", "اكره", "😡", "🤬"]
    h = sum(1 for w in happy if w in text)
    a = sum(1 for w in angry if w in text)
    if h > a:
        return "😊 هادئ", "🟢"
    elif a > h:
        return "😠 غاضب", "🔴"
    return "😐 عادي", "🟡"

def detect_links(text):
    urls = re.findall(r'(https?://[^\s]+|t\.me/[^\s]+)', text)
    dangerous = ["t.me/+", "bit.ly", "grabify"]
    for url in urls:
        for d in dangerous:
            if d in url:
                return urls, True
    return urls, False

# =========================================
# 📂 جلب المجموعات المشتركة والأسماء القديمة
# =========================================

async def get_common_chats(user_id):
    common = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    await client(GetParticipantRequest(dialog.entity, user_id))
                    common.append(dialog.name)
                except:
                    continue
    except:
        pass
    return common[:5]

async def get_name_history(user_id):
    try:
        full = await client(GetFullUserRequest(user_id))
        user = full.user
        names = set()
        if user.first_name:
            names.add(user.first_name)
        if user.username:
            names.add(f"@{user.username}")
        return list(names)
    except:
        return []

# =========================================
# 🧠 الذكاء الاصطناعي
# =========================================

async def generate_ai_reply(user_name, text):
    try:
        response = model.generate_content(f"الاسم: {user_name}\nالرسالة: {text}\nرد بشكل سيبراني مختصر:")
        return response.text[:300]
    except:
        return random.choice(["☠️ تم رصدك.", "💀 سايبر يعرف كل شيء.", "🔪 لا تحاول."])

# =========================================
# 📊 البطاقة السيبرانية
# =========================================

async def build_cyber_card(sender, mood, mood_icon, links, danger):
    old_names = await get_name_history(sender.id)
    common_chats = await get_common_chats(sender.id)
    premium = "✅" if getattr(sender, "premium", False) else "❌"
    
    card = f"""
╔══════════════════════════╗
☠️ **سايبر سكان v4.0** ☠️
╚══════════════════════════╝

👤 **{sender.first_name or 'مجهول'}** @{sender.username or 'لايوجد'}
🆔 **ID:** `{sender.id}`
💎 **بريميوم:** {premium}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📜 **الأسماء السابقة:**
{chr(10).join([f'• {n}' for n in old_names[:3]]) if old_names else '• لا توجد'}

🧠 **المزاج:** {mood} {mood_icon}
🔗 **روابط خطرة:** {'⚠️ نعم' if danger else '✅ لا'}
📢 **مجموعات مشتركة:** {len(common_chats)}

🕒 **التاريخ:** {datetime.now().strftime('%H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━
☠️ _سايبر للحماية_ ☠️
"""
    return card

# =========================================
# 🛡️ مكافحة السبام
# =========================================

async def anti_spam(event, user_id):
    now = time.time()
    user_messages[user_id] = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
    user_messages[user_id].append(now)
    count = len(user_messages[user_id])
    
    if count == WARNING_LIMIT:
        await event.reply("⚠️ **تحذير سايبر** ⚠️\nتم رصد نشاط سريع...")
        
    if count >= MAX_MESSAGES:
        try:
            await client(BlockRequest(user_id))
            blocked_users.add(user_id)
            await event.reply("🔨 **تم تفعيل الحظر السيبراني** 🔨")
            return True
        except:
            pass
    return False

# =========================================
# 📩 استقبال الرسائل
# =========================================

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    
    if user_id == OWNER_ID:
        return
    
    if user_id in talking_with and time.time() - talking_with[user_id] < TALKING_TIMEOUT:
        return
    
    if user_id in blocked_users:
        return
    
    text = event.raw_text or ""
    
    spammed = await anti_spam(event, user_id)
    if spammed:
        return
    
    mood, mood_icon = analyze_mood(text)
    links, danger = detect_links(text)
    
    card = await build_cyber_card(sender, mood, mood_icon, links, danger)
    await event.reply(card)
    await asyncio.sleep(1)
    
    if random.random() > 0.5:
        try:
            await event.reply(file=random.choice(CYBER_GIFS))
        except:
            pass
    
    await asyncio.sleep(1)
    
    if AI_ENABLED:
        ai_reply = await generate_ai_reply(sender.first_name or "مجهول", text)
        await event.reply(f"☠️ **سايبر:** {ai_reply}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {sender.first_name}: {text[:40]}")

# =========================================
# 📤 تتبع رسائلك (وضع المحادثة)
# =========================================

@client.on(events.NewMessage(outgoing=True))
async def track_my_messages(event):
    if not event.is_private:
        return
    talking_with[event.chat_id] = time.time()

# =========================================
# 🌐 الجزء الخرافي: خادم الويب + النبض الذاتي
# =========================================

# متغير لتخزين الرابط الخارجي
EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://tgauto-worker.onrender.com")

# صفحة الصحة - يطلبها UptimeRobot من الخارج
async def health_page(request):
    return web.Response(
        text=f"""☠️ **سايبر سيستم - شغال 24/7** ☠️
━━━━━━━━━━━━━━━━━━━━━━
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👥 المستخدمين: {len(known_users)}
🚫 المحظورين: {len(blocked_users)}
🤖 الذكاء الاصطناعي: {'ON' if AI_ENABLED else 'OFF'}
━━━━━━━━━━━━━━━━━━━━━━
✅ البوت يعمل بكفاءة عالية
✅ رابط الصحة يعمل بشكل ممتاز
☠️ سايبر في خدمتك
""",
        content_type="text/plain",
        status=200
    )

# صفحة رئيسية للموقع
async def index_page(request):
    return web.Response(
        text=f"""<!DOCTYPE html>
<html>
<head><title>سايبر سيستم</title></head>
<body style="background:#0f0f0f;color:#0f0;font-family:monospace;text-align:center;padding:50px;">
<h1>☠️ سايبر سيستم ☠️</h1>
<p>البوت شغال 24/7 بدون توقف</p>
<p>الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>المستخدمين: {len(known_users)} | المحظورين: {len(blocked_users)}</p>
<hr>
<p><a href="/health">/health</a> - لفحص حالة البوت</p>
<p><a href="/stats">/stats</a> - للإحصائيات</p>
</body>
</html>""",
        content_type="text/html"
    )

# صفحة الإحصائيات
async def stats_page(request):
    return web.json_response({
        "status": "online",
        "uptime_seconds": int(time.time() - start_time) if 'start_time' in globals() else 0,
        "users_count": len(known_users),
        "blocked_count": len(blocked_users),
        "ai_enabled": AI_ENABLED,
        "timestamp": str(datetime.now())
    })

# الدالة الخرافية: تنبيه ذاتي داخلي + خارجي
async def self_ping():
    """يطلب البوت من نفسه كل 4 دقائق عشان ما ينام"""
    global start_time
    start_time = time.time()
    
    while True:
        await asyncio.sleep(240)  # 4 دقائق (أسرع من UptimeRobot)
        try:
            # نبض داخلي ذاتي
            async with aiohttp.ClientSession() as session:
                # اطلب من نفسك داخلياً
                await session.get('http://localhost:8080/health', timeout=5)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ نبض داخلي ذاتي ناجح")
                
                # إذا عندك رابط خارجي، اطلبه أيضاً (تأكيد مزدوج)
                if EXTERNAL_URL and "onrender.com" in EXTERNAL_URL:
                    await session.get(f'{EXTERNAL_URL}/health', timeout=5)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ نبض خارجي ذاتي ناجح")
                    
        except Exception as e:
            print(f"⚠️ فشل النبض الذاتي: {e}")

# تشغيل خادم الويب
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', index_page)
    app.router.add_get('/health', health_page)
    app.router.add_get('/stats', stats_page)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ خادم الويب شغال على المنفذ 8080")
    print(f"🌐 رابط الصحة: http://localhost:8080/health")
    print(f"📊 رابط الإحصائيات: http://localhost:8080/stats")

# =========================================
# ⚙️ أوامر التحكم
# =========================================

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.(ai|stats|block|unblock|ping)'))
async def control_commands(event):
    global AI_ENABLED
    cmd = event.raw_text.lower()
    
    if cmd == ".ai off":
        AI_ENABLED = False
        await event.edit("❌ تم تعطيل الذكاء الاصطناعي")
    elif cmd == ".ai on":
        AI_ENABLED = True
        await event.edit("✅ تم تشغيل الذكاء الاصطناعي")
    elif cmd == ".stats":
        await event.edit(f"""
☠️ **إحصائيات سايبر** ☠️

👥 المستخدمين: {len(known_users)}
🚫 المحظورين: {len(blocked_users)}
🤖 AI: {'ON' if AI_ENABLED else 'OFF'}
💬 محادثات نشطة: {len(talking_with)}
━━━━━━━━━━━━━━━━━━━━━━
🌐 الرابط: {EXTERNAL_URL}/health
☠️ الحالة: شغال 24/7
""")
    elif cmd == ".ping":
        await event.edit("🏓 **بونغ! سايبر شغال 100%**")

# =========================================
# 🚀 التشغيل النهائي الخرافي
# =========================================

async def main():
    # تشغيل البوت
    await client.start()
    me = await client.get_me()
    
    # تشغيل خادم الويب (للرابط الخارجي)
    asyncio.create_task(start_web_server())
    
    # تشغيل النبض الذاتي (عشان ما ينام)
    asyncio.create_task(self_ping())
    
    print("=" * 55)
    print("☠️ **سايبر سيستم - النسخة الخرافية** ☠️")
    print(f"👤 الحساب: {me.first_name} (@{me.username})")
    print(f"🆔 الايدي: {me.id}")
    print(f"🤖 AI: {'ON' if AI_ENABLED else 'OFF'}")
    print(f"🖼️ صور متحركة: {len(CYBER_GIFS)}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print("=" * 55)
    print("🌐 الروابط الشغالة:")
    print(f"   - http://localhost:8080/")
    print(f"   - http://localhost:8080/health")
    print(f"   - http://localhost:8080/stats")
    print("=" * 55)
    print("☠️ **نبض ذاتي داخلي + خارجي شغال** ☠️")
    print("💀 البوت لن ينام أبداً 💀")
    print("=" * 55)
    
    await client.run_until_disconnected()

# =========================================
asyncio.run(main())
