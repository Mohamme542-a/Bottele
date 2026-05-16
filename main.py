# ===================================================================
# 💀 CYBER AI ENGINE - النسخة النهائية المتكاملة 💀
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
# ✅ بياناتك - كلها مضبوطة
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"

SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="

OWNER_ID = 8676210788
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

# ===================================================================
# ⚙️ إعدادات سريعة
# ===================================================================

MAX_MESSAGES = 8
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
REPLY_DELAY = 0.5  # نصف ثانية فقط
TALKING_TIMEOUT = 3600

# ===================================================================
# 🧠 ردود طبيعية (بدون كلمات سايبر)
# ===================================================================

NATURAL_REPLIES = [
    "مرحباً! شكراً لتواصلك 🌸",
    "أهلاً بك، رسالتك وصلت ✅",
    "شكراً لك، سأرد عليك قريباً 💫",
    "مرحباً! كيف أستطيع مساعدتك؟ 😊",
    "تم استلام رسالتك، شكراً جزيلاً 🌹",
    "أهلاً وسهلاً، رسالتك بأمان 💙",
    "شكراً لتواصلك معنا ✨",
    "مرحباً! أنا هنا من أجلك 🌟",
]

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
                    self.users = data.get("users", {})
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

data_manager = DataManager()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# تخزين مؤقت
user_timestamps = defaultdict(list)
talking_mode = {}

# ===================================================================
# 🔍 دوال جلب المعلومات كاملة
# ===================================================================

async def get_full_user_info(user_id):
    """جلب جميع معلومات الحساب"""
    try:
        full = await client(GetFullUserRequest(user_id))
        user = full.user
        
        # الأسماء السابقة (إذا موجودة)
        old_names = []
        if hasattr(user, "usernames"):
            old_names = [u.username for u in user.usernames if u.username != user.username]
        
        return {
            "first_name": user.first_name or "غير معروف",
            "last_name": user.last_name or "",
            "username": user.username or "لا يوجد",
            "user_id": user.id,
            "phone": user.phone or "غير مرئي",
            "premium": "✅ نعم" if getattr(user, "premium", False) else "❌ لا",
            "bot": "✅ نعم" if user.bot else "❌ لا",
            "verified": "✅ نعم" if getattr(user, "verified", False) else "❌ لا",
            "scam": "⚠️ نعم" if getattr(user, "scam", False) else "✅ لا",
            "fake": "⚠️ نعم" if getattr(user, "fake", False) else "✅ لا",
            "about": full.about or "لا يوجد",
            "old_usernames": old_names,
            "common_chats_count": full.common_chats_count or 0
        }
    except Exception as e:
        print(f"خطأ في جلب المعلومات: {e}")
        return None

async def get_common_groups(user_id):
    """جلب المجموعات المشتركة"""
    common = []
    try:
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                try:
                    await client(GetParticipantRequest(dialog.entity, user_id))
                    common.append(dialog.name)
                    if len(common) >= 5:
                        break
                except:
                    continue
    except:
        pass
    return common

# ===================================================================
# 📊 بناء بطاقة المعلومات
# ===================================================================

