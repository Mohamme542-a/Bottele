# ===================================================================
# 💀 CYBER AI ENGINE - النسخة النهائية الكاملة 💀
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
from aiohttp import web

# ===================================================================
# ✅ بياناتك - كلها مضبوطة
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"

SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="

OWNER_ID = 8676210788
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

# ===================================================================
# ⚙️ إعدادات النظام
# ===================================================================

MAX_MESSAGES = 8
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
REPLY_DELAY = 2
TALKING_TIMEOUT = 3600

# ===================================================================
# 🗂️ تخزين البيانات
# ===================================================================

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
                        self.users[int(uid)] = udata
            if os.path.exists("blocked_users.json"):
                with open("blocked_users.json", "r") as f:
                    self.blocked_users = set(json.load(f))
        except:
            pass
    
    def save_data(self):
        try:
            with open("users_data.json", "w", encoding="utf-8") as f:
                json.dump({"users": self.users}, f, ensure_ascii=False, indent=2)
            with open("blocked_users.json", "w") as f:
                json.dump(list(self.blocked_users), f)
        except:
            pass
    
    def get_user(self, user_id):
        return self.users.get(str(user_id), {})
    
    def save_user(self, user_id, data):
        self.users[str(user_id)] = data
        self.save_data()

data_manager = DataManager()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# تخزين مؤقت
user_timestamps = defaultdict(list)
talking_mode = {}

# ردود متنوعة
REPLIES = [
    "مرحباً! شكراً لتواصلك، سأرد عليك قريباً.",
    "أهلاً بك، تم استلام رسالتك بنجاح.",
    "شكراً لك، سأتأكد من رسالتك في أقرب وقت.",
    "مرحباً! كيف يمكنني مساعدتك اليوم؟",
    "تم استلام رسالتك، شكراً على تواصلك.",
    "أهلاً وسهلاً، رسالتك وصلت.",
    "شكراً لتواصلك، سأعود إليك قريباً.",
]

# ===================================================================
# 🔍 دوال جلب المعلومات
# ===================================================================

async def get_user_info(user_id):
    """جلب معلومات كاملة عن المستخدم"""
    try:
        full = await client(GetFullUserRequest(user_id))
        user = full.user
        return {
            "first_name": user.first_name or "لا يوجد",
            "last_name": user.last_name or "",
            "username": user.username or "لا يوجد",
            "phone": user.phone or "غير مرئي",
            "premium": getattr(user, "premium", False),
            "bot": user.bot or False,
            "about": full.about or "لا يوجد",
        }
    except:
        return None

async def get_common_chats(user_id):
    """جلب المجموعات المشتركة"""
    common = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    await client.get_participants(dialog.entity, limit=1)
                    common.append(dialog.name)
                except:
                    continue
    except:
        pass
    return common[:5]

# ===================================================================
# 🛡️ دوال الحماية
# ===================================================================

async def check_spam(user_id):
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل - مع جلب المعلومات
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
        await event.reply("🚫 أنت محظور من هذا الحساب.")
        return
    
    # حفظ بيانات المستخدم
    user_data = data_manager.get_user(user_id)
    if not user_data:
        user_data = {"messages": 0, "first_seen": datetime.now().isoformat()}
    user_data["last_seen"] = datetime.now().isoformat()
    user_data["name"] = user_name
    user_data["username"] = username
    data_manager.save_user(user_id, user_data)
    
    # فحص السبام
    msg_count = await check_spam(user_id)
    
    if msg_count == WARNING_LIMIT:
        await event.reply("⚠️ **تنبيه**: إرسال سريع للرسائل، رجاءً تمهل.")
        return
    
    if msg_count >= MAX_MESSAGES:
        data_manager.blocked_users.add(user_id)
        data_manager.save_data()
        await event.reply(f"🚫 **تم حظرك تلقائياً** (أرسلت {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية)")
        return
    
    # ========== جلب المعلومات الكاملة ==========
    info = await get_user_info(user_id)
    common_chats = await get_common_chats(user_id)
    
    # بناء بطاقة المعلومات
    if info:
        info_card = f"""
╔══════════════════════════════╗
☠️ **معلومات المرسل** ☠️
╚══════════════════════════════╝

👤 **الاسم:** {info['first_name']} {info['last_name']}
🆔 **يوزرنيم:** @{info['username']}
🔢 **الايدي:** `{user_id}`
📞 **رقم الهاتف:** {info['phone']}
💎 **بريميوم:** {'✅' if info['premium'] else '❌'}
🤖 **بوت:** {'✅' if info['bot'] else '❌'}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📝 **عن الحساب:**
{info['about'][:100]}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📢 **مجموعات مشتركة:**
{chr(10).join([f'• {c}' for c in common_chats]) if common_chats else '• لا توجد'}

📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        await event.reply(info_card)
        await asyncio.sleep(1)
    
    # الرد العادي
    await asyncio.sleep(REPLY_DELAY)
    reply = random.choice(REPLIES)
    await event.reply(reply)
    
    # إرسال الصورة
    try:
        await event.reply(file=DEFAULT_IMAGE)
    except:
        pass
    
    # تحديث إحصائيات المستخدم
    user_data["messages"] = user_data.get("messages", 0) + 1
    data_manager.save_user(user_id, user_data)
    
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
# 🌐 خادم الويب (للمنفذ المطلوب)
# ===================================================================

async def health_check(request):
    """صفحة فحص الصحة - عشان المنفذ"""
    return web.Response(
        text=f"""✅ CYBER AI ENGINE ONLINE
