import asyncio
import time
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import BlockRequest
from datetime import datetime

# ==================== بياناتك ====================
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="

# ==================== إعدادات الحظر ====================
MAX_MESSAGES = 5      # 5 رسائل = حظر
WARNING_LIMIT = 3     # 3 رسائل = تحذير
COOLDOWN_SECONDS = 60 # خلال دقيقة كاملة (60 ثانية)

# ==================== ردود مخصصة ====================
# رد خاص لـ Yaharp
SPECIAL_REPLY = """🌹✨ **مرحباً حجي فرات العراقي** ✨🌹

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📨 **تم تسليم رسالتك بنجاح**
⏳ **سيتم الرد عليك لاحقاً**
💚 **نشكرك على التواصل معنا**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 _تحيات فريق الدعم_ 🌸"""

# الرد العام للناس
DEFAULT_REPLY = """😊✨ **عذراً صاحب الحساب مشغول حالياً** ✨😊

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📬 **تم استلام رسالتك**
⏰ **سيتم الرد عليك في أقرب فرصة**
💫 _نشكرك على تفهمك_

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 **مع تحيات إدارة TgAuto** 🌸"""

# ==================== تخزين البيانات ====================
user_messages = defaultdict(list)  # user_id -> list of timestamps
blocked_users = set()  # المستخدمين المحظورين محلياً

# ==================== دوال الحظر ====================
def check_spam(user_id):
    """ترجع (هل يعتبر سبام، عدد الرسائل خلال الفترة)"""
    now = time.time()
    recent = [ts for ts in user_messages[user_id] if now - ts < COOLDOWN_SECONDS]
    user_messages[user_id] = recent
    return len(recent) >= MAX_MESSAGES, len(recent)

def add_message(user_id):
    """تسجيل رسالة جديدة"""
    user_messages[user_id].append(time.time())

# ==================== الكود الرئيسي ====================
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    user_id = sender.id
    username = sender.username or "لا يوجد"
    first_name = sender.first_name or ""
    last_name = sender.last_name or ""
    phone = getattr(sender, 'phone', "غير مرئي")
    
    # ========== إذا كان الشخص محظور محلياً ==========
    if user_id in blocked_users:
        await event.reply("🚫 **أنت محظور من هذا البوت** 🚫\n\nلن تصلك أي ردود بعد الآن.")
        return
    
    # تسجيل الرسالة
    add_message(user_id)
    
    # التحقق من السبام
    is_spam, count = check_spam(user_id)
    
    # ========== تحذير عند 3 رسائل ==========
    if count == WARNING_LIMIT and not is_spam:
        warning_msg = f"""⚠️🧨 **تحذير من التكرار** 🧨⚠️

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📊 لقد أرسلت **{count} رسائل** خلال {COOLDOWN_SECONDS} ثانية

⚠️ إذا وصلت إلى **{MAX_MESSAGES} رسائل**، سيتم **حظرك تلقائياً من الحساب**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
😊 _رجاءً انتظر قليلاً قبل إرسال رسائل جديدة_"""
        await event.reply(warning_msg)
        print(f"⚠️ تحذير للمستخدم {first_name} (@{username}): {count} رسائل خلال {COOLDOWN_SECONDS} ثانية")
        return
    
    # ========== حظر عند 5 رسائل (حظر حقيقي من الحساب) ==========
    if is_spam:
        # حظر المستخدم من حساب التليجرام نفسه
        try:
            await client(BlockRequest(id=user_id))
            blocked_users.add(user_id)
            block_msg = f"""🔨🚫 **تم حظرك تلقائياً** 🚫🔨

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🚷 **سبب الحظر:** إرسال {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية

📌 **لن تصلك أي رسائل من هذا الحساب بعد الآن**
🔓 للفك، تواصل مع المشرف يدوياً

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
😔 _هذا الإجراء تلقائي لحماية الحساب_"""
            await event.reply(block_msg)
            print(f"🔨 تم حظر المستخدم {first_name} (@{username}) - ID: {user_id}")
        except Exception as e:
            print(f"❌ فشل حظر {user_id}: {e}")
        return
    
    # ========== كشف المعلومات للمستخدم (الجميع) ==========
    info_msg = f"""🕵️‍♂️ **معلومات رسالتك** 🕵️‍♂️

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
👤 **الاسم الأول:** {first_name}
👥 **الاسم الأخير:** {last_name}
🆔 **اسم المستخدم:** @{username}
🔢 **المعرف (ID):** `{user_id}`
📞 **رقم الهاتف:** {phone}
📅 **تاريخ الإرسال:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"""
    
    await event.reply(info_msg)
    
    # ========== الرد المناسب بعد كشف المعلومات ==========
    await asyncio.sleep(1.5)
    
    # رد خاص لـ Yaharp
    if username == "Yaharp" or first_name == "Yaharp" or user_id == 123456789:  # حط ايدي Yaharp إذا عندك
        await event.reply(SPECIAL_REPLY)
        print(f"🎖️ رد خاص لـ {first_name} (@{username})")
    else:
        await event.reply(DEFAULT_REPLY)
        print(f"✅ رد عام لـ {first_name} (@{username})")

async def main():
    await client.start()
    me = await client.get_me()
    print("=" * 50)
    print(f"💀 **المطور المدمر - شغال 100%** 💀")
    print(f"👤 الحساب: {me.first_name} (@{me.username})")
    print(f"⚙️ إعدادات الحظر: {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية")
    print(f"⚠️ تحذير عند {WARNING_LIMIT} رسائل")
    print(f"🔨 الحظر يكون من الحساب نفسه (Block API)")
    print("=" * 50)
    await client.run_until_disconnected()

asyncio.run(main())
