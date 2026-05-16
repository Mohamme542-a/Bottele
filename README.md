# 🤖 TgAuto Userbot Worker

ربط الـ Worker بلوحة تحكم TgAuto لتفعيل الرد التلقائي على حسابك الشخصي على Telegram.

## ⚠️ تنبيهات مهمة

- استخدام Userbot قد يُعتبر مخالفاً لشروط Telegram. استخدمه باعتدال.
- لا تشارك ملف `session.txt` مع أي شخص — يعطي تحكماً كاملاً بحسابك.
- ضع تأخير معقول (3+ ثواني) و Anti-spam مرتفع لتجنب الحظر.

## 📋 المتطلبات

- Python 3.10+
- حساب Telegram (شخصي)
- `api_id` و `api_hash` من https://my.telegram.org/apps
- توكن Worker من لوحة TgAuto
- رابط الـ API من لوحة TgAuto

## 🚀 التشغيل المحلي

```bash
# 1. ثبّت المتطلبات
pip install -r requirements.txt

# 2. أنشئ ملف .env
cp .env.example .env
# عدّل القيم داخله

# 3. سجّل دخول أول مرة (سيُطلب رقمك + OTP يصلك على Telegram)
python login.py

# 4. شغّل الـ Worker
python main.py
```

## ☁️ النشر على Railway (مجاناً 24/7)

1. سجّل دخولك أول مرة محلياً (`python login.py`) لإنشاء `session.txt`
2. ارفع المجلد كاملاً إلى GitHub repo
3. على Railway: New Project → Deploy from GitHub
4. أضف Environment Variables:
   - `API_BASE_URL`
   - `WORKER_TOKEN`
   - `TG_API_ID`
   - `TG_API_HASH`
   - `TG_SESSION` ← الصق محتوى ملف `session.txt` هنا

## 🐳 Docker

```bash
docker build -t tgauto .
docker run -d --restart=always --env-file .env tgauto
```

## 📁 ملفات المشروع

- `login.py` — تسجيل الدخول لأول مرة وإنشاء الجلسة
- `main.py` — الـ Worker الرئيسي (event handler)
- `config_client.py` — يجلب الإعدادات من API
- `reply_engine.py` — منطق اختيار الرد
- `anti_spam.py` — منع تكرار الرد
- `scheduler.py` — فحص ساعات النشاط