━━━━━━━━━━━━━━━━━━━━━━
⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
👥 المستخدمين: {len(data_manager.users)}
🚫 المحظورين: {len(data_manager.blocked_users)}
💬 إجمالي الرسائل: {sum(u.get('messages', 0) for u in data_manager.users.values())}
━━━━━━━━━━━━━━━━━━━━━━
☠️ النظام يعمل بكفاءة 100%
""",
        content_type="text/plain",
        status=200
    )

async def dashboard(request):
    """لوحة تحكم بسيطة"""
    users_list = ""
    for uid, udata in list(data_manager.users.items())[-20:]:
        users_list += f"""
        <tr>
            <td>{udata.get('name', 'مجهول')} </td>
            <td>@{udata.get('username', '-')} </td>
            <td>{udata.get('messages', 0)} </td>
            <td>{udata.get('last_seen', '-')[:16]} </td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>💀 سايبر أنجن - لوحة التحكم</title>
        <style>
            body {{
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
                color: #e2e8f0;
                font-family: system-ui;
                padding: 20px;
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .header {{ text-align: center; padding: 30px; background: rgba(0,0,0,0.5); border-radius: 20px; margin-bottom: 30px; }}
            .header h1 {{ background: linear-gradient(135deg, #00ffff, #ff00ff); -webkit-background-clip: text; background-clip: text; color: transparent; }}
            .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
            .stat-card {{ background: rgba(30,30,50,0.9); padding: 20px; border-radius: 15px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #00ffff; }}
            .card {{ background: rgba(30,30,50,0.9); border-radius: 20px; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; text-align: right; border-bottom: 1px solid #334155; }}
            th {{ color: #00ffff; }}
            .status {{ display: inline-block; padding: 5px 15px; background: #00ff0044; color: #00ff00; border-radius: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💀 سايبر أنجن - Cyber Engine 💀</h1>
                <div class="status">🟢 النظام يعمل 24/7</div>
            </div>
            
            <div class="stats">
                <div class="stat-card"><div class="stat-number">{len(data_manager.users)}</div><div>👥 المستخدمين</div></div>
                <div class="stat-card"><div class="stat-number">{len(data_manager.blocked_users)}</div><div>🚫 المحظورين</div></div>
                <div class="stat-card"><div class="stat-number">{sum(u.get('messages', 0) for u in data_manager.users.values())}</div><div>💬 الرسائل</div></div>
                <div class="stat-card"><div class="stat-number">{len(talking_mode)}</div><div>🗣️ محادثات نشطة</div></div>
            </div>
            
            <div class="card">
                <h3>📋 آخر المستخدمين</h3>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>الاسم</th><th>يوزرنيم</th><th>الرسائل</th><th>آخر ظهور</th></tr></thead>
                        <tbody>{users_list if users_list else '<tr><td colspan="4">لا يوجد مستخدمين بعد</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
            
            <div style="text-align: center; padding: 30px; color: #64748b;">
                <p>💀 سايبر أنجن - نظام حماية وردود ذكية 💀</p>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def start_web_server():
    """تشغيل خادم الويب على المنفذ 8080"""
    app = web.Application()
    app.router.add_get('/', dashboard)
    app.router.add_get('/dashboard', dashboard)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ خادم الويب شغال على المنفذ 8080")
    print("🌐 لوحة التحكم: http://localhost:8080/dashboard")

# ===================================================================
# 🚀 التشغيل الرئيسي
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 سايبر أنجن - النسخة النهائية الكاملة 💀")
    print("=" * 60)
    
    await client.start()
    me = await client.get_me()
    
    # تشغيل خادم الويب
    asyncio.create_task(start_web_server())
    
    print(f"✅ الحساب: {me.first_name} (@{me.username})")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print(f"🌐 المنفذ: 8080")
    print("=" * 60)
    print("💀 النظام جاهز 24/7 💀")
    print("=" * 60)
    
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
