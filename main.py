# ===================================================================
# 💀 CYBER AI ENGINE - الأسطوري 💀
# ===================================================================
# نظام ذكاء اصطناعي متطور للردود التلقائية مع لوحة تحكم سحابية
# ===================================================================

import asyncio
import random
import time
import re
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import hashlib

# ===================================================================
# المكتبات الأساسية
# ===================================================================

import aiohttp
from aiohttp import web
import google.generativeai as genai
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

# مفتاح Gemini API
GEMINI_API = "AIzaSyCXSXEcYN0aO0o3fgCqIIt9u238_sKyA80"

# الصورة اللي تترسل مع كل رد
DEFAULT_IMAGE = "https://c.top4top.io/p_3788pc3ao1.jpg"

# ===================================================================
# ⚙️ إعدادات النظام
# ===================================================================

MAX_MESSAGES = 8          # عدد الرسائل للحظر
WARNING_LIMIT = 4         # عدد الرسائل للتحذير
COOLDOWN_SECONDS = 60     # خلال 60 ثانية
TALKING_TIMEOUT = 3600    # ساعة - وضع المحادثة
REPLY_DELAY = 2           # تأخير الرد بالثواني
AUTO_BAN_ENABLED = True   # تفعيل الحظر التلقائي

# أنماط الرد
REPLY_STYLES = {
    "default": "عادي",
    "friendly": "ودي",
    "professional": "رسمي",
    "mysterious": "غامض",
    "short": "مختصر"
}

# ===================================================================
# 🗂️ هيكلة البيانات
# ===================================================================

class UserData:
    """بيانات المستخدم الكاملة"""
    def __init__(self, user_id, first_name="", username=""):
        self.user_id = user_id
        self.first_name = first_name
        self.username = username
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.messages = []  # قائمة الرسائل
        self.total_messages = 0
        self.status = "normal"  # normal, suspicious, dangerous, blocked
        self.mood_history = []
        self.rank = "عادي"  # واقي, عادي, مشبوه, خطر
        self.notes = ""     # ملاحظات يدوية
        
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
            "notes": self.notes,
            "messages": self.messages[-50:]  # آخر 50 رسالة
        }

# ===================================================================
# 💾 التخزين وإدارة البيانات
# ===================================================================

