import asyncio
import time
import random
import re
import json
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import BlockRequest, UnblockRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import User, Channel, Chat
from telethon.errors import (
    ChannelPrivateError, UserPrivacyRestrictedError,
    FloodWaitError, PeerFloodError, RPCError
)

# ═══════════════════════════════════════════════════════════
# 📁 إعدادات الملفات والتخزين
# ═══════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ملفات البيانات
BLOCKED_FILE = DATA_DIR / "blocked_users.json"
STATS_FILE = DATA_DIR / "stats.json"
CONFIG_FILE = DATA_DIR / "config.json"
MESSAGES_LOG = LOGS_DIR / f"messages_{datetime.now().strftime('%Y-%m-%d')}.log"

# ═══════════════════════════════════════════════════════════
# 🔐 بيانات الاعتماد (استخدم متغيرات البيئة في الإنتاج!)
# ═══════════════════════════════════════════════════════════
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1wBuxhhwQnpWNLtAbQdsr3vvh7UwGD2lYgmdU9madk89xTUCBU6nwnt_L9dtHZb2P74qdnbmauxCuvokcELLBsu7VVD_Pc6pIf8ZzyCn1zkzLSGyKswSLHPztHiNJrHpzd9Mt9tVoWEFn72uZzJHhuMthwn5LoInUos9-QRR6CUADMIGUS--PPOtVawFYoQxGqhoZ4VrTQ2Pe7a8nc4NRRgl07bMOQpMJ6r8oTRdvkMHaA51cxEDgVNY8tHZgt3X2G12-SDk6YGIV1v9otm1E-ucc1Vo5sqsF9yfoCA-RhnAg-lnf5hhEcfb02G7Sm62OL7frzp1PatsHg60fe0HkcvoEU="

# ═══════════════════════════════════════════════════════════
# 🎨 مكتبة الصور المتحركة
# ═══════════════════════════════════════════════════════════
ANIME_GIFS = [
    "https://media.tenor.com/mVv9yvKvX2sAAAAC/anime-peace.gif",
    "https://media.tenor.com/-hxP9V3x6zMAAAAC/anime-welcome.gif",
    "https://media.tenor.com/x8v1XHfZ9bQAAAAC/anime-thank-you.gif",
    "https://media.tenor.com/Jv7qR6P8c4sAAAAC/anime-smile.gif",
    "https://media.tenor.com/YZWhRGJTeZwAAAAC/anime-wave.gif",
    "https://media.tenor.com/X7n6E6E1s5sAAAAC/anime-happy.gif",
]

SPECIAL_GIF = "https://media.tenor.com/RfyX7xVqZ8YAAAAC/anime-respect.gif"

# ═══════════════════════════════════════════════════════════
# ⚙️ إعدادات الحماية المتقدمة
# ═══════════════════════════════════════════════════════════
class SecurityConfig:
    """إعدادات الأمان القابلة للتعديل"""
    MAX_MESSAGES = 5              # عدد الرسائل المسموح بها
    WARNING_LIMIT = 3             # التحذير عند هذا العدد
    COOLDOWN_SECONDS = 60         # فترة التبريد بالثواني
    TALKING_TIMEOUT = 3600        # مدة المحادثة (ساعة)
    DUPLICATE_TIMEOUT = 300       # فترة منع التكرار (5 دقائق)
    MAX_DAILY_MESSAGES = 50       # الحد الأقصى اليومي
    FLOOD_SLEEP = 2               # ثواني الانتظار بين الردود
    
    # قائمة الأصدقاء (لن يتم حظرهم)
    FRIENDS = []  # أضف المعرفات هنا: [123456789, ...]
    
    # الكلمات الممنوعة (محتوى غير مرغوب)
    BANNED_WORDS = [
        "اباحي", "سكس", "porn", "xxx", "sex", "نيك", "احتيال",
        "احمق", "غبي", "كلب", "حمار", "تافه"
    ]
    
    # الروابط الخطرة
    DANGEROUS_PATTERNS = [
        r"t\.me/joinchat", r"t\.me/\+", r"bit\.ly", r"goo\.gl",
        r"tinyurl", r"shortlink", r"free-money", r"crypto-giveaway"
    ]

