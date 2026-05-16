# ===================================================================
# 💀 CYBER AI ENGINE - الأسطوري المصحح 💀
# ===================================================================

import asyncio
import random
import time
import re
import os
import json
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

# ===================================================================
# المكتبات الأساسية - كلها صحيحة الآن
# ===================================================================

import aiohttp
from aiohttp import web
import google.generativeai as genai  # ✅ صححت الكتابة
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import FloodWaitError

# ===================================================================
# ✅ بياناتك الشخصية
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="
OWNER_ID = 8676210788

# مفتاح Gemini API (جديد)
GEMINI_API = "AIzaSyCXSXEcYN0aO0o3fgCqIIt9u238_sKyA80"

# الصورة اللي تترسل مع كل رد
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

# ===================================================================
# ⚙️ إعدادات النظام
# ===================================================================

MAX_MESSAGES = 8
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
TALKING_TIMEOUT = 3600
REPLY_DELAY = 2
AUTO_BAN_ENABLED = True

# ===================================================================
# 🗂️ إدارة البيانات
# ===================================================================

class UserData:
    def __init__(self, user_id, first_name="", username=""):
        self.user_id = user_id
        self.first_name = first_name
        self.username = username
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.messages = []
        self.total_messages = 0
        self.status = "normal"
        self.rank = "عادي"
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "username": self.username,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_messages": self.total_messages,
            "status": self.status,
            "rank": self.rank,
            "messages": self.messages[-50:]
        }

class DataManager:
    def __init__(self):
        self.users = {}
        self.blocked_users = set()
        self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists("users_data.json"):
                with open("users_data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for uid, udata in data.get("users", {}).items():
                        uid_int = int(uid)
                        user = UserData(uid_int)
                        user.first_name = udata.get("first_name", "")
                        user.username = udata.get("username", "")
                        user.total_messages = udata.get("total_messages", 0)
                        user.status = udata.get("status", "normal")
                        user.rank = udata.get("rank", "عادي")
                        self.users[uid_int] = user
            if os.path.exists("blocked_users.json"):
                with open("blocked_users.json", "r") as f:
                    self.blocked_users = set(json.load(f))
            print("✅ تم تحميل البيانات")
        except Exception as e:
            print(f"⚠️ خطأ في التحميل: {e}")
    
    def save_data(self):
        try:
            users_dict = {str(uid): user.to_dict() for uid, user in self.users.items()}
            with open("users_data.json", "w", encoding="utf-8") as f:
                json.dump({"users": users_dict}, f, ensure_ascii=False, indent=2)
            with open("blocked_users.json", "w") as f:
                json.dump(list(self.blocked_users), f)
        except Exception as e:
            print(f"⚠️ خطأ في الحفظ: {e}")
    
    def get_or_create_user(self, user_id, first_name="", username=""):
        if user_id not in self.users:
            self.users[user_id] = UserData(user_id, first_name, username)
        else:
            user = self.users[user_id]
            if first_name:
                user.first_name = first_name
            if username:
                user.username = username
            user.last_seen = datetime.now()
        return self.users[user_id]
    
    def add_message(self, user_id, text, reply=""):
        if user_id in self.users:
            user = self.users[user_id]
            user.total_messages += 1
            user.messages.append({
                "text": text[:500],
                "reply": reply[:500],
                "time": datetime.now().isoformat()
            })
            if len(user.messages) > 100:
                user.messages = user.messages[-100:]
        self.save_data()

# ===================================================================
# 🧠 الذكاء الاصطناعي
# ===================================================================

class CyberAI:
    def __init__(self):
        genai.configure(api_key=GEMINI_API)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.9,
                "max_output_tokens": 300,
            }
        )
    
    async def generate_reply(self, text: str, user_name: str) -> str:
        prompt = f"""
[المهمة]: رد على رسالة المستخدم بشكل طبيعي ومختصر.

[اسم المستخدم]: {user_name}
[الرسالة]: {text}

[تعليمات]:
- كن طبيعياً كأنك بشر
- لا تقل "أنا سايبر" أو "ذكاء اصطناعي"
- لا تكرر نفس العبارات
- استخدم إيموجيات مناسبة

[الرد]:
"""
        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip()
            # تنظيف الرد من العبارات السيبرانية
            for phrase in ["سايبر", "سيبراني", "AI", "ذكاء اصطناعي"]:
                reply = reply.replace(phrase, "")
            if len(reply) > 300:
                reply = reply[:300]
            return reply
        except Exception as e:
            print(f"⚠️ AI خطأ: {e}")
            fallbacks = [
                "مرحباً! شكراً لتواصلك، سأرد عليك قريباً.",
                "أهلاً بك، تم استلام رسالتك بنجاح.",
                "شكراً لك، سأتأكد من رسالتك.",
            ]
            return random.choice(fallbacks)

