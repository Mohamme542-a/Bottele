"""تسجيل الدخول لأول مرة — ينشئ session string."""
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")

print("🔐 سيُطلب منك إدخال رقم هاتفك + كود OTP يصل على Telegram")
with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_str = client.session.save()
    with open("session.txt", "w") as f:
        f.write(session_str)
    print("\n✅ تم! حُفظت الجلسة في session.txt")
    print("   استخدم محتواه كقيمة TG_SESSION في .env عند النشر على السحابة")
    print(f"\nالرقم: {client.get_me().phone}")