def build_info_card(info, groups):
    """بناء بطاقة معلومات كاملة"""
    
    if not info:
        return None
    
    # الأسماء القديمة
    old_names_text = ""
    if info.get("old_usernames"):
        old_names_text = "\n".join([f"  • @{n}" for n in info["old_usernames"][:3]])
    else:
        old_names_text = "  • لا يوجد"
    
    # المجموعات المشتركة
    groups_text = ""
    if groups:
        groups_text = "\n".join([f"  • {g[:30]}" for g in groups[:5]])
    else:
        groups_text = "  • لا توجد مجموعات مشتركة"
    
    card = f"""
╔══════════════════════════════════════╗
📋 **【 معلومات الحساب 】**
╚══════════════════════════════════════╝

👤 **الاسم:** {info['first_name']} {info['last_name']}
🆔 **اسم المستخدم:** @{info['username']}
🔢 **المعرف (ID):** `{info['user_id']}`

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📞 **رقم الهاتف:** {info['phone']}
💎 **بريميوم:** {info['premium']}
🤖 **بوت:** {info['bot']}
✅ **موثق:** {info['verified']}
🚨 **مشبوه:** {info['scam']}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📜 **الأسماء السابقة:**
{old_names_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📢 **المجموعات المشتركة:**
{groups_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📝 **عن الحساب:**
{info['about'][:150]}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return card

# ===================================================================
# 🛡️ فحص السبام
# ===================================================================

async def check_spam(user_id):
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل الأساسي
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def message_handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    user_name = sender.first_name or "مجهول"
    text = event.raw_text or ""
    
    # المالك
    if user_id == OWNER_ID:
        return
    
    # وضع المحادثة
    if user_id in talking_mode and time.time() - talking_mode[user_id] < TALKING_TIMEOUT:
        return
    
    # محظور
    if user_id in data_manager.blocked_users:
        await event.reply("🚫 عذراً، تم حظرك من هذا الحساب.")
        return
    
    # فحص السبام
    msg_count = await check_spam(user_id)
    
    if msg_count == WARNING_LIMIT:
        await event.reply("⚠️ **تنبيه**: إرسال سريع جداً، رجاءً تمهل قليلاً.")
        return
    
    if msg_count >= MAX_MESSAGES:
        data_manager.blocked_users.add(user_id)
        data_manager.save_data()
        await event.reply(f"🚫 **تم حظرك تلقائياً** (أرسلت {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية)")
        return
    
    # جلب المعلومات كاملة
    user_info = await get_full_user_info(user_id)
    common_groups = await get_common_groups(user_id)
    
    # إرسال بطاقة المعلومات
    if user_info:
        card = build_info_card(user_info, common_groups)
        if card:
            await event.reply(card)
            await asyncio.sleep(0.5)
    
    # الرد الطبيعي
    await asyncio.sleep(REPLY_DELAY)
    reply = random.choice(NATURAL_REPLIES)
    await event.reply(reply)
    
    # إرسال الصورة
    try:
        await event.reply(file=DEFAULT_IMAGE)
    except:
        pass
    
    # حفظ الإحصائيات
    user_key = str(user_id)
    if user_key not in data_manager.users:
        data_manager.users[user_key] = {"messages": 0, "name": user_name}
    data_manager.users[user_key]["messages"] += 1
    data_manager.users[user_key]["last_seen"] = datetime.now().isoformat()
    data_manager.save_data()
    
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

async def health_check(request):
    return web.Response(
        text=f"✅ النظام يعمل\n👥 المستخدمين: {len(data_manager.users)}\n🚫 المحظورين: {len(data_manager.blocked_users)}\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        content_type="text/plain"
    )

async def dashboard(request):
    users_list = ""
    for uid, udata in list(data_manager.users.items())[-30:]:
        users_list += f"<tr><td>{udata.get('name', 'مجهول')}</td><td>{udata.get('messages', 0)}</td><td>{udata.get('last_seen', '-')[:16]}</td></tr>"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة التحكم</title>
    <style>body{{background:#0a0a0a;color:#fff;font-family:system-ui;padding:20px;}}
    .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:30px;}}
    .card{{background:#1a1a2e;padding:20px;border-radius:15px;text-align:center;}}
    .number{{font-size:2em;color:#00ffff;}}
    table{{width:100%;border-collapse:collapse;}}
    th,td{{padding:10px;text-align:right;border-bottom:1px solid #333;}}
    th{{color:#00ffff;}}
    .status{{color:#00ff00;}}</style>
    </head>
    <body>
        <h1>💀 لوحة التحكم</h1>
        <div class="stats">
            <div class="card"><div class="number">{len(data_manager.users)}</div><div>المستخدمين</div></div>
            <div class="card"><div class="number">{len(data_manager.blocked_users)}</div><div>المحظورين</div></div>
            <div class="card"><div class="number">{sum(u.get('messages',0) for u in data_manager.users.values())}</div><div>الرسائل</div></div>
        </div>
        <div class="card">
            <h3>📋 المستخدمين</h3>
            <table><thead><tr><th>الاسم</th><th>الرسائل</th><th>آخر ظهور</th></tr></thead>
            <tbody>{users_list if users_list else '<tr><td colspan="3">لا يوجد</td></tr>'}</tbody>
            </table>
        </div>
        <div class="status">🟢 النظام يعمل 24/7</div>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def start_web():
    app = web.Application()
    app.router.add_get('/', dashboard)
    app.router.add_get('/dashboard', dashboard)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ خادم الويب شغال على المنفذ 8080")

# ===================================================================
# 🚀 التشغيل
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 النظام شغال - النسخة المتكاملة 💀")
    print("=" * 60)
    
    await client.start()
    me = await client.get_me()
    
    asyncio.create_task(start_web())
    
    print(f"✅ الحساب: {me.first_name}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print(f"⚡ سرعة الرد: {REPLY_DELAY} ثانية")
    print(f"🌐 لوحة التحكم: http://localhost:8080")
    print("=" * 60)
    print("💀 جاهز! 💀")
    print("=" * 60)
    
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