# ===================================================================
# 🌐 لوحة التحكم
# ===================================================================

class Dashboard:
    def __init__(self, data_manager: DataManager):
        self.data = data_manager
        self.start_time = datetime.now()
    
    async def get_html(self) -> str:
        stats = {
            "users": len(self.data.users),
            "blocked": len(self.data.blocked_users),
            "messages": sum(u.total_messages for u in self.data.users.values()),
            "uptime": str(datetime.now() - self.start_time).split(".")[0]
        }
        
        users_table = ""
        for user in list(self.data.users.values())[:20]:
            users_table += f"""
            <tr>
                <td>{user.first_name or 'مجهول'} </td>
                <td>@{user.username or '-'}</td>
                <td>{user.total_messages}</td>
                <td>{user.rank}</td>
                <td>{user.last_seen.strftime('%H:%M') if user.last_seen else '-'}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>💀 سايبر أنجن - لوحة التحكم</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Cairo', system-ui;
                    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
                    color: #e2e8f0;
                    padding: 20px;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{
                    text-align: center;
                    padding: 30px;
                    background: rgba(0,0,0,0.5);
                    border-radius: 20px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    font-size: 2.5em;
                    background: linear-gradient(135deg, #00ffff, #ff00ff);
                    -webkit-background-clip: text;
                    background-clip: text;
                    color: transparent;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: rgba(30,30,50,0.9);
                    padding: 20px;
                    border-radius: 15px;
                    text-align: center;
                    border: 1px solid rgba(0,255,255,0.2);
                }}
                .stat-number {{ font-size: 2.5em; font-weight: bold; color: #00ffff; }}
                .stat-label {{ color: #94a3b8; margin-top: 10px; }}
                .card {{
                    background: rgba(30,30,50,0.9);
                    border-radius: 20px;
                    padding: 20px;
                    margin-bottom: 30px;
                }}
                .card-title {{
                    font-size: 1.5em;
                    margin-bottom: 20px;
                    color: #00ffff;
                    border-right: 3px solid #00ffff;
                    padding-right: 15px;
                }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: right; border-bottom: 1px solid #334155; }}
                th {{ color: #00ffff; }}
                .footer {{ text-align: center; padding: 30px; color: #64748b; }}
                .status-badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    background: #00ff0044;
                    color: #00ff00;
                    border-radius: 20px;
                    margin-top: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💀 سايبر أنجن | Cyber Engine 💀</h1>
                    <div class="status-badge">🟢 النظام يعمل</div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-number">{stats['users']}</div><div class="stat-label">👥 المستخدمين</div></div>
                    <div class="stat-card"><div class="stat-number">{stats['blocked']}</div><div class="stat-label">🚫 المحظورين</div></div>
                    <div class="stat-card"><div class="stat-number">{stats['messages']}</div><div class="stat-label">💬 الرسائل</div></div>
                    <div class="stat-card"><div class="stat-number">{stats['uptime']}</div><div class="stat-label">⏱️ وقت التشغيل</div></div>
                </div>
                
                <div class="card">
                    <div class="card-title">👥 المستخدمين</div>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead><tr><th>الاسم</th><th>اسم المستخدم</th><th>الرسائل</th><th>الرتبة</th><th>آخر ظهور</th></tr></thead>
                            <tbody>{users_table if users_table else '<tr><td colspan="5" style="text-align:center">لا يوجد مستخدمين</td></tr>'}</tbody>
                        </table>
                    </div>
                </div>
                
                <div class="footer">
                    <p>💀 سايبر أنجن - نظام حماية وردود ذكية 💀</p>
                    <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """

