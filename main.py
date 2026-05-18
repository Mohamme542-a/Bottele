# ===================================================================
# 💀 CYBER AI ENGINE - EDITION EXTREME MAX PRO 💀
# ===================================================================
# تمت إضافة وظيفة جلب رقم الهاتف و الأسماء القديمة بكفاءة عالية
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
from telethon.tl.functions.contacts import ResolveUsernameRequest, GetContactsRequest
from telethon.errors import FloodWaitError
from aiohttp import web

# ===================================================================
# ✅ بياناتك - لا تلمسها
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="
OWNER_ID = 8676210788
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

SPECIAL_USERNAME = "Yaharp"   # اكتب اسم المستخدم الذي تريد رداً خاصاً له

SPECIAL_REPLY = f"""
🌹✨ **مرحباً حجي فرات العراقي** ✨🌹

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📨 تم تسليم رسالتك بنجاح
⏳ سيتم الرد عليك لاحقاً
💚 نشكرك على التواصل معنا
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 _تحيات فريق الدعم_ 🌸
"""

# ===================================================================
# ⚙️ إعدادات
# ===================================================================

MAX_MESSAGES = 8
WARNING_LIMIT = 4
COOLDOWN_SECONDS = 60
REPLY_DELAY = 0.5
TALKING_TIMEOUT = 3600

REPLIES = [
    "مرحباً! شكراً لتواصلك 🌸",
    "أهلاً بك، رسالتك وصلت ✅",
    "شكراً لك، سأرد عليك قريباً 💫",
    "تم استلام رسالتك، شكراً جزيلاً 🌹",
    "أهلاً وسهلاً، رسالتك بأمان 💙",
]

# ===================================================================
# إدارة البيانات
# ===================================================================

class DataManager:
    def __init__(self):
        self.users = {}
        self.blocked_users = set()
        self.contacts_phone_cache = {}
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
        except: pass
    def save_data(self):
        try:
            with open("users_data.json", "w", encoding="utf-8") as f:
                json.dump({"users": self.users}, f, ensure_ascii=False, indent=2)
            with open("blocked_users.json", "w") as f:
                json.dump(list(self.blocked_users), f)
        except: pass

data_manager = DataManager()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

user_timestamps = defaultdict(list)
talking_mode = {}

# ===================================================================
# 🔍 **وظائف لجلب كل ما تريد** (رقم الهاتف + الأسماء القديمة)
# ===================================================================

async def get_user_phone_and_old_names(user_id):
    """ترجع رقم الهاتف (مع ذكاء الحصول عليه) + الأسماء السابقة"""
    phone_number = "غير مرئي (الخصوصية)"
    old_usernames = []
    full_user = None

    # 1. محاولة جلب الرقم الأساسي
    try:
        full = await client(GetFullUserRequest(user_id))
        full_user = full
        if hasattr(full.user, 'phone') and full.user.phone:
            phone_number = full.user.phone
    except Exception:
        pass

    # 2. إذا الرقم مخفي، حاول استيراد المستخدم مؤقتاً إلى جهات الاتصال (مثل بوت Mjkjvnbot)
    if phone_number == "غير مرئي (الخصوصية)":
        try:
            # إضافة المستخدم كجهة اتصال مؤقتة لعل الرقم ينكشف
            await client.add_contact(user_id, first_name="Temp", last_name="User")
            # الانتظار قليلاً حتى تتم المزامنة
            await asyncio.sleep(1)
            # جلب كل جهات الاتصال للبحث عن الرقم
            contacts = await client(GetContactsRequest(hash=0))
            for user in contacts.users:
                if user.id == user_id:
                    if hasattr(user, 'phone') and user.phone:
                        phone_number = user.phone
                        break
            # مسح جهة الاتصال المؤقتة بعدها مباشرة
            await client.delete_contacts([user_id])
        except Exception:
            pass

    # 3. محاولة تحليل الأسماء السابقة من خاصية `usernames`
    if full_user and hasattr(full_user.user, 'usernames') and full_user.user.usernames:
        for un in full_user.user.usernames:
            if un.active and un.username != full_user.user.username:
                old_usernames.append(f"@{un.username}")
    else:
        # محاولة ثانية لجلب الأسماء السابقة إن وجدت
        try:
            user_entity = await client.get_entity(user_id)
            if hasattr(user_entity, 'usernames') and user_entity.usernames:
                for un in user_entity.usernames:
                    if un.active and un.username != user_entity.username:
                        old_usernames.append(f"@{un.username}")
        except Exception:
            pass

    return phone_number, old_usernames