class DataManager:
    """مدير التخزين والبيانات"""
    
    def __init__(self):
        self.users: Dict[int, UserData] = {}
        self.global_messages = []  # سجل كل الرسائل
        self.blocked_users = set()
        self.excluded_users = set()  # مستثنيين من الحظر
        self.alert_keywords = ["help", "مساعدة", "urgent", "طوارئ"]
        self.load_data()
    
    def load_data(self):
        """تحميل البيانات من الملفات"""
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
                        user.notes = udata.get("notes", "")
                        self.users[uid_int] = user
            
            if os.path.exists("blocked_users.json"):
                with open("blocked_users.json", "r") as f:
                    self.blocked_users = set(json.load(f))
                    
            print("✅ تم تحميل البيانات بنجاح")
        except Exception as e:
            print(f"⚠️ خطأ في تحميل البيانات: {e}")
    
    def save_data(self):
        """حفظ البيانات إلى الملفات"""
        try:
            users_dict = {}
            for uid, user in self.users.items():
                users_dict[str(uid)] = user.to_dict()
            
            with open("users_data.json", "w", encoding="utf-8") as f:
                json.dump({"users": users_dict, "last_update": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            
            with open("blocked_users.json", "w") as f:
                json.dump(list(self.blocked_users), f)
                
            print(f"💾 تم حفظ البيانات - {len(self.users)} مستخدم")
        except Exception as e:
            print(f"⚠️ خطأ في حفظ البيانات: {e}")
    
    def get_or_create_user(self, user_id, first_name="", username=""):
        """جلب أو إنشاء مستخدم جديد"""
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
        """تسجيل رسالة جديدة"""
        if user_id in self.users:
            user = self.users[user_id]
            user.total_messages += 1
            user.last_seen = datetime.now()
            user.messages.append({
                "text": text[:500],
                "reply": reply[:500],
                "time": datetime.now().isoformat()
            })
            # الاحتفاظ بآخر 100 رسالة فقط
            if len(user.messages) > 100:
                user.messages = user.messages[-100:]
        
        # تسجيل في السجل العالمي
        self.global_messages.append({
            "user_id": user_id,
            "text": text[:200],
            "reply": reply[:200],
            "time": datetime.now().isoformat()
        })
        # الاحتفاظ بآخر 500 رسالة عالمية
        if len(self.global_messages) > 500:
            self.global_messages = self.global_messages[-500:]
        
        self.save_data()
    
    def update_rank(self, user_id):
        """تحديث رتبة المستخدم بناءً على سلوكه"""
        if user_id not in self.users:
            return
        
        user = self.users[user_id]
        msg_count = user.total_messages
        
        if msg_count > 100:
            user.rank = "خطر"
            user.status = "dangerous"
        elif msg_count > 50:
            user.rank = "مشبوه"
            user.status = "suspicious"
        elif msg_count > 10:
            user.rank = "عادي"
            user.status = "normal"
        else:
            user.rank = "واقي"
            user.status = "normal"

# ===================================================================
# 🧠 الذكاء الاصطناعي المتطور
# ===================================================================

class CyberAI:
    """نظام الذكاء الاصطناعي المتقدم"""
    
    def __init__(self):
        genai.configure(api_key=GEMINI_API)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 300,
            }
        )
        self.conversation_history = defaultdict(list)
    
    def analyze_mood(self, text: str) -> Dict:
        """تحليل المشاعر والأسلوب بشكل متقدم"""
        text_lower = text.lower()
        
        # قوائم المشاعر المتقدمة
        emotions = {
            "happy": ["شكرا", "حب", "رائع", "جميل", "❤️", "😊", "ممتاز", "حلو", "الله", "سعيد"],
            "sad": ["حزين", "بكي", "تعبان", "💔", "😢", "زعلان", "ضيق", "متعب"],
            "angry": ["غبي", "زفت", "اكره", "😡", "🤬", "حرام", "تكفى", "حمق", "غضب"],
            "fear": ["خايف", "خوف", "😨", "رعب", "مذعور", "هلع"],
            "love": ["حبيبي", "عشق", "💕", "💖", "غرام", "قلب", "روح"],
            "respect": ["شكر", "احترام", "🙏", "تقدير", "عذراً", "لو سمحت"],
        }
        
        scores = {emotion: sum(1 for w in words if w in text_lower) for emotion, words in emotions.items()}
        primary_emotion = max(scores, key=scores.get) if max(scores.values()) > 0 else "neutral"
        
        # تحليل أسلوب الكاتب
        style = {
            "length": len(text),
            "has_emoji": bool(re.search(r'[\U0001F600-\U0001F64F]', text)),
            "has_url": bool(re.search(r'https?://', text)),
            "has_question": "?" in text,
            "has_exclamation": "!" in text,
        }
        
        return {
            "primary": primary_emotion,
            "scores": scores,
            "style": style,
            "intensity": "high" if max(scores.values()) > 3 else "medium" if max(scores.values()) > 1 else "low"
        }
    
    def analyze_personality(self, user: UserData) -> Dict:
        """تحليل شخصية المستخدم بناءً على تاريخ رسائله"""
        recent_texts = " ".join([m["text"] for m in user.messages[-20:]])
        
        # تحليل بسيط للشخصية
        personality = {
            "activity_level": "high" if user.total_messages > 50 else "medium" if user.total_messages > 20 else "low",
            "talkative": user.total_messages > 30,
            "avg_message_length": sum(len(m["text"]) for m in user.messages) / max(len(user.messages), 1),
        }
        
        # كشف النوايا من النص
        intentions = []
        if any(w in recent_texts for w in ["طلب", "اريد", "ابي", "احتاج"]):
            intentions.append("طلب مساعدة")
        if any(w in recent_texts for w in ["شكر", "جزاك", "الله"]):
            intentions.append("شكر وتقدير")
        if any(w in recent_texts for w in ["مشكلة", "خطأ", "غلط", "عطل"]):
            intentions.append("شكوى أو مشكلة")
            
        return {
            "personality": personality,
            "intentions": intentions,
            "trust_score": min(100, max(0, 100 - user.total_messages * 0.5)) if user.total_messages > 30 else 100
        }
    
    async def generate_reply(self, text: str, user_name: str, mood: Dict, personality: Dict, style: str = "default") -> str:
        """توليد رد ذكي باستخدام Gemini"""
        
        style_prompts = {
            "default": "رد بشكل طبيعي ومحترم، كن لطيفاً ومختصراً.",
            "friendly": "رد بشكل ودي وحنون، استخدم إيموجيات دافئة، كن صديقاً.",
            "professional": "رد بشكل رسمي ومهني، كن محترماً ومباشراً.",
            "mysterious": "رد بشكل غامض وقوي، اجعل المرسل يشعر بالرهبة قليلاً.",
            "short": "رد باختصار شديد، كلمة أو كلمتين فقط مع إيموجي."
        }
        
        prompt = f"""
[المهمة]: أنت نظام ردود ذكي جداً. رد على المرسل بشكل طبيعي، بدون عبارات متكررة مملة.

[اسم المرسل]: {user_name}
[نص رسالته]: {text}
[تحليل مشاعره]: {mood.get('primary', 'neutral')}
[مستوى نشاطه]: {personality.get('personality', {}).get('activity_level', 'medium')}
[أسلوب الرد]: {style_prompts.get(style, style_prompts['default'])}

[تعليمات مهمة]:
- لا تقل "أنا سايبر" أو أي شيء مشابه
- كن طبيعياً كأنك بشر
- لا تكرر نفس العبارات في كل رد
- غير أسلوبك بين الحين والآخر
- استخدم إيموجيات مناسبة بشكل طبيعي

[الرد]:
"""
        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip()
            
            # تنظيف الرد من أي عبارات سيبرانية
            bad_phrases = ["سايبر", "سيبراني", "cyber", "AI", "ذكاء اصطناعي"]
            for phrase in bad_phrases:
                reply = reply.replace(phrase, "")
            
            # تحديد طول الرد
            if style == "short":
                reply = reply[:50]
            elif len(reply) > 300:
                reply = reply[:300]
                
            return reply
            
        except Exception as e:
            print(f"⚠️ خطأ في AI: {e}")
            # ردود احتياطية طبيعية
            fallback_replies = [
                "مرحباً! شكراً لتواصلك، سأرد عليك قريباً.",
                "أهلاً بك، تم استلام رسالتك بنجاح.",
                "شكراً لك، سأتأكد من رسالتك.",
                "مرحباً! كيف يمكنني مساعدتك؟"
            ]
            return random.choice(fallback_replies)
    
    def store_conversation(self, user_id, user_message, ai_reply):
        """تخزين المحادثة للذاكرة"""
        self.conversation_history[user_id].append({
            "user": user_message,
            "ai": ai_reply,
            "time": datetime.now().isoformat()
        })
        # الاحتفاظ بآخر 50 محادثة فقط
        if len(self.conversation_history[user_id]) > 50:
            self.conversation_history[user_id] = self.conversation_history[user_id][-50:]