# ===================================================================
# 🚀 تشغيل النظام
# ===================================================================

data_manager = DataManager()
ai_system = CyberAI()
dashboard = Dashboard(data_manager)
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# تخزين مؤقت
user_timestamps = defaultdict(list)
talking_mode = {}

async def check_spam(user_id):
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    user_name = sender.first_name or "مجهول"
    username = sender.username or ""
    text = event.raw_text or ""
    
    if user_id == OWNER_ID:
        return
    
    if user_id in talking_mode and time.time() - talking_mode[user_id] < TALKING_TIMEOUT:
        return
    
    if user_id in data_manager.blocked_users:
        return
    
    data_manager.get_or_create_user(user_id, user_name, username)
    
    msg_count = await check_spam(user_id)
    
    if msg_count == WARNING_LIMIT:
        await event.reply("⚠️ تنبيه: إرسال سريع للرسائل، رجاءً تمهل.")
        data_manager.add_message(user_id, text, "تحذير")
        return
    
    if msg_count >= MAX_MESSAGES and AUTO_BAN_ENABLED:
        data_manager.blocked_users.add(user_id)
        await event.reply("🚫 تم حظرك تلقائياً.")
        data_manager.add_message(user_id, text, "حظر")
        data_manager.save_data()
        return
    
    await asyncio.sleep(REPLY_DELAY)
    
    # توليد رد بالذكاء الاصطناعي
    ai_reply = await ai_system.generate_reply(text, user_name)
    await event.reply(ai_reply)
    
    # إرسال الصورة
    try:
        await event.reply(file=DEFAULT_IMAGE)
    except Exception as e:
        print(f"⚠️ فشل إرسال الصورة: {e}")
    
    data_manager.add_message(user_id, text, ai_reply)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_name}: {text[:40]}")

# ===================================================================
# 📤 تتبع رسائل المالك
# ===================================================================

@client.on(events.NewMessage(outgoing=True))
async def track_owner(event):
    if not event.is_private:
        return
    talking_mode[event.chat_id] = time.time()

# ===================================================================
# 🌐 خادم الويب
# ===================================================================

async def web_handler(request):
    html = await dashboard.get_html()
    return web.Response(text=html, content_type="text/html")

async def health_check(request):
    return web.Response(
        text=f"✅ CYBER AI ONLINE\nUsers: {len(data_manager.users)}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        content_type="text/plain"
    )

async def start_web():
    app = web.Application()
    app.router.add_get('/', web_handler)
    app.router.add_get('/dashboard', web_handler)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ خادم الويب شغال على http://localhost:8080")

# ===================================================================
# 🔄 النبض الذاتي
# ===================================================================

async def self_ping():
    while True:
        await asyncio.sleep(240)
        try:
            async with aiohttp.ClientSession() as session:
                await session.get('http://localhost:8080/health', timeout=5)
                print(f"✅ نبض ذاتي - {datetime.now().strftime('%H:%M:%S')}")
        except:
            pass

# ===================================================================
# 🚀 التشغيل
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 سايبر أنجن - النسخة الأسطورية المصححة 💀")
    print("=" * 60)
    
    await client.start()
    me = await client.get_me()
    
    asyncio.create_task(start_web())
    asyncio.create_task(self_ping())
    
    print(f"✅ الحساب: {me.first_name} (@{me.username})")
    print(f"🧠 الذكاء الاصطناعي: Gemini 1.5 Flash")
    print(f"🖼️ الصورة: {DEFAULT_IMAGE}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print("=" * 60)
    print("🌐 لوحة التحكم: http://localhost:8080/dashboard")
    print("💀 النظام جاهز 24/7 💀")
    print("=" * 60)
    
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