# ═══════════════════════════════════════════════════════════
# 📊 أنظمة التخزين والتتبع
# ═══════════════════════════════════════════════════════════
class DataStore:
    """نظام تخزين مركزي مع دعم الحفظ على القرص"""
    
    def __init__(self):
        self.user_messages = defaultdict(list)      # رسائل المستخدمين
        self.blocked_users = self._load_json(BLOCKED_FILE, set())
        self.talking_with = {}                       # المحادثات النشطة
        self.user_names = defaultdict(set)          # أسماء المستخدمين
        self.daily_counts = defaultdict(int)         # عدد الرسائل اليومية
        self.last_reply = defaultdict(str)           # آخر رد لكل مستخدم
        self.reply_history = defaultdict(deque)      # تاريخ الردود
        self.spam_scores = defaultdict(int)          # نقاط السبام
        self.last_seen = {}                          # آخر ظهور
        
    def _load_json(self, path, default):
        """تحميل البيانات من ملف JSON"""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(default, set):
                        return set(data)
                    return data
            except:
                pass
        return default
    
    def _save_json(self, path, data):
        """حفظ البيانات في ملف JSON"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                if isinstance(data, set):
                    json.dump(list(data), f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ خطأ في الحفظ: {e}")
    
    def save_blocked(self):
        self._save_json(BLOCKED_FILE, self.blocked_users)
    
    def is_blocked(self, user_id):
        return user_id in self.blocked_users
    
    def block(self, user_id):
        self.blocked_users.add(user_id)
        self.save_blocked()
    
    def unblock(self, user_id):
        self.blocked_users.discard(user_id)
        self.save_blocked()

# إنشاء مخزن البيانات
store = DataStore()

# ═══════════════════════════════════════════════════════════
# 📝 نظام السجلات المتقدم
# ═══════════════════════════════════════════════════════════
class Logger:
    """نظام تسجيل احترافي"""
    
    @staticmethod
    def log_message(user_id, username, text, action="received"):
        """تسجيل رسالة"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{action}] User:{user_id} (@{username}): {text[:100]}\n"
        try:
            with open(MESSAGES_LOG, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    @staticmethod
    def log_event(event_type, details):
        """تسجيل حدث"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"📋 [{timestamp}] {event_type}: {details}")

# ═══════════════════════════════════════════════════════════
# 🧠 محلل المحتوى الذكي
# ═══════════════════════════════════════════════════════════
class ContentAnalyzer:
    """تحليل المحتوى والمزاج والتهديدات"""
    
    MOOD_PATTERNS = {
        'happy': ["حب", "شكر", "ممتاز", "جميل", "رائع", "❤️", "😊", "الله", "بارك", "ههه", "ضحك", "فرح"],
        'angry': ["غلط", "حرام", "زعل", "غبي", "حمق", "😡", "🤬", "تكفى", "لعنة", "كره", "بغض"],
        'sad': ["حزن", "بكاء", "دمعة", "😢", "💔", "فقدان", "موت", "مرض", "هم"],
        'urgent': ["ضروري", "طوارئ", "ساعدوني", "مساعدة", "هيلب", "urgent", "help", "سريع"]
    }
    
    @classmethod
    def analyze_mood(cls, text):
        """تحليل المزاج بدقة"""
        text_lower = text.lower()
        scores = {}
        
        for mood, words in cls.MOOD_PATTERNS.items():
            scores[mood] = sum(1 for w in words if w in text_lower)
        
        max_mood = max(scores, key=scores.get)
        
        if scores[max_mood] == 0:
            return "😐 **محايد**", "gray"
        
        colors = {
            'happy': ('😊 **سعيد وإيجابي**', 'green'),
            'angry': ('😠 **غاضب أو منزعج**', 'red'),
            'sad': ('😢 **حزين أو قلق**', 'blue'),
            'urgent': ('🚨 **عاجل يحتاج مساعدة**', 'orange')
        }
        
        return colors.get(max_mood, ('😐 **محايد**', 'gray'))
    
    @classmethod
    def detect_links(cls, text):
        """كشف الروابط المتقدم"""
        # أنماط الروابط
        url_pattern = r'(https?://[^\s]+|t\.me/[^\s]+|@[^\s]+)'
        urls = re.findall(url_pattern, text)
        
        # فحص الخطورة
        is_dangerous = False
        dangerous_found = []
        
        for url in urls:
            for pattern in SecurityConfig.DANGEROUS_PATTERNS:
                if re.search(pattern, url, re.IGNORECASE):
                    is_dangerous = True
                    dangerous_found.append(url)
                    break
        
        return urls, is_dangerous, dangerous_found
    
    @classmethod
    def check_banned_words(cls, text):
        """فحص الكلمات الممنوعة"""
        text_lower = text.lower()
        found = [word for word in SecurityConfig.BANNED_WORDS if word in text_lower]
        return found
    
    @classmethod
    def calculate_spam_score(cls, user_id, text, store):
        """حساب نقاط السبام (0-100)"""
        score = 0
        
        # 1. تكرار الرسائل
        recent_msgs = [m for m in store.user_messages[user_id] 
                      if time.time() - m < 60]
        score += len(recent_msgs) * 10
        
        # 2. روابط خطرة
        _, dangerous, _ = cls.detect_links(text)
        if dangerous:
            score += 30
        
        # 3. كلمات ممنوعة
        banned = cls.check_banned_words(text)
        score += len(banned) * 15
        
        # 4. كتابة بأحرف كبيرة (صياح)
        if text.isupper() and len(text) > 10:
            score += 10
        
        # 5. تكرار نفس الحرف
        if re.search(r'(.)\1{4,}', text):
            score += 10
            
        return min(score, 100)

# ═══════════════════════════════════════════════════════════
# 🛡️ مدير الحماية والسبام
# ═══════════════════════════════════════════════════════════
class SecurityManager:
    """إدارة الحماية المتقدمة"""
    
    @staticmethod
    def check_flood(user_id, store):
        """فحص الفيضان (السبام)"""
        now = time.time()
        config = SecurityConfig
        
        # تنظيف الرسائل القديمة
        store.user_messages[user_id] = [
            ts for ts in store.user_messages[user_id] 
            if now - ts < config.COOLDOWN_SECONDS
        ]
        
        store.user_messages[user_id].append(now)
        count = len(store.user_messages[user_id])
        
        # فحص الحد اليومي
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = f"{user_id}_{today}"
        
        if store.daily_counts[daily_key] >= config.MAX_DAILY_MESSAGES:
            return 'daily_limit', count
            
        store.daily_counts[daily_key] += 1
        
        # فحص التكرار
        if count >= config.MAX_MESSAGES:
            return 'blocked', count
        elif count == config.WARNING_LIMIT:
            return 'warning', count
        
        return 'ok', count
    
    @staticmethod
    def is_duplicate_reply(user_id, reply_text, store):
        """فحص تكرار الرد"""
        last = store.last_reply.get(user_id)
        if last == reply_text:
            return True
        store.last_reply[user_id] = reply_text
        return False
    
    @staticmethod
    def should_reply(user_id, store):
        """التحقق من ضرورة الرد"""
        # إذا كان في محادثة نشطة
        if user_id in store.talking_with:
            last_talk = store.talking_with[user_id]
            if time.time() - last_talk < SecurityConfig.TALKING_TIMEOUT:
                return False
            else:
                # انتهت المهلة
                del store.talking_with[user_id]
        
        return True

# ═══════════════════════════════════════════════════════════
# 💬 مولد الردود الذكي
# ═══════════════════════════════════════════════════════════
class ReplyGenerator:
    """توليد ردود ذكية ومتنوعة"""
    
    # ردود عادية متنوعة حسب المزاج
    REPLIES = {
        'happy': [
            "😊✨ شكراً لتواصلك الممتاز! سنرد عليك قريباً ✨😊",
            "🌸 أهلاً بك! رسالتك الإيجابية وصلت، نشكرك 🌸",
            "💫 مرحباً! نقدر طاقتك الإيجابية، سنعود إليك 💫",
        ],
        'neutral': [
            "🍃 تم استلام رسالتك، شكراً لتواصلك معنا 🍃",
            "⭐ رسالتك بأمان، سنعود إليك في أقرب وقت ⭐",
            "📩 تم التسليم بنجاح، نقدر صبرك 📩",
        ],
        'angry': [
            "🙏 نفهم شعورك، وسنساعدك في أقرب وقت ممكن",
            "💚 نعتذر إذا كان هناك أي إزعاج، فريقنا هنا للمساعدة",
            "🤝 نقدر صبرك، سنعالج طلبك بأسرع وقت",
        ],
        'sad': [
            "💙 نحن معك، وسنساعدك في أقرب وقت",
            "🫂 لا تقلق، فريق الدعم هنا لمساعدتك",
            "💚 تم استلام رسالتك، سنعود إليك بحل",
        ],
        'urgent': [
            "🚨 تم تحديد رسالتك كعاجلة! سنعالجها فوراً",
            "⚡ رسالتك في الأولوية، سنتواصل معك سريعاً",
        ]
    }
    
    SPECIAL_USERS = {
        'Yaharp': {
            'text': """🌹✨ **مرحباً حجي فرات العراقي** ✨🌹

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📨 تم تسليم رسالتك بنجاح
⏳ سيتم الرد عليك لاحقاً
💚 نشكرك على التواصل معنا
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🌸 _تحيات فريق الدعم_ 🌸""",
            'gif': SPECIAL_GIF
        }
    }
    
    @classmethod
    def generate(cls, user_id, first_name, username, mood='neutral'):
        """توليد رد مناسب"""
        # فحص المستخدمين الخاصين
        if username in cls.SPECIAL_USERS or first_name in cls.SPECIAL_USERS:
            key = username if username in cls.SPECIAL_USERS else first_name
            return cls.SPECIAL_USERS[key]['text'], cls.SPECIAL_USERS[key]['gif'], True
        
        # اختيار رد حسب المزاج
        mood_key = mood if mood in cls.REPLIES else 'neutral'
        replies = cls.REPLIES[mood_key]
        
        # تجنب التكرار
        history = store.reply_history[user_id]
        available = [r for r in replies if r not in history]
        
        if not available:
            available = replies
            history.clear()
        
        reply = random.choice(available)
        history.append(reply)
        
        # الاحتفاظ بآخر 5 ردود فقط
        if len(history) > 5:
            history.popleft()
        
        gif = random.choice(ANIME_GIFS)
        return reply, gif, False

# ═══════════════════════════════════════════════════════════
# 📋 منشئ بطاقات المعلومات
# ═══════════════════════════════════════════════════════════
class InfoCardBuilder:
    """بناء بطاقة معلومات احترافية"""
    
    @staticmethod
    async def build(sender, text, store, client):
        """بناء البطاقة الكاملة"""
        user_id = sender.id
        username = sender.username or "لا يوجد"
        first_name = sender.first_name or "لا يوجد"
        last_name = sender.last_name or ""
        
        # التحليلات
        mood, mood_color = ContentAnalyzer.analyze_mood(text)
        links, is_dangerous, dangerous_links = ContentAnalyzer.detect_links(text)
        banned_words = ContentAnalyzer.check_banned_words(text)
        spam_score = ContentAnalyzer.calculate_spam_score(user_id, text, store)
        
        # معلومات إضافية
        account_age = "غير معروف"
        try:
            if sender.date:
                age = datetime.now() - sender.date.replace(tzinfo=None)
                account_age = f"{age.days} يوم"
        except:
            pass
        
        # حالة الحظر
        block_status = "🚫 محظور" if store.is_blocked(user_id) else "✅ نشط"
        
        card = f"""🕵️‍♂️ **【 تقرير المستخدم الكامل 】** 🕵️‍♂️

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
👤 **الاسم:** {first_name} {last_name}
🆔 **المعرف:** @{username}
🔢 **الرقم:** `{user_id}`
📅 **عمر الحساب:** {account_age}
📊 **حالة الحساب:** {block_status}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
💬 **تحليل الرسالة:**
• المزاج: {mood}
• نقاط السبام: {spam_score}/100 {'🔴' if spam_score > 50 else '🟡' if spam_score > 25 else '🟢'}

📎 **الروابط:** {len(links)}
{chr(10).join([f'  • {link}' for link in links[:5]]) if links else '  • لا توجد روابط'}
{'  ⚠️ **روابط خطرة مكتشفة!** ⚠️' if is_dangerous else ''}

🚫 **كلمات ممنوعة:** {len(banned_words)}
{chr(10).join([f'  • {w}' for w in banned_words]) if banned_words else '  • لا توجد'}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📊 **إحصائيات اليوم:**
• رسائل مرسلة: {store.daily_counts.get(f"{user_id}_{datetime.now().strftime('%Y-%m-%d')}", 0)}
• إنذارات: {len([m for m in store.user_messages[user_id] if time.time() - m < 3600])}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📅 **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return card, mood, spam_score, is_dangerous

# ═══════════════════════════════════════════════════════════
# 🤖 العميل الرئيسي
# ═══════════════════════════════════════════════════════════
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# ═══════════════════════════════════════════════════════════
# 📨 معالج الرسائل الواردة
# ═══════════════════════════════════════════════════════════
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    """المعالج الرئيسي للرسائل الواردة"""
    
    # تجاهل غير الخاص
    if not event.is_private:
        return
    
    # تجاهل البوتات
    sender = await event.get_sender()
    if not isinstance(sender, User) or sender.bot:
        return
    
    user_id = sender.id
    username = sender.username or "لا يوجد"
    first_name = sender.first_name or "لا يوجد"
    last_name = sender.last_name or ""
    text = event.message.message or ""
    
    # تسجيل الرسالة
    Logger.log_message(user_id, username, text, "received")
    
    # ═══════════════════════════════════════════════
    # 🛡️ فحوصات الأمان
    # ═══════════════════════════════════════════════
    
    # 1. التحقق من الحظر
    if store.is_blocked(user_id):
        Logger.log_event("BLOCKED_USER", f"User {user_id} attempted to message")
        return
    
    # 2. التحقق من الصديق
    is_friend = user_id in SecurityConfig.FRIENDS
    
    # 3. فحص الفيضان (السبام)
    if not is_friend:
        status, count = SecurityManager.check_flood(user_id, store)
        
        if status == 'daily_limit':
            await event.reply("📛 **تم تجاوز الحد اليومي**\n\nلقد أرسلت الحد الأقصى من الرسائل اليوم. يرجى المحاولة غداً.")
            return
        
        elif status == 'blocked':
            try:
                await client(BlockRequest(id=user_id))
                store.block(user_id)
                
                warning = f"""🔨🚫 **تم الحظر التلقائي** 🚫🔨

السبب: إرسال {count} رسائل خلال {SecurityConfig.COOLDOWN_SECONDS} ثانية
⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}
🆔 المعرف: `{user_id}`

📌 **للاستئناف:** تواصل مع المشرف."""
                
                await event.reply(warning)
                Logger.log_event("AUTO_BLOCK", f"User {user_id} blocked for flooding")
                return
            except Exception as e:
                Logger.log_event("BLOCK_ERROR", f"Failed to block {user_id}: {e}")
                pass
        
        elif status == 'warning':
            await event.reply(f"""⚠️ **تحذير من السبام** ⚠️

لقد أرسلت {count} رسائل خلال {SecurityConfig.COOLDOWN_SECONDS} ثانية!
إذا وصلت إلى {SecurityConfig.MAX_MESSAGES} سيتم حظرك تلقائياً.

🐢 **يرجى التباطؤ.**""")
            return
    
    # 4. التحقق من المحادثة النشطة
    if not SecurityManager.should_reply(user_id, store):
        return
    
    # ═══════════════════════════════════════════════
    # 📋 بناء تقرير المعلومات
    # ═══════════════════════════════════════════════
    
    try:
        info_card, mood, spam_score, is_dangerous = await InfoCardBuilder.build(
            sender, text, store, client
        )
        
        # إرسال البطاقة
        await event.reply(info_card)
        await asyncio.sleep(SecurityConfig.FLOOD_SLEEP)
        
    except Exception as e:
        Logger.log_event("INFO_CARD_ERROR", f"Error building card: {e}")
    
    # ═══════════════════════════════════════════════
    # ⚠️ التعامل مع المحتوى الخطير
    # ═══════════════════════════════════════════════
    
    if is_dangerous and not is_friend:
        danger_msg = """🚨 **محتوى خطير مكتشف!** 🚨

تم اكتشاف روابط مشبوهة في رسالتك.
⚠️ يرجى عدم إرسال روابط غير آمنة.

🔒 **للأمان:** تم تسجيل هذا المحاولة."""
        await event.reply(danger_msg)
        Logger.log_event("DANGEROUS_LINK", f"User {user_id} sent dangerous links")
        return
    
    # ═══════════════════════════════════════════════
    # 💬 إنشاء وإرسال الرد
    # ═══════════════════════════════════════════════
    
    try:
        reply_text, gif_url, is_special = ReplyGenerator.generate(
            user_id, first_name, username, mood
        )
        
        # فحص تكرار الرد
        if SecurityManager.is_duplicate_reply(user_id, reply_text, store):
            # إذا تكرر، اختر رداً مختلفاً
            reply_text = random.choice([
                "🔄 **رسالة جديدة:** شكراً لتواصلك!",
                "💬 **تأكيد:** تم استلام رسالتك.",
                "✅ **تم:** رسالتك مسجلة."
            ])
        
        # إرسال الرد النصي
        await event.reply(reply_text)
        await asyncio.sleep(0.5)
        
        # إرسال الصورة المتحركة
        await event.reply(file=gif_url)
        
        # تسجيل
        action = "SPECIAL_REPLY" if is_special else "AUTO_REPLY"
        Logger.log_event(action, f"Sent to {first_name} ({user_id})")
        
    except FloodWaitError as e:
        Logger.log_event("FLOOD_WAIT", f"Waiting {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        Logger.log_event("REPLY_ERROR", f"Error: {e}")

# ═══════════════════════════════════════════════════════════
# 📤 معالج الرسائل الصادرة (تتبع المحادثات)
# ═══════════════════════════════════════════════════════════
@client.on(events.NewMessage(outgoing=True))
async def my_message_handler(event):
    """تتبع رسائلك لتجنب الرد أثناء المحادثة"""
    if not event.is_private:
        return
    
    chat_id = event.chat_id
    store.talking_with[chat_id] = time.time()
    Logger.log_message(chat_id, "me", event.message.message or "", "sent")

# ═══════════════════════════════════════════════════════════
# 🔄 معالج تعديل الرسائل
# ═══════════════════════════════════════════════════════════
@client.on(events.MessageEdited)
async def edited_handler(event):
    """التعامل مع الرسائل المعدلة"""
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    if not isinstance(sender, User):
        return
    
    Logger.log_event("MESSAGE_EDITED", f"User {sender.id} edited message")

# ═══════════════════════════════════════════════════════════
# 📊 أوامر التحكم (للمشرف فقط)
# ═══════════════════════════════════════════════════════════
@client.on(events.NewMessage(pattern=r'^/stats'))
async def stats_handler(event):
    """إحصائيات البوت"""
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    # فقط لك (يمكن تعديل الشرط)
    if sender.id not in SecurityConfig.FRIENDS and sender.id != (await client.get_me()).id:
        return
    
    stats = f"""📊 **إحصائيات البوت**

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
🚷 **المحظورون:** {len(store.blocked_users)}
💬 **المحادثات النشطة:** {len(store.talking_with)}
📅 **رسائل اليوم:** {sum(1 for k in store.daily_counts if k.endswith(datetime.now().strftime('%Y-%m-%d')))}

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
⚙️ **الإعدادات:**
• الحد الأقصى: {SecurityConfig.MAX_MESSAGES} رسائل
• فترة التبريد: {SecurityConfig.COOLDOWN_SECONDS} ثانية
• الحد اليومي: {SecurityConfig.MAX_DAILY_MESSAGES} رسالة
"""
    await event.reply(stats)

@client.on(events.NewMessage(pattern=r'^/unblock (\d+)'))
async def unblock_handler(event):
    """فك حظر مستخدم"""
    if not event.is_private:
        return
    
    sender = await event.get_sender()
    me = await client.get_me()
    
    if sender.id != me.id:
        return
    
    user_id = int(event.pattern_match.group(1))
    
    if store.is_blocked(user_id):
        try:
            await client(UnblockRequest(id=user_id))
            store.unblock(user_id)
            await event.reply(f"✅ **تم فك حظر المستخدم:** `{user_id}`")
            Logger.log_event("UNBLOCK", f"User {user_id} unblocked")
        except Exception as e:
            await event.reply(f"❌ **خطأ:** {e}")
    else:
        await event.reply("ℹ️ المستخدم غير محظور")

# ═══════════════════════════════════════════════════════════
# 🚀 الدالة الرئيسية
# ═══════════════════════════════════════════════════════════
async def main():
    """التشغيل الرئيسي"""
    await client.start()
    me = await client.get_me()
    
    banner = f"""
╔══════════════════════════════════════════════════════╗
║  🤖 البوت الذكي المتقدد - v2.0                      ║
╠══════════════════════════════════════════════════════╣
║  👤 الحساب: {me.first_name[:15]:<<20}                ║
║  🆔 المعرف: @{str(me.username):<<20}                  ║
║  🖼️ الصور المتحركة: {len(ANIME_GIFS)} صور            ║
║  🛡️ الحماية: {SecurityConfig.MAX_MESSAGES} رسائل = حظر║
║  📁 السجلات: {LOGS_DIR}                             ║
╚══════════════════════════════════════════════════════╝
"""
    print(banner)
    Logger.log_event("STARTUP", "Bot started successfully")
    
    # تشغيل المهام الدورية
    asyncio.create_task(cleanup_task())
    
    await client.run_until_disconnected()

async def cleanup_task():
    """تنظيف دوري للبيانات القديمة"""
    while True:
        await asyncio.sleep(3600)  # كل ساعة
        
        # تنظيف المحادثات القديمة
        now = time.time()
        expired = [
            uid for uid, ts in store.talking_with.items()
            if now - ts > SecurityConfig.TALKING_TIMEOUT
        ]
        for uid in expired:
            del store.talking_with[uid]
        
        # تنظيف عدادات الأيام السابقة
        today = datetime.now().strftime('%Y-%m-%d')
        old_keys = [k for k in store.daily_counts if not k.endswith(today)]
        for k in old_keys:
            del store.daily_counts[k]
        
        Logger.log_event("CLEANUP", f"Cleaned {len(expired)} expired chats")

# ═══════════════════════════════════════════════════════════
# ▶️ تشغيل
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 تم إيقاف البوت")
        Logger.log_event("SHUTDOWN", "Bot stopped by user")
    except Exception as e:
        print(f"💥 خطأ فادح: {e}")
        Logger.log_event("FATAL_ERROR", str(e))