# ===================================================================
# 🌐 لوحة التحكم السحابية
# ===================================================================

class Dashboard:
    """لوحة تحكم ويب متكاملة"""
    
    def __init__(self, data_manager: DataManager, ai_system: CyberAI):
        self.data = data_manager
        self.ai = ai_system
        self.start_time = datetime.now()
    
    def get_stats(self) -> Dict:
        """إحصائيات سريعة"""
        return {
            "total_users": len(self.data.users),
            "blocked_users": len(self.data.blocked_users),
            "total_messages": sum(u.total_messages for u in self.data.users.values()),
            "active_today": sum(1 for u in self.data.users.values() if u.last_seen.date() == datetime.now().date()),
            "uptime": str(datetime.now() - self.start_time).split(".")[0],
            "ai_status": "Online",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_dashboard_html(self) -> str:
        """توليد صفحة لوحة التحكم"""
        stats = self.get_stats()
        users = list(self.data.users.values())
        users.sort(key=lambda x: x.total_messages, reverse=True)
        
        # بناء جدول المستخدمين
        users_table = ""
        for user in users[:20]:  # آخر 20 مستخدم
            users_table += f"""
            <tr class="{'danger' if user.status == 'dangerous' else 'warning' if user.status == 'suspicious' else ''}">
                <td>{user.first_name or 'مجهول'}</td>
                <td>@{user.username or '-'}</td>
                <td>{user.total_messages}</td>
                <td>{user.rank}</td>
                <td class="{'text-danger' if user.status == 'dangerous' else 'text-warning' if user.status == 'suspicious' else 'text-success'}">{user.status}</td>
                <td>{user.last_seen.strftime('%H:%M %d/%m') if user.last_seen else '-'}</td>
            </tr>
            """
        
        if not users_table:
            users_table = "<tr><td colspan='6' style='text-align:center'>لا يوجد مستخدمين بعد</td></tr>"
        
        html = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💀 سايبر أنجن - لوحة التحكم</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Cairo', 'Segoe UI', system-ui;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            padding: 30px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 20px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 255, 255, 0.2);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(135deg, #00ffff, #ff00ff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            margin-top: 15px;
            background: #00ff0044;
            color: #00ff00;
            border: 1px solid #00ff00;
        }}
        
        /* Cards */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(30, 30, 50, 0.9);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid rgba(0, 255, 255, 0.2);
            transition: all 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: #00ffff;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00ffff;
        }}
        
        .stat-label {{
            color: #94a3b8;
            margin-top: 10px;
        }}
        
        /* Tables */
        .card {{
            background: rgba(30, 30, 50, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 30px;
            border: 1px solid rgba(0, 255, 255, 0.2);
        }}
        
        .card-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #00ffff;
            border-right: 3px solid #00ffff;
            padding-right: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #334155;
        }}
        
        th {{
            color: #00ffff;
            font-weight: 600;
        }}
        
        tr:hover {{
            background: rgba(0, 255, 255, 0.1);
        }}
        
        .danger {{
            background: rgba(255, 0, 0, 0.2);
        }}
        
        .warning {{
            background: rgba(255, 165, 0, 0.2);
        }}
        
        .text-danger {{
            color: #ff4444;
        }}
        
        .text-warning {{
            color: #ffaa00;
        }}
        
        .text-success {{
            color: #00ff00;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .live {{
            animation: pulse 2s infinite;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💀 سايبر أنجن | Cyber Engine 💀</h1>
            <div class="status-badge live">🟢 النظام يعمل بكفاءة عالية</div>
            <p style="margin-top: 15px;">نظام ذكاء اصطناعي متطور للردود التلقائية مع لوحة تحكم كاملة</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats['total_users']}</div>
                <div class="stat-label">👥 إجمالي المستخدمين</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['blocked_users']}</div>
                <div class="stat-label">🚫 المستخدمين المحظورين</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['total_messages']}</div>
                <div class="stat-label">💬 إجمالي الرسائل</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['active_today']}</div>
                <div class="stat-label">🟢 نشطاء اليوم</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">📊 إحصائيات النظام</div>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div>⏱️ وقت التشغيل: <strong>{stats['uptime']}</strong></div>
                <div>🧠 الذكاء الاصطناعي: <strong class="text-success">{stats['ai_status']}</strong></div>
                <div>🛡️ الحماية التلقائية: <strong>{"✅ مفعلة" if AUTO_BAN_ENABLED else "❌ معطلة"}</strong></div>
                <div>🎨 أنماط الرد: <strong>{len(REPLY_STYLES)} نمط</strong></div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">👥 قائمة المستخدمين</div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>الاسم</th>
                            <th>اسم المستخدم</th>
                            <th>الرسائل</th>
                            <th>الرتبة</th>
                            <th>الحالة</th>
                            <th>آخر ظهور</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users_table}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>💀 سايبر أنجن - نظام حماية وردود ذكية 💀</p>
            <p style="font-size: 12px; margin-top: 10px;">{"التحديث الأخير: " + stats['timestamp'].replace("T", " ")[:19]}</p>
        </div>
    </div>