# ===================================================================
# 🔍 دوال جلب المعلومات القديمة الكاملة
# ===================================================================

async def get_full_user_details(user_id):
    """ترجع قاموساً مفصلاً عن المستخدم (مع إظهار الأرقام المخفية)"""
    try:
        # معلومات الحساب الأساسية
        full = await client(GetFullUserRequest(user_id))
        user = full.user
        
        # المعلومة الخارقة: استدعاء الرقم والأسماء السابقة
        final_phone, old_names = await get_user_phone_and_old_names(user_id)
        
        # الأساسيات
        first_name = user.first_name or "غير معروف"
        last_name = user.last_name or ""
        username = f"@{user.username}" if user.username else "لا يوجد"
        user_id_val = user.id
        
        # الحالة
        premium = "✅ نعم" if getattr(user, "premium", False) else "❌ لا"
        is_bot = "✅ نعم" if user.bot else "❌ لا"
        verified = "✅ نعم" if getattr(user, "verified", False) else "❌ لا"
        scam = "⚠️ نعم" if getattr(user, "scam", False) else "✅ لا"
        fake = "⚠️ نعم" if getattr(user, "fake", False) else "✅ لا"
        contact = "✅ نعم" if getattr(user, "contact", False) else "❌ لا"
        mutual = "✅ نعم" if getattr(user, "mutual_contact", False) else "❌ لا"
        deleted = "⚠️ نعم" if getattr(user, "deleted", False) else "✅ لا"
        
        # صورة
        photos_count = 0
        try:
            photos = await client.get_profile_photos(user_id)
            photos_count = len(photos)
        except: pass
        
        # الأسماء السابقة
        old_names_text = "\n".join([f"  • {n}" for n in old_names[:5]]) if old_names else "  • لا يوجد"
        
        # المجموعات المشتركة
        common_groups = []
        try:
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    try:
                        await client(GetParticipantRequest(dialog.entity, user_id))
                        common_groups.append(dialog.name[:35])
                        if len(common_groups) >= 8:
                            break
                    except:
                        continue
        except: pass
        groups_text = "\n".join([f"  • {g}" for g in common_groups]) if common_groups else "  • لا توجد"
        
        # البايو
        about = full.about or "لا يوجد"
        
        # البطاقة النهائية (ستظهر الآن الرقم حتى لو مخفياً في بعض الحالات)
        card = f"""
╔══════════════════════════════════════════════╗
📋 **【 معلومات الحساب 】**
╚══════════════════════════════════════════════╝

👤 **الاسم:** {first_name} {last_name}
🆔 **اسم المستخدم:** {username}
🔢 **المعرف (ID):** `{user_id_val}`

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📞 **رقم الهاتف:** {final_phone}
🖼️ **عدد الصور:** {photos_count}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
💎 **بريميوم:** {premium}
🤖 **بوت:** {is_bot}
✅ **موثق:** {verified}
🚨 **مشبوه:** {scam}
🎭 **مزيف:** {fake}
📞 **جهة اتصال:** {contact}
🔄 **جهة اتصال متبادلة:** {mutual}
🗑️ **محذوف:** {deleted}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📜 **الأسماء السابقة:**
{old_names_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📢 **المجموعات المشتركة:**
{groups_text}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📝 **عن الحساب:**
{about[:200]}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return card
    except Exception as e:
        print(f"خطأ في جلب المعلومات: {e}")
        return None

# ===================================================================
# 🛡️ فحص السبام و باقي الوظائف الأساسية
# ===================================================================

async def check_spam(user_id):
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل الرئيسي
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    user_name = sender.first_name or sender.username or "مجهول"
    username = sender.username or ""
    text = event.raw_text or ""
    
    if user_id == OWNER_ID:
        return
    
    if user_id in talking_mode and time.time() - talking_mode[user_id] < TALKING_TIMEOUT:
        return
    
    if user_id in data_manager.blocked_users:
        await event.reply("🚫 أنت محظور من هذا الحساب.")
        return
    
    msg_count = await check_spam(user_id)
    if msg_count == WARNING_LIMIT:
        await event.reply("⚠️ تنبيه: إرسال سريع، رجاءً تمهل.")
        return
    if msg_count >= MAX_MESSAGES:
        data_manager.blocked_users.add(user_id)
        data_manager.save_data()
        await event.reply(f"🚫 تم حظرك (أرسلت {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية)")
        return
    
    # إرسال بطاقة المعلومات الكاملة (بها الرقم + الأسماء القديمة)
    info_card = await get_full_user_details(user_id)
    if info_card:
        await event.reply(info_card)
        await asyncio.sleep(0.5)
    
    # الرد المخصص لاسم المستخدم المطلوب
    if username == SPECIAL_USERNAME or user_name == SPECIAL_USERNAME:
        await event.reply(SPECIAL_REPLY)
        try:
            await event.reply(file=DEFAULT_IMAGE)
        except: pass
    else:
        await asyncio.sleep(REPLY_DELAY)
        reply = random.choice(REPLIES)
        await event.reply(reply)
        try:
            await event.reply(file=DEFAULT_IMAGE)
        except: pass
    
    # حفظ الإحصائيات
    uid_str = str(user_id)
    if uid_str not in data_manager.users:
        data_manager.users[uid_str] = {"messages": 0, "name": user_name}
    data_manager.users[uid_str]["messages"] += 1
    data_manager.users[uid_str]["last_seen"] = datetime.now().isoformat()
    data_manager.save_data()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_name} (@{username}): {text[:40]}")

@client.on(events.NewMessage(outgoing=True))
async def track_owner(event):
    if not event.is_private:
        return
    talking_mode[event.chat_id] = time.time()
    asyncio.create_task(clean_talking())

async def clean_talking():
    await asyncio.sleep(60)
    now = time.time()
    expired = [uid for uid, ts in talking_mode.items() if now - ts > 3600]
    for uid in expired:
        del talking_mode[uid]

# ===================================================================
# 🌐 خادم الويب (للبقاء 24/7)
# ===================================================================

async def health(request):
    return web.Response(text=f"✅ Online\nUsers: {len(data_manager.users)}\nBlocked: {len(data_manager.blocked_users)}")

async def dashboard(request):
    users_list = ""
    for uid, udata in list(data_manager.users.items())[-30:]:
        users_list += f"<tr><td>{udata.get('name','مجهول')}</td><td>{udata.get('messages',0)}</td><td>{udata.get('last_seen','-')[:16]}<td></tr>"
    html = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة التحكم</title>
    <style>
        body{{background:#0a0a0a;color:#fff;font-family:system-ui;padding:20px;}}
        .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:30px;}}
        .card{{background:#1a1a2e;padding:20px;border-radius:15px;text-align:center;}}
        .number{{font-size:2em;color:#00ffff;}}
        table{{width:100%;border-collapse:collapse;}}
        th,td{{padding:10px;text-align:right;border-bottom:1px solid #333;}}
        th{{color:#00ffff;}}
    </style>
    </head>
    <body>
        <h1>📊 سايبر أنجن - لوحة التحكم</h1>
        <div class="stats">
            <div class="card"><div class="number">{len(data_manager.users)}</div><div>المستخدمين</div></div>
            <div class="card"><div class="number">{len(data_manager.blocked_users)}</div><div>المحظورين</div></div>
            <div class="card"><div class="number">{sum(u.get('messages',0) for u in data_manager.users.values())}</div><div>الرسائل</div></div>
        </div>
        <div class="card">
            <h3>📋 آخر المستخدمين</h3>
            <div style="overflow-x: auto;">
                <table>
                    <thead><tr><th>الاسم</th><th>الرسائل</th><th>آخر ظهور</th></thead>
                    <tbody>{users_list if users_list else '<tr><td colspan="3">لا يوجد</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

async def start_web():
    app = web.Application()
    app.router.add_get('/', dashboard)
    app.router.add_get('/dashboard', dashboard)
    app.router.add_get('/health', health)
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
    print("💀 CYBER AI ENGINE - EXTREME MAX PRO 💀")
    print("🤖 تم تفعيل جلب أرقام الهواتف المخفية عبر جهات الاتصال المؤقتة والأسماء السابقة")
    print("=" * 60)
    await client.start()
    me = await client.get_me()
    asyncio.create_task(start_web())
    print(f"✅ الحساب: {me.first_name}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل = حظر")
    print(f"⚡ سرعة الرد: {REPLY_DELAY} ثانية")
    print(f"🎯 رد خاص لـ: {SPECIAL_USERNAME}")
    print("=" * 60)
    print("💀 النظام جاهز 24/7 💀")
    print("=" * 60)
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
