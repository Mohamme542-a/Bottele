# ===================================================================
# 💀 CYBER AI ENGINE - النسخة النهائية الأسطورية 💀
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

# ===================================================================
# ✅ بياناتك - كلها مضبوطة
# ===================================================================

API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"

# السيشن الجديد - مخصوص لـ Render فقط
SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="

OWNER_ID = 8676210788

# الصورة اللي تترسل مع كل رد
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

# ===================================================================
# ⚙️ إعدادات الحماية
# ===================================================================

MAX_MESSAGES = 8          # 8 رسائل = حظر
WARNING_LIMIT = 4         # 4 رسائل = تحذير
COOLDOWN_SECONDS = 60     # خلال 60 ثانية
REPLY_DELAY = 2           # تأخير الرد ثانيتين
TALKING_TIMEOUT = 3600    # ساعة (وضع المحادثة)

# ===================================================================
# 🗂️ تخزين البيانات
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
        
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "username": self.username,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_messages": self.total_messages,
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
            print(f"💾 تم حفظ البيانات - {len(self.users)} مستخدم")
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
# 🚀 تشغيل العميل
# ===================================================================

data_manager = DataManager()
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# تخزين مؤقت
user_timestamps = defaultdict(list)
talking_mode = {}

# ردود طبيعية ومتنوعة (بدون عبارات سايبر)
REPLIES = [
    "مرحباً! شكراً لتواصلك، سأرد عليك قريباً.",
    "أهلاً بك، تم استلام رسالتك بنجاح.",
    "شكراً لك، سأتأكد من رسالتك في أقرب وقت.",
    "مرحباً! كيف يمكنني مساعدتك اليوم؟",
    "تم استلام رسالتك، شكراً على تواصلك.",
    "أهلاً وسهلاً، رسالتك وصلت.",
    "شكراً لتواصلك، سأعود إليك قريباً.",
    "مرحباً! أنا هنا لمساعدتك.",
    "تم التسلم! شكراً لك.",
    "أهلاً بك، سأرد عليك خلال فترة قصيرة.",
]

# ===================================================================
# دوال الحماية
# ===================================================================

async def check_spam(user_id):
    """فحص السبام"""
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    return len(user_timestamps[user_id])

# ===================================================================
# 📩 معالج الرسائل الرئيسي
# ===================================================================

@client.on(events.NewMessage(incoming=True))
async def message_handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    user_name = sender.first_name or "مجهول"
    username = sender.username or ""
    text = event.raw_text or ""
    
    # تجاهل المالك
    if user_id == OWNER_ID:
        return
    
    # وضع المحادثة - إذا كنت ترد على هذا الشخص
    if user_id in talking_mode:
        if time.time() - talking_mode[user_id] < TALKING_TIMEOUT:
            print(f"⏸️ وضع المحادثة: تم تجاهل {user_name}")
            return
    
    # المستخدمين المحظورين
    if user_id in data_manager.blocked_users:
        await event.reply("🚫 أنت محظور من هذا الحساب.")
        return
    
    # حفظ أو تحديث بيانات المستخدم
    data_manager.get_or_create_user(user_id, user_name, username)
    
    # فحص السبام
    msg_count = await check_spam(user_id)
    
    if msg_count == WARNING_LIMIT:
        await event.reply("⚠️ **تنبيه**: إرسال سريع للرسائل، رجاءً تمهل قليلاً.")
        data_manager.add_message(user_id, text, "تحذير سبام")
        print(f"⚠️ تحذير لـ {user_name}: {msg_count} رسائل")
        return
    
    if msg_count >= MAX_MESSAGES:
        data_manager.blocked_users.add(user_id)
        data_manager.save_data()
        await event.reply(f"🚫 **تم حظرك تلقائياً** 🚫\n\nلقد تجاوزت الحد المسموح ({MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية).")
        data_manager.add_message(user_id, text, "حظر تلقائي")
        print(f"🔨 تم حظر {user_name}")
        return
    
    # تأخير الرد الطبيعي
    await asyncio.sleep(REPLY_DELAY)
    
    # اختيار رد عشوائي
    reply = random.choice(REPLIES)
    await event.reply(reply)
    
    # إرسال الصورة
    try:
        await event.reply(file=DEFAULT_IMAGE)
        print(f"🖼️ تم إرسال الصورة لـ {user_name}")
    except Exception as e:
        print(f"⚠️ فشل إرسال الصورة: {e}")
    
    # تسجيل الرسالة
    data_manager.add_message(user_id, text, reply)
    
    # طباعة في السجل
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_name}: {text[:50]}... -> {reply[:30]}...")

# ===================================================================
# 📤 تتبع رسائل المالك (وضع المحادثة)
# ===================================================================

@client.on(events.NewMessage(outgoing=True))
async def track_owner_messages(event):
    if not event.is_private:
        return
    # سجل أنك رديت على هذا الشخص
    talking_mode[event.chat_id] = time.time()
    print(f"📝 تم تسجيل محادثة مع {event.chat_id}")

# ===================================================================
# 🧹 تنظيف وضع المحادثة القديم
# ===================================================================

async def clean_talking_mode():
    """ينظف وضع المحادثة كل دقيقة"""
    while True:
        await asyncio.sleep(60)
        now = time.time()
        expired = [uid for uid, ts in talking_mode.items() if now - ts > TALKING_TIMEOUT]
        for uid in expired:
            del talking_mode[uid]
        if expired:
            print(f"🧹 تم تنظيف {len(expired)} محادثة منتهية")

# ===================================================================
# 📊 طباعة الإحصائيات
# ===================================================================

async def print_stats():
    """يطبع إحصائيات كل ساعة"""
    while True:
        await asyncio.sleep(3600)  # كل ساعة
        print("=" * 50)
        print(f"📊 إحصائيات:")
        print(f"   👥 المستخدمين: {len(data_manager.users)}")
        print(f"   🚫 المحظورين: {len(data_manager.blocked_users)}")
        print(f"   💬 إجمالي الرسائل: {sum(u.total_messages for u in data_manager.users.values())}")
        print(f"   🗣️ محادثات نشطة: {len(talking_mode)}")
        print("=" * 50)

# ===================================================================
# 🚀 التشغيل الرئيسي
# ===================================================================

async def main():
    print("=" * 60)
    print("💀 سايبر أنجن - النسخة الأسطورية النهائية 💀")
    print("=" * 60)
    
    # تشغيل البوت
    await client.start()
    me = await client.get_me()
    
    # تشغيل المهام الخلفية
    asyncio.create_task(clean_talking_mode())
    asyncio.create_task(print_stats())
    
    print(f"✅ الحساب: {me.first_name} (@{me.username})")
    print(f"🆔 الايدي: {me.id}")
    print(f"🖼️ الصورة: {DEFAULT_IMAGE}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية = حظر")
    print(f"⚠️ تحذير عند: {WARNING_LIMIT} رسائل")
    print(f"💬 وضع المحادثة: {TALKING_TIMEOUT // 60} دقيقة")
    print("=" * 60)
    print("💀 النظام جاهز للعمل 24/7 💀")
    print("=" * 60)
    
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