</body>
</html>
"""
        return html

# ===================================================================
# 🚀 تشغيل النظام
# ===================================================================

# تهيئة المديرين
data_manager = DataManager()
ai_system = CyberAI()
dashboard = Dashboard(data_manager, ai_system)

# تشغيل العميل
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# ===================================================================
# 🛡️ مكافحة السبام
# ===================================================================

user_timestamps = defaultdict(list)

async def check_spam(user_id):
    now = time.time()
    user_timestamps[user_id] = [ts for ts in user_timestamps[user_id] if now - ts < COOLDOWN_SECONDS]
    user_timestamps[user_id].append(now)
    count = len(user_timestamps[user_id])
    return count, count >= MAX_MESSAGES

# ===================================================================
# 📩 معالج الرسائل الرئيسي
# ===================================================================

talking_mode = {}  # وضع المحادثة: user_id -> آخر وقت رديت عليه

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
    
    # وضع المحادثة: إذا كنت ترد على هذا الشخص
    if user_id in talking_mode:
        if time.time() - talking_mode[user_id] < TALKING_TIMEOUT:
            print(f"⏸️ وضع المحادثة - تم تجاهل {user_name}")
            return
    
    # المستخدمين المحظورين
    if user_id in data_manager.blocked_users:
        return
    
    # حفظ بيانات المستخدم
    user = data_manager.get_or_create_user(user_id, user_name, username)
    
    # تحديث الرتبة
    data_manager.update_rank(user_id)
    
    # مكافحة السبام
    msg_count, is_spam = await check_spam(user_id)
    
    if msg_count == WARNING_LIMIT and not is_spam:
        await event.reply("⚠️ **تنبيه** ⚠️\n\nلقد أرسلت عدة رسائل بسرعة، رجاءً تمهل قليلاً.")
        data_manager.add_message(user_id, text, "تحذير سبام")
        return
    
    if is_spam and AUTO_BAN_ENABLED:
        data_manager.blocked_users.add(user_id)
        await event.reply("🚫 **تم حظرك تلقائياً** 🚫\n\nلقد تجاوزت الحد المسموح من الرسائل.")
        data_manager.add_message(user_id, text, "حظر تلقائي")
        data_manager.save_data()
        return
    
    # تحليل الرسالة
    mood = ai_system.analyze_mood(text)
    personality = ai_system.analyze_personality(user)
    
    # توليد رد ذكي
    reply_style = random.choice(list(REPLY_STYLES.keys()))
    ai_reply = await ai_system.generate_reply(
        text=text,
        user_name=user_name,
        mood=mood,
        personality=personality,
        style=reply_style
    )
    
    # تخزين المحادثة
    ai_system.store_conversation(user_id, text, ai_reply)
    
    # تأخير الرد
    await asyncio.sleep(REPLY_DELAY)
    
    # إرسال الرد
    await event.reply(ai_reply)
    
    # إرسال الصورة مع الرد
    try:
        await event.reply(file=DEFAULT_IMAGE)
    except Exception as e:
        print(f"⚠️ فشل إرسال الصورة: {e}")
    
    # تسجيل في السجل
    data_manager.add_message(user_id, text, ai_reply)
    
    # طباعة في الكونسول
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_name}: {text[:50]}... -> {ai_reply[:30]}...")

# ===================================================================
# 📤 تتبع رسائل المالك (وضع المحادثة)
# ===================================================================

@client.on(events.NewMessage(outgoing=True))
async def track_owner_messages(event):
    if not event.is_private:
        return
    
    # سجل أنك رديت على هذا الشخص
    chat_id = event.chat_id
    talking_mode[chat_id] = time.time()
    
    # تنظيف الإدخالات القديمة
    now = time.time()
    expired = [uid for uid, ts in talking_mode.items() if now - ts > TALKING_TIMEOUT]
    for uid in expired:
        del talking_mode[uid]

# ===================================================================
# 🌐 خادم الويب للوحة التحكم
# ===================================================================

async def web_handler(request):
    """صفحة الويب الرئيسية"""
    html = await dashboard.get_dashboard_html()
    return web.Response(text=html, content_type="text/html")

async def api_stats(request):
    """API للإحصائيات"""
    return web.json_response(dashboard.get_stats())

async def api_users(request):
    """API لقائمة المستخدمين"""
    users = []
    for user in data_manager.users.values():
        users.append({
            "id": user.user_id,
            "name": user.first_name,
            "username": user.username,
            "messages": user.total_messages,
            "rank": user.rank,
            "status": user.status
        })
    return web.json_response({"users": users, "count": len(users)})

async def health_check(request):
    """صفحة الصحة - للـ UptimeRobot"""
    return web.Response(
        text=f"✅ CYBER AI ENGINE ONLINE\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nUsers: {len(data_manager.users)}\nMessages: {sum(u.total_messages for u in data_manager.users.values())}",
        content_type="text/plain"
    )

async def start_web_server():
    """تشغيل خادم الويب"""
    app = web.Application()
    app.router.add_get('/', web_handler)
    app.router.add_get('/dashboard', web_handler)
    app.router.add_get('/api/stats', api_stats)
    app.router.add_get('/api/users', api_users)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ خادم الويب شغال على http://localhost:8080")
    print("📊 لوحة التحكم: http://localhost:8080/dashboard")

# ===================================================================
# 🔄 النبض الذاتي (عشان ما ينام)
# ===================================================================

async def self_ping():
    """يبقى البوت فايق 24/7"""
    while True:
        await asyncio.sleep(240)  # كل 4 دقائق
        try:
            async with aiohttp.ClientSession() as session:
                await session.get('http://localhost:8080/health', timeout=5)
                print(f"✅ نبض ذاتي ناجح - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"⚠️ فشل النبض: {e}")

# ===================================================================
# 🚀 التشغيل الرئيسي
# ===================================================================

async def main():
    print("=" * 70)
    print("💀 سايبر أنجن - النسخة الأسطورية الخارقة 💀")
    print("=" * 70)
    
    # تشغيل البوت
    await client.start()
    me = await client.get_me()
    
    # تشغيل خادم الويب
    asyncio.create_task(start_web_server())
    
    # تشغيل النبض الذاتي
    asyncio.create_task(self_ping())
    
    print(f"✅ الحساب: {me.first_name} (@{me.username})")
    print(f"🆔 الايدي: {me.id}")
    print(f"🧠 الذكاء الاصطناعي: Gemini 1.5 Flash")
    print(f"🖼️ صورة الرد: {DEFAULT_IMAGE}")
    print(f"🛡️ الحماية: {MAX_MESSAGES} رسائل خلال {COOLDOWN_SECONDS} ثانية = حظر")
    print("=" * 70)
    print("🌐 الروابط:")
    print(f"   - لوحة التحكم: https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/dashboard")
    print(f"   - فحص الصحة: https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/health")
    print("=" * 70)
    print("💀 النظام جاهز للعمل 24/7 💀")
    print("=" * 70)
    
    await client.run_until_disconnected()

# ===================================================================
if __name__ == "__main__":
    asyncio.run(main())
