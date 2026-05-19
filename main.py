# ===================================================================
# 💀 CYBER AI ENGINE - ULTIMATE EDITION v3 💀
# ===================================================================
# - بدون كلمة سر / بدون مصادقة (وصول مفتوح للوحة)
# - 15+ ميزة جديدة: قواعد تلقائية، بث، جدولة، قائمة بيضاء،
#   كلمات محظورة، ملاحظات، وسوم، ساعات هدوء، ترحيب، تصدير،
#   بحث، إحصائيات بالساعة، قوالب، توجيه، مستويات، حظر مؤقت
# ===================================================================

import asyncio
import os
import json
import time
import random
import re
import csv
import io
from datetime import datetime, timedelta
from collections import defaultdict, deque

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import GetCommonChatsRequest
from telethon.tl.functions.contacts import (
    ImportContactsRequest, DeleteContactsRequest,
)
from telethon.tl.types import InputPhoneContact
from aiohttp import web

# ===================================================================
# ✅ بيانات الحساب
# ===================================================================
API_ID = 34082021
API_HASH = "0b88d1ec5f05cb43a8f01cc1c93de4e9"
SESSION = "1BJWap1sBu30GulG13MrOKpfv_bU1No5RUDlcR21GmF03_V8H9it6LseZpHODk51zqzzjS4-sOx98AoXANMGLBI0K4dP0sERlkMJP3RLfaWWeRMvRODzhU5sDkJgvn8pZQ63-2hIYTmGGjyLq-1FfhxcIY9_AJOmhFJ4i3O6AByrj4ffn0CNrlVIxsEMgCaf_ntkJ9uLsMW7gSd_tnhD4N3J6Oi_mm-G_HN6E4Q7YKZVTTOOWjellx66kJa2429iDS7LSiaR5PI7xZ-_iSOyzxvADvnNPtQExxQtdrgUBxjWdB5bgSJqbMY9T3ynsxfss3v1ZfkWRzr2SjrZ5kXLFmKN3Zj5bAiU="
OWNER_ID = 8676210788
PORT = int(os.environ.get("PORT", 8080))

# ===================================================================
# ⚙️ الإعدادات الافتراضية
# ===================================================================
DEFAULT_SETTINGS = {
    "max_messages": 8,
    "warning_limit": 4,
    "cooldown_seconds": 60,
    "reply_delay": 0.5,
    "talking_timeout": 3600,
    "auto_reply": True,
    "send_info_card": True,
    "auto_block": True,
    "silent_mode": False,
    "special_username": "Yaharp",
    "special_reply": "🌹 مرحباً حجي فرات العراقي 🌹",
    "welcome_enabled": True,
    "welcome_message": "👋 أهلاً بك! تم استلام رسالتك وسيتم الرد قريباً.",
    "quiet_hours_enabled": False,
    "quiet_start": 0,    # 0-23
    "quiet_end": 7,
    "quiet_reply": "🌙 المالك نائم الآن، سيتم الرد صباحاً.",
    "forward_to_owner": False,
    "banned_words": ["spam", "scam"],
    "replies": [
        "مرحباً! شكراً لتواصلك 🌸",
        "أهلاً بك، رسالتك وصلت ✅",
        "شكراً لك، سأرد عليك قريباً 💫",
    ],
    "templates": {
        "ترحيب": "أهلاً وسهلاً 🌹",
        "وداع": "إلى اللقاء 👋",
        "شكر": "شكراً جزيلاً لك 💙",
    },
    "keyword_rules": [
        # {"keyword": "سعر", "reply": "للأسعار راسل @owner"}
    ],
}

# ===================================================================
# 📦 إدارة البيانات
# ===================================================================
DATA_DIR = os.environ.get("DATA_DIR", ".")
def _p(name): return os.path.join(DATA_DIR, name)

class DataManager:
    def __init__(self):
        self.users = {}            # uid -> dict(name, username, msgs, last, notes, tags, level, points, warns, temp_ban_until)
        self.blocked = set()
        self.whitelist = set()
        self.settings = dict(DEFAULT_SETTINGS)
        self.events_log = deque(maxlen=1000)
        self.hourly_stats = defaultdict(int)  # "YYYY-MM-DD HH" -> count
        self.scheduled = []        # [{id, target, text, run_at, sent}]
        self.start_time = time.time()
        self._load()

    def _load(self):
        try:
            with open(_p("users.json"), "r", encoding="utf-8") as f:
                self.users = {int(k): v for k, v in json.load(f).items()}
        except Exception: pass
        try:
            with open(_p("blocked.json"), "r", encoding="utf-8") as f:
                self.blocked = set(json.load(f))
        except Exception: pass
        try:
            with open(_p("whitelist.json"), "r", encoding="utf-8") as f:
                self.whitelist = set(json.load(f))
        except Exception: pass
        try:
            with open(_p("settings.json"), "r", encoding="utf-8") as f:
                s = json.load(f)
                for k, v in s.items(): self.settings[k] = v
        except Exception: pass
        try:
            with open(_p("hourly.json"), "r", encoding="utf-8") as f:
                self.hourly_stats = defaultdict(int, json.load(f))
        except Exception: pass
        try:
            with open(_p("scheduled.json"), "r", encoding="utf-8") as f:
                self.scheduled = json.load(f)
        except Exception: pass

    def save(self):
        try:
            with open(_p("users.json"), "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2, default=str)
            with open(_p("blocked.json"), "w", encoding="utf-8") as f:
                json.dump(list(self.blocked), f)
            with open(_p("whitelist.json"), "w", encoding="utf-8") as f:
                json.dump(list(self.whitelist), f)
            with open(_p("settings.json"), "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            with open(_p("hourly.json"), "w", encoding="utf-8") as f:
                json.dump(dict(self.hourly_stats), f)
            with open(_p("scheduled.json"), "w", encoding="utf-8") as f:
                json.dump(self.scheduled, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SAVE ERROR] {e}")

    def log(self, kind, msg):
        self.events_log.append({
            "t": datetime.now().strftime("%H:%M:%S"),
            "kind": kind, "msg": msg,
        })

    def touch_user(self, sender):
        uid = sender.id
        u = self.users.get(uid, {
            "id": uid, "name": "", "username": "", "msgs": 0,
            "first_seen": datetime.now().isoformat(timespec="seconds"),
            "last": "", "notes": "", "tags": [],
            "level": 1, "points": 0, "warns": 0, "temp_ban_until": 0,
        })
        u["name"] = (getattr(sender, "first_name", "") or "") + " " + (getattr(sender, "last_name", "") or "")
        u["name"] = u["name"].strip() or "—"
        u["username"] = getattr(sender, "username", "") or ""
        u["msgs"] += 1
        u["last"] = datetime.now().isoformat(timespec="seconds")
        u["points"] += 1
        u["level"] = 1 + u["points"] // 25
        self.users[uid] = u
        # hourly bucket
        bucket = datetime.now().strftime("%Y-%m-%d %H")
        self.hourly_stats[bucket] += 1
        return u

DM = DataManager()

# ===================================================================
# 🤖 Telethon
# ===================================================================
client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
talking = {}        # uid -> {count, warns, last, blocked_at}
info_cache = {}     # uid -> (timestamp, card_text)
phone_cache = {}    # uid -> phone or ""

def in_quiet_hours():
    s = DM.settings
    if not s.get("quiet_hours_enabled"): return False
    h = datetime.now().hour
    a, b = s["quiet_start"], s["quiet_end"]
    return (a <= h < b) if a <= b else (h >= a or h < b)

def is_temp_banned(uid):
    u = DM.users.get(uid)
    if not u: return False
    return u.get("temp_ban_until", 0) > time.time()

async def try_get_phone(user):
    if user.id in phone_cache:
        return phone_cache[user.id]
    phone = getattr(user, "phone", "") or ""
    if not phone:
        try:
            fake = f"+1555{random.randint(1000000, 9999999)}"
            r = await client(ImportContactsRequest([
                InputPhoneContact(client_id=0, phone=fake,
                                  first_name=str(user.id), last_name="probe")
            ]))
            if r.users:
                phone = getattr(r.users[0], "phone", "") or ""
            if r.imported:
                try:
                    await client(DeleteContactsRequest(id=[u.user_id for u in r.imported]))
                except Exception: pass
        except FloodWaitError as e:
            DM.log("warn", f"FloodWait phone: {e.seconds}s")
        except Exception: pass
    phone_cache[user.id] = phone
    return phone

async def build_info_card(sender):
    cached = info_cache.get(sender.id)
    if cached and time.time() - cached[0] < 300:
        return cached[1]
    name = ((getattr(sender, "first_name", "") or "") + " " + (getattr(sender, "last_name", "") or "")).strip() or "—"
    uname = getattr(sender, "username", "") or "—"
    uid = sender.id
    about, common, photos = "—", "—", "—"
    try:
        full = await client(GetFullUserRequest(sender))
        about = (getattr(full.full_user, "about", "") or "—")
    except Exception: pass
    try:
        cc = await client(GetCommonChatsRequest(user_id=sender, max_id=0, limit=50))
        common = str(len(cc.chats))
    except Exception: pass
    try:
        ph = await client.get_profile_photos(sender, limit=0)
        photos = str(getattr(ph, "total", len(ph)))
    except Exception: pass
    phone = await try_get_phone(sender) or "—"
    card = (
        "👤 <b>بطاقة المستخدم</b>\n"
        f"• الاسم: <b>{name}</b>\n"
        f"• المعرّف: @{uname}\n"
        f"• ID: <code>{uid}</code>\n"
        f"• الهاتف: {phone}\n"
        f"• البايو: {about}\n"
        f"• مجموعات مشتركة: {common}\n"
        f"• عدد الصور: {photos}\n"
    )
    info_cache[sender.id] = (time.time(), card)
    return card

# ===================================================================
# 📨 معالج الرسائل
# ===================================================================
@client.on(events.NewMessage(incoming=True))
async def handler(event):
    try:
        if not event.is_private: return
        sender = await event.get_sender()
        if sender is None or getattr(sender, "bot", False): return
        uid = sender.id
        if uid == OWNER_ID: return

        s = DM.settings
        u = DM.touch_user(sender)
        text = (event.raw_text or "").strip()

        # حظر مؤقت
        if is_temp_banned(uid):
            return

        # مستخدم محظور دائماً
        if uid in DM.blocked: return

        # كلمات محظورة → حظر تلقائي
        low = text.lower()
        if any(w.lower() in low for w in s.get("banned_words", [])):
            DM.blocked.add(uid)
            DM.log("block", f"banned-word: {u['name']} ({uid})")
            DM.save()
            try: await client.edit_permissions  # noqa
            except Exception: pass
            return

        # توجيه للمالك
        if s.get("forward_to_owner"):
            try: await event.forward_to(OWNER_ID)
            except Exception: pass

        # whitelist يتجاوز كل القيود
        is_white = uid in DM.whitelist

        # عداد الرسائل (سبام)
        st = talking.get(uid, {"count": 0, "warns": 0, "last": 0})
        now = time.time()
        if now - st["last"] < s["cooldown_seconds"]:
            st["count"] += 1
        else:
            st["count"] = 1
        st["last"] = now
        talking[uid] = st

        if not is_white and st["count"] >= s["max_messages"] and s["auto_block"]:
            DM.blocked.add(uid)
            DM.log("block", f"spam: {u['name']} ({uid})")
            DM.save()
            return

        if s.get("silent_mode"): 
            DM.save(); return

        # ساعات الهدوء
        if in_quiet_hours():
            try: await event.reply(s["quiet_reply"])
            except Exception: pass
            DM.save(); return

        # رسالة ترحيب لأول مرة
        first_time = u["msgs"] == 1
        await asyncio.sleep(s["reply_delay"])

        # قواعد الكلمات المفتاحية
        matched_rule = None
        for rule in s.get("keyword_rules", []):
            if rule.get("keyword", "").lower() in low:
                matched_rule = rule; break

        try:
            if matched_rule:
                await event.reply(matched_rule["reply"])
            elif first_time and s.get("welcome_enabled"):
                await event.reply(s["welcome_message"])
            elif (getattr(sender, "username", "") or "").lower() == s["special_username"].lower():
                await event.reply(s["special_reply"])
            elif s.get("auto_reply"):
                await event.reply(random.choice(s["replies"]))

            if s.get("send_info_card") and first_time:
                try:
                    card = await build_info_card(sender)
                    await client.send_message(OWNER_ID, card, parse_mode="html")
                except Exception as e:
                    DM.log("warn", f"info card: {e}")
        except FloodWaitError as e:
            DM.log("warn", f"FloodWait reply: {e.seconds}s")
        except Exception as e:
            DM.log("error", f"reply: {e}")

        DM.log("msg", f"{u['name']}: {text[:40]}")
        DM.save()
    except Exception as e:
        DM.log("error", f"handler: {e}")

# ===================================================================
# ⏰ مهام دورية: تنظيف + جدولة
# ===================================================================
async def cleanup_loop():
    while True:
        await asyncio.sleep(300)
        cutoff = time.time() - DM.settings["talking_timeout"]
        for uid in list(talking.keys()):
            if talking[uid]["last"] < cutoff:
                talking.pop(uid, None)

async def scheduler_loop():
    while True:
        await asyncio.sleep(20)
        now = time.time()
        changed = False
        for item in DM.scheduled:
            if not item.get("sent") and item.get("run_at", 0) <= now:
                try:
                    await client.send_message(int(item["target"]), item["text"])
                    item["sent"] = True
                    DM.log("sched", f"sent to {item['target']}")
                    changed = True
                except Exception as e:
                    DM.log("error", f"sched: {e}")
                    item["sent"] = True
                    changed = True
        if changed: DM.save()

# ===================================================================
# 🌐 لوحة التحكم - HTML
# ===================================================================
DASHBOARD_HTML = r"""<!doctype html>
<html lang="ar" dir="rtl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>💀 Cyber Control Panel</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',Tahoma,sans-serif;background:#0a0e1a;color:#e6e6e6;min-height:100vh}
header{background:linear-gradient(135deg,#1a0033,#330066);padding:18px 24px;box-shadow:0 4px 20px rgba(138,43,226,.4);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
header h1{font-size:22px;background:linear-gradient(90deg,#ff00cc,#00ffff);-webkit-background-clip:text;color:transparent}
.status{font-size:13px;color:#0f0}
nav{background:#12172a;padding:0 16px;display:flex;gap:4px;overflow-x:auto;border-bottom:1px solid #222a44}
nav button{background:none;border:none;color:#aaa;padding:14px 18px;cursor:pointer;font-size:14px;border-bottom:3px solid transparent;white-space:nowrap}
nav button.active{color:#0ff;border-color:#0ff;background:rgba(0,255,255,.05)}
nav button:hover{color:#fff}
main{padding:20px;max-width:1400px;margin:0 auto}
.tab{display:none}.tab.active{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}
.card{background:linear-gradient(135deg,#1a1f3a,#252b50);padding:18px;border-radius:12px;border:1px solid #2a3458}
.card h3{font-size:12px;color:#888;margin-bottom:8px;text-transform:uppercase}
.card .v{font-size:28px;font-weight:bold;color:#0ff}
table{width:100%;border-collapse:collapse;background:#12172a;border-radius:8px;overflow:hidden;margin-top:10px}
th,td{padding:10px;text-align:right;border-bottom:1px solid #222a44;font-size:13px}
th{background:#1a1f3a;color:#0ff}
tr:hover{background:#1a1f3a}
button.btn,a.btn{background:linear-gradient(135deg,#8a2be2,#ff00cc);color:#fff;border:none;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:13px;text-decoration:none;display:inline-block}
button.danger{background:linear-gradient(135deg,#cc0033,#ff3366)}
button.ok{background:linear-gradient(135deg,#00aa55,#00cc77)}
button.small{padding:4px 10px;font-size:12px;margin:2px}
input,textarea,select{background:#0d1224;color:#fff;border:1px solid #2a3458;padding:9px;border-radius:6px;font-size:14px;width:100%;font-family:inherit}
label{display:block;margin:10px 0 4px;color:#aaa;font-size:13px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.box{background:#12172a;padding:18px;border-radius:10px;border:1px solid #222a44;margin-bottom:14px}
.box h2{color:#0ff;font-size:16px;margin-bottom:12px;border-bottom:1px solid #2a3458;padding-bottom:8px}
.log{font-family:monospace;font-size:12px;background:#000;padding:12px;border-radius:6px;max-height:420px;overflow:auto}
.log div{padding:3px 0;border-bottom:1px solid #111}
.kind{display:inline-block;padding:1px 8px;border-radius:4px;margin-left:6px;font-size:11px}
.kind.msg{background:#003366}.kind.block{background:#660033}.kind.warn{background:#664400}
.kind.error{background:#aa0000}.kind.sched{background:#006633}
.heat{display:grid;grid-template-columns:repeat(24,1fr);gap:2px;margin-top:10px}
.heat div{height:24px;border-radius:2px;background:#111;text-align:center;font-size:9px;color:#666;padding-top:6px}
@media(max-width:700px){.row{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}}
</style></head><body>
<header><h1>💀 CYBER ULTIMATE PANEL v3</h1><span class="status" id="st">● متصل</span></header>
<nav id="nav"></nav>
<main id="main"></main>
<script>
const TABS=[
 ['stats','📊 إحصائيات'],['users','👥 المستخدمين'],['blocked','🚫 المحظورين'],
 ['whitelist','✅ القائمة البيضاء'],['rules','🎯 قواعد تلقائية'],['templates','📋 القوالب'],
 ['broadcast','📢 بث جماعي'],['schedule','⏰ جدولة'],['banned','🛑 كلمات محظورة'],
 ['quiet','🌙 ساعات الهدوء'],['welcome','👋 الترحيب'],['settings','⚙️ الإعدادات'],
 ['send','💌 إرسال مباشر'],['logs','📜 السجل'],['tools','🛠️ أدوات']
];
let active='stats',data={};
const nav=document.getElementById('nav');
TABS.forEach(([k,n])=>{const b=document.createElement('button');b.textContent=n;b.onclick=()=>{active=k;render();};b.id='b_'+k;nav.appendChild(b);});

async function api(p,opt={}){const r=await fetch('/api/'+p,opt);return r.json();}
async function refresh(){data=await api('all');render();}

function fmt(o){return JSON.stringify(o,null,2);}
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

function render(){
 document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
 const ab=document.getElementById('b_'+active);if(ab)ab.classList.add('active');
 const m=document.getElementById('main');m.innerHTML='';
 ({stats:vStats,users:vUsers,blocked:vBlocked,whitelist:vWhite,rules:vRules,
   templates:vTpl,broadcast:vBroad,schedule:vSched,banned:vBanned,quiet:vQuiet,
   welcome:vWelcome,settings:vSettings,send:vSend,logs:vLogs,tools:vTools}[active]||(()=>{}))(m);
}

function vStats(m){
 const s=data.stats||{};
 m.innerHTML=`<div class="cards">
  <div class="card"><h3>👥 المستخدمين</h3><div class="v">${s.users||0}</div></div>
  <div class="card"><h3>🚫 المحظورين</h3><div class="v">${s.blocked||0}</div></div>
  <div class="card"><h3>✅ القائمة البيضاء</h3><div class="v">${s.whitelist||0}</div></div>
  <div class="card"><h3>📨 إجمالي الرسائل</h3><div class="v">${s.total_msgs||0}</div></div>
  <div class="card"><h3>⏰ مدة التشغيل</h3><div class="v">${s.uptime||'—'}</div></div>
  <div class="card"><h3>📋 مجدولة</h3><div class="v">${s.scheduled||0}</div></div>
 </div>
 <div class="box"><h2>🔥 نشاط آخر 24 ساعة</h2><div class="heat" id="h"></div></div>`;
 const h=document.getElementById('h');const hr=s.hourly||[];
 const mx=Math.max(1,...hr);
 hr.forEach((v,i)=>{const d=document.createElement('div');
  const a=v/mx;d.style.background=`rgba(0,255,255,${0.1+a*0.9})`;d.textContent=v||'';d.title=i+':00 → '+v;h.appendChild(d);});
}

function vUsers(m){
 const u=data.users||[];
 m.innerHTML=`<div class="box"><h2>👥 المستخدمين (${u.length})</h2>
 <input id="q" placeholder="🔍 ابحث بالاسم أو المعرف أو ID..." oninput="filterU()">
 <div id="ut"></div></div>`;
 window.filterU=()=>{const q=document.getElementById('q').value.toLowerCase();
  const f=u.filter(x=>!q||(x.name||'').toLowerCase().includes(q)||(x.username||'').toLowerCase().includes(q)||String(x.id).includes(q));
  document.getElementById('ut').innerHTML=tblU(f);};
 filterU();
}
function tblU(u){
 if(!u.length)return '<p style="padding:20px;color:#666">لا يوجد</p>';
 return `<table><tr><th>الاسم</th><th>المعرف</th><th>ID</th><th>رسائل</th><th>المستوى</th><th>الوسوم</th><th>إجراءات</th></tr>`+
  u.slice(0,200).map(x=>`<tr>
  <td>${esc(x.name)}</td><td>@${esc(x.username||'-')}</td><td>${x.id}</td>
  <td>${x.msgs}</td><td>⭐ ${x.level}</td>
  <td>${(x.tags||[]).map(t=>`<span class="kind msg">${esc(t)}</span>`).join('')}</td>
  <td>
   <button class="btn small danger" onclick="block(${x.id})">حظر</button>
   <button class="btn small" onclick="tempBan(${x.id})">حظر مؤقت</button>
   <button class="btn small ok" onclick="addWhite(${x.id})">قائمة بيضاء</button>
   <button class="btn small" onclick="editUser(${x.id})">📝</button>
  </td></tr>`).join('')+`</table>`;
}
window.block=async id=>{await api('block',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});refresh();};
window.tempBan=async id=>{const h=prompt('عدد الساعات للحظر المؤقت:','24');if(!h)return;
 await api('temp_ban',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,hours:+h})});refresh();};
window.addWhite=async id=>{await api('whitelist_add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});refresh();};
window.editUser=async id=>{const u=(data.users||[]).find(x=>x.id===id);if(!u)return;
 const notes=prompt('ملاحظات:',u.notes||'');if(notes===null)return;
 const tags=prompt('وسوم (مفصولة بفاصلة):',(u.tags||[]).join(','));if(tags===null)return;
 await api('user_edit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,notes,tags:tags.split(',').map(s=>s.trim()).filter(Boolean)})});refresh();};

function vBlocked(m){
 const b=data.blocked||[];
 m.innerHTML=`<div class="box"><h2>🚫 المحظورين (${b.length})</h2>
 <button class="btn danger" onclick="clearAll()">🗑️ فك حظر الكل</button>
 <table style="margin-top:12px"><tr><th>ID</th><th>الاسم</th><th></th></tr>
 ${b.map(x=>`<tr><td>${x.id}</td><td>${esc(x.name||'-')}</td><td><button class="btn small ok" onclick="unb(${x.id})">فك</button></td></tr>`).join('')}
 </table></div>`;
 window.unb=async id=>{await api('unblock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});refresh();};
 window.clearAll=async()=>{if(!confirm('تأكيد فك حظر الكل؟'))return;await api('unblock_all',{method:'POST'});refresh();};
}

function vWhite(m){
 const w=data.whitelist||[];
 m.innerHTML=`<div class="box"><h2>✅ القائمة البيضاء (${w.length})</h2>
 <p style="color:#888;font-size:12px;margin-bottom:8px">يتجاوزون كل قيود السبام والحظر التلقائي</p>
 <input id="wid" placeholder="ID للإضافة"><button class="btn ok" onclick="wadd()">+ إضافة</button>
 <table style="margin-top:12px"><tr><th>ID</th><th></th></tr>
 ${w.map(id=>`<tr><td>${id}</td><td><button class="btn small danger" onclick="wdel(${id})">حذف</button></td></tr>`).join('')}
 </table></div>`;
 window.wadd=async()=>{const v=document.getElementById('wid').value.trim();if(!v)return;
  await api('whitelist_add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:+v})});refresh();};
 window.wdel=async id=>{await api('whitelist_del',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});refresh();};
}

function vRules(m){
 const r=data.settings?.keyword_rules||[];
 m.innerHTML=`<div class="box"><h2>🎯 قواعد الرد التلقائي بالكلمات</h2>
 <p style="color:#888;font-size:12px">عند ورود كلمة معينة في الرسالة، يتم الرد بنص مخصص.</p>
 <div class="row"><input id="rk" placeholder="الكلمة المفتاحية"><input id="rr" placeholder="نص الرد"></div>
 <button class="btn ok" style="margin-top:10px" onclick="ar()">+ إضافة قاعدة</button>
 <table style="margin-top:14px"><tr><th>#</th><th>الكلمة</th><th>الرد</th><th></th></tr>
 ${r.map((x,i)=>`<tr><td>${i+1}</td><td>${esc(x.keyword)}</td><td>${esc(x.reply)}</td>
  <td><button class="btn small danger" onclick="dr(${i})">حذف</button></td></tr>`).join('')}</table></div>`;
 window.ar=async()=>{const k=document.getElementById('rk').value.trim(),v=document.getElementById('rr').value.trim();
  if(!k||!v)return;await api('rule_add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keyword:k,reply:v})});refresh();};
 window.dr=async i=>{await api('rule_del',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({i})});refresh();};
}

function vTpl(m){
 const t=data.settings?.templates||{};
 m.innerHTML=`<div class="box"><h2>📋 قوالب الردود</h2>
 <div class="row"><input id="tk" placeholder="اسم القالب"><input id="tv" placeholder="النص"></div>
 <button class="btn ok" style="margin-top:10px" onclick="at()">+ حفظ</button>
 <table style="margin-top:14px"><tr><th>الاسم</th><th>النص</th><th></th></tr>
 ${Object.entries(t).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${esc(v)}</td>
  <td><button class="btn small danger" onclick="dt('${esc(k)}')">حذف</button></td></tr>`).join('')}</table></div>`;
 window.at=async()=>{const k=document.getElementById('tk').value.trim(),v=document.getElementById('tv').value.trim();
  if(!k||!v)return;await api('tpl_set',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k,v})});refresh();};
 window.dt=async k=>{await api('tpl_del',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({k})});refresh();};
}

function vBroad(m){
 m.innerHTML=`<div class="box"><h2>📢 بث جماعي</h2>
 <label>الهدف:</label>
 <select id="bt"><option value="all">جميع المستخدمين</option><option value="white">القائمة البيضاء فقط</option><option value="tag">حسب وسم</option></select>
 <label>الوسم (إن اخترت "حسب وسم"):</label><input id="btag" placeholder="مثلاً: vip">
 <label>الرسالة:</label><textarea id="bm" rows="5"></textarea>
 <button class="btn" style="margin-top:10px" onclick="dobr()">🚀 إرسال البث</button>
 <p id="br" style="margin-top:10px;color:#0f0"></p></div>`;
 window.dobr=async()=>{const r=await api('broadcast',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({target:document.getElementById('bt').value,tag:document.getElementById('btag').value,text:document.getElementById('bm').value})});
  document.getElementById('br').textContent='✅ تم الإرسال إلى '+(r.sent||0)+' مستخدم ('+(r.failed||0)+' فشل)';};
}

function vSched(m){
 const s=data.scheduled||[];
 m.innerHTML=`<div class="box"><h2>⏰ الرسائل المجدولة</h2>
 <div class="row"><input id="sid" placeholder="ID المستهدف"><input id="sdt" type="datetime-local"></div>
 <label>الرسالة:</label><textarea id="stx" rows="3"></textarea>
 <button class="btn ok" style="margin-top:10px" onclick="addS()">+ جدولة</button>
 <table style="margin-top:14px"><tr><th>الهدف</th><th>الوقت</th><th>الحالة</th><th>النص</th><th></th></tr>
 ${s.map(x=>`<tr><td>${x.target}</td><td>${new Date(x.run_at*1000).toLocaleString('ar-EG')}</td>
  <td>${x.sent?'✅ مُرسل':'⏳ منتظر'}</td><td>${esc((x.text||'').slice(0,40))}</td>
  <td><button class="btn small danger" onclick="dS('${x.id}')">حذف</button></td></tr>`).join('')}</table></div>`;
 window.addS=async()=>{const id=document.getElementById('sid').value,dt=document.getElementById('sdt').value,tx=document.getElementById('stx').value;
  if(!id||!dt||!tx)return;await api('sched_add',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({target:id,text:tx,run_at:Math.floor(new Date(dt).getTime()/1000)})});refresh();};
 window.dS=async id=>{await api('sched_del',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});refresh();};
}

function vBanned(m){
 const b=data.settings?.banned_words||[];
 m.innerHTML=`<div class="box"><h2>🛑 الكلمات المحظورة</h2>
 <p style="color:#888;font-size:12px">أي مستخدم يرسل واحدة منها يُحظر تلقائياً.</p>
 <input id="bw" placeholder="كلمة"><button class="btn danger" onclick="abw()">+ إضافة</button>
 <div style="margin-top:14px">${b.map(w=>`<span class="kind block" style="font-size:14px;padding:6px 12px;margin:4px;cursor:pointer" onclick="dbw('${esc(w)}')">${esc(w)} ✕</span>`).join('')}</div></div>`;
 window.abw=async()=>{const v=document.getElementById('bw').value.trim();if(!v)return;
  await api('banned_add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({w:v})});refresh();};
 window.dbw=async w=>{await api('banned_del',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({w})});refresh();};
}

function vQuiet(m){
 const s=data.settings||{};
 m.innerHTML=`<div class="box"><h2>🌙 ساعات الهدوء</h2>
 <label><input type="checkbox" id="qe" ${s.quiet_hours_enabled?'checked':''}> تفعيل</label>
 <div class="row"><div><label>من الساعة (0-23):</label><input id="qs" type="number" min="0" max="23" value="${s.quiet_start}"></div>
 <div><label>إلى الساعة:</label><input id="qz" type="number" min="0" max="23" value="${s.quiet_end}"></div></div>
 <label>الرد خلال الهدوء:</label><textarea id="qr" rows="3">${esc(s.quiet_reply||'')}</textarea>
 <button class="btn ok" style="margin-top:10px" onclick="sq()">💾 حفظ</button></div>`;
 window.sq=async()=>{await api('settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
  quiet_hours_enabled:document.getElementById('qe').checked,
  quiet_start:+document.getElementById('qs').value,quiet_end:+document.getElementById('qz').value,
  quiet_reply:document.getElementById('qr').value})});refresh();};
}

function vWelcome(m){
 const s=data.settings||{};
 m.innerHTML=`<div class="box"><h2>👋 رسالة الترحيب</h2>
 <label><input type="checkbox" id="we" ${s.welcome_enabled?'checked':''}> إرسال ترحيب للمستخدمين الجدد</label>
 <label>النص:</label><textarea id="wm" rows="4">${esc(s.welcome_message||'')}</textarea>
 <button class="btn ok" style="margin-top:10px" onclick="sw()">💾 حفظ</button></div>`;
 window.sw=async()=>{await api('settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
  welcome_enabled:document.getElementById('we').checked,welcome_message:document.getElementById('wm').value})});refresh();};
}

function vSettings(m){
 const s=data.settings||{};
 m.innerHTML=`<div class="box"><h2>⚙️ الإعدادات العامة</h2>
 <div class="row">
  <div><label>الحد الأقصى للرسائل قبل الحظر</label><input id="s_max" type="number" value="${s.max_messages}"></div>
  <div><label>حد التحذير</label><input id="s_warn" type="number" value="${s.warning_limit}"></div>
  <div><label>مدة التهدئة (ثانية)</label><input id="s_cool" type="number" value="${s.cooldown_seconds}"></div>
  <div><label>تأخير الرد (ثانية)</label><input id="s_del" type="number" step="0.1" value="${s.reply_delay}"></div>
  <div><label>مهلة الجلسة (ثانية)</label><input id="s_tt" type="number" value="${s.talking_timeout}"></div>
  <div><label>المعرّف الخاص</label><input id="s_sp" value="${esc(s.special_username)}"></div>
 </div>
 <label>الرد الخاص:</label><textarea id="s_sr" rows="2">${esc(s.special_reply)}</textarea>
 <label>الردود العشوائية (سطر لكل رد):</label>
 <textarea id="s_rep" rows="5">${esc((s.replies||[]).join('\n'))}</textarea>
 <div style="margin-top:10px">
  <label><input type="checkbox" id="s_ar" ${s.auto_reply?'checked':''}> رد تلقائي</label>
  <label><input type="checkbox" id="s_ic" ${s.send_info_card?'checked':''}> إرسال بطاقة معلومات للمالك</label>
  <label><input type="checkbox" id="s_ab" ${s.auto_block?'checked':''}> حظر تلقائي عند السبام</label>
  <label><input type="checkbox" id="s_sm" ${s.silent_mode?'checked':''}> الوضع الصامت (لا ردود)</label>
  <label><input type="checkbox" id="s_fo" ${s.forward_to_owner?'checked':''}> توجيه كل الرسائل للمالك</label>
 </div>
 <button class="btn ok" style="margin-top:14px" onclick="saveS()">💾 حفظ الإعدادات</button></div>`;
 window.saveS=async()=>{await api('settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
  max_messages:+document.getElementById('s_max').value,warning_limit:+document.getElementById('s_warn').value,
  cooldown_seconds:+document.getElementById('s_cool').value,reply_delay:+document.getElementById('s_del').value,
  talking_timeout:+document.getElementById('s_tt').value,special_username:document.getElementById('s_sp').value,
  special_reply:document.getElementById('s_sr').value,
  replies:document.getElementById('s_rep').value.split('\n').map(x=>x.trim()).filter(Boolean),
  auto_reply:document.getElementById('s_ar').checked,send_info_card:document.getElementById('s_ic').checked,
  auto_block:document.getElementById('s_ab').checked,silent_mode:document.getElementById('s_sm').checked,
  forward_to_owner:document.getElementById('s_fo').checked})});refresh();alert('✅ تم الحفظ');};
}

function vSend(m){
 m.innerHTML=`<div class="box"><h2>💌 إرسال رسالة مباشرة</h2>
 <label>ID المستلم:</label><input id="snid">
 <label>الرسالة:</label><textarea id="snm" rows="5"></textarea>
 <button class="btn" style="margin-top:10px" onclick="snd()">🚀 إرسال</button>
 <p id="snr" style="margin-top:10px;color:#0f0"></p></div>`;
 window.snd=async()=>{const r=await api('send',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({id:document.getElementById('snid').value,text:document.getElementById('snm').value})});
  document.getElementById('snr').textContent=r.ok?'✅ تم الإرسال':'❌ '+r.error;};
}

function vLogs(m){
 const l=data.logs||[];
 m.innerHTML=`<div class="box"><h2>📜 سجل الأحداث</h2>
 <button class="btn danger" onclick="clr()">🗑️ مسح</button>
 <div class="log">${l.slice().reverse().map(x=>`<div>[${x.t}] <span class="kind ${x.kind}">${x.kind}</span> ${esc(x.msg)}</div>`).join('')}</div></div>`;
 window.clr=async()=>{await api('logs_clear',{method:'POST'});refresh();};
}

function vTools(m){
 m.innerHTML=`<div class="box"><h2>🛠️ أدوات</h2>
 <a class="btn" href="/api/export" target="_blank">📤 تصدير كل البيانات (JSON)</a>
 <a class="btn" href="/api/export_csv" target="_blank">📊 تصدير المستخدمين (CSV)</a>
 <button class="btn danger" onclick="rst()">♻️ إعادة تعيين الإحصائيات</button>
 <h2 style="margin-top:20px">📥 استيراد بيانات</h2>
 <textarea id="imp" rows="6" placeholder='ألصق JSON هنا'></textarea>
 <button class="btn" style="margin-top:8px" onclick="doImp()">📥 استيراد</button>
 <p id="impr" style="color:#0f0;margin-top:8px"></p></div>`;
 window.rst=async()=>{if(!confirm('متأكد؟'))return;await api('reset_stats',{method:'POST'});refresh();};
 window.doImp=async()=>{try{const j=JSON.parse(document.getElementById('imp').value);
  const r=await api('import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(j)});
  document.getElementById('impr').textContent=r.ok?'✅ تم الاستيراد':'❌ '+r.error;refresh();
 }catch(e){alert('JSON غير صالح');}};
}

refresh();setInterval(refresh,8000);
</script></body></html>"""

# ===================================================================
# 🌐 API
# ===================================================================
def J(o, **kw): return web.json_response(o, **kw)

async def page(req): return web.Response(text=DASHBOARD_HTML, content_type="text/html")

def uptime_str():
    s = int(time.time() - DM.start_time)
    h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return f"{h}س {m}د {s}ث"

def hourly_24():
    # last 24h buckets ending at current hour
    out = []
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    for i in range(23, -1, -1):
        k = (now - timedelta(hours=i)).strftime("%Y-%m-%d %H")
        out.append(DM.hourly_stats.get(k, 0))
    return out

async def api_all(req):
    total_msgs = sum(u.get("msgs", 0) for u in DM.users.values())
    blocked_list = []
    for uid in DM.blocked:
        u = DM.users.get(uid, {})
        blocked_list.append({"id": uid, "name": u.get("name", "-")})
    return J({
        "stats": {
            "users": len(DM.users), "blocked": len(DM.blocked),
            "whitelist": len(DM.whitelist), "total_msgs": total_msgs,
            "uptime": uptime_str(), "scheduled": sum(1 for s in DM.scheduled if not s.get("sent")),
            "hourly": hourly_24(),
        },
        "users": sorted(DM.users.values(), key=lambda x: -x.get("msgs", 0)),
        "blocked": blocked_list,
        "whitelist": sorted(list(DM.whitelist)),
        "settings": DM.settings,
        "scheduled": DM.scheduled,
        "logs": list(DM.events_log),
    })

async def api_block(req):
    d = await req.json(); DM.blocked.add(int(d["id"])); DM.save(); return J({"ok": True})
async def api_unblock(req):
    d = await req.json(); DM.blocked.discard(int(d["id"])); DM.save(); return J({"ok": True})
async def api_unblock_all(req):
    DM.blocked.clear(); DM.save(); return J({"ok": True})

async def api_temp_ban(req):
    d = await req.json(); uid = int(d["id"]); h = int(d.get("hours", 24))
    u = DM.users.setdefault(uid, {"id": uid, "msgs": 0, "tags": []})
    u["temp_ban_until"] = time.time() + h * 3600
    DM.log("block", f"temp ban {uid} for {h}h"); DM.save(); return J({"ok": True})

async def api_white_add(req):
    d = await req.json(); DM.whitelist.add(int(d["id"])); DM.save(); return J({"ok": True})
async def api_white_del(req):
    d = await req.json(); DM.whitelist.discard(int(d["id"])); DM.save(); return J({"ok": True})

async def api_user_edit(req):
    d = await req.json(); uid = int(d["id"])
    u = DM.users.get(uid)
    if u:
        u["notes"] = d.get("notes", "")
        u["tags"] = d.get("tags", [])
        DM.save()
    return J({"ok": True})

async def api_settings(req):
    d = await req.json()
    for k, v in d.items():
        if k in DM.settings: DM.settings[k] = v
    DM.save(); return J({"ok": True})

async def api_rule_add(req):
    d = await req.json()
    DM.settings.setdefault("keyword_rules", []).append({"keyword": d["keyword"], "reply": d["reply"]})
    DM.save(); return J({"ok": True})
async def api_rule_del(req):
    d = await req.json(); i = int(d["i"])
    r = DM.settings.get("keyword_rules", [])
    if 0 <= i < len(r): r.pop(i)
    DM.save(); return J({"ok": True})

async def api_tpl_set(req):
    d = await req.json()
    DM.settings.setdefault("templates", {})[d["k"]] = d["v"]
    DM.save(); return J({"ok": True})
async def api_tpl_del(req):
    d = await req.json()
    DM.settings.get("templates", {}).pop(d["k"], None); DM.save(); return J({"ok": True})

async def api_banned_add(req):
    d = await req.json()
    bw = DM.settings.setdefault("banned_words", [])
    if d["w"] not in bw: bw.append(d["w"])
    DM.save(); return J({"ok": True})
async def api_banned_del(req):
    d = await req.json()
    bw = DM.settings.get("banned_words", [])
    if d["w"] in bw: bw.remove(d["w"])
    DM.save(); return J({"ok": True})

async def api_send(req):
    d = await req.json()
    try:
        await client.send_message(int(d["id"]), d["text"])
        DM.log("msg", f"manual → {d['id']}")
        return J({"ok": True})
    except Exception as e:
        return J({"ok": False, "error": str(e)})

async def api_broadcast(req):
    d = await req.json()
    target, tag, text = d.get("target"), (d.get("tag") or "").strip(), d.get("text", "")
    if not text: return J({"sent": 0, "failed": 0})
    ids = []
    if target == "white":
        ids = list(DM.whitelist)
    elif target == "tag":
        ids = [u["id"] for u in DM.users.values() if tag in (u.get("tags") or [])]
    else:
        ids = [u["id"] for u in DM.users.values() if u["id"] not in DM.blocked]
    sent = failed = 0
    for uid in ids:
        try:
            await client.send_message(int(uid), text); sent += 1
            await asyncio.sleep(0.3)
        except Exception: failed += 1
    DM.log("msg", f"broadcast: {sent} sent, {failed} failed")
    return J({"sent": sent, "failed": failed})

async def api_sched_add(req):
    d = await req.json()
    DM.scheduled.append({
        "id": f"s{int(time.time()*1000)}",
        "target": str(d["target"]), "text": d["text"],
        "run_at": int(d["run_at"]), "sent": False,
    })
    DM.save(); return J({"ok": True})
async def api_sched_del(req):
    d = await req.json()
    DM.scheduled = [x for x in DM.scheduled if x["id"] != d["id"]]
    DM.save(); return J({"ok": True})

async def api_logs_clear(req):
    DM.events_log.clear(); return J({"ok": True})
async def api_reset_stats(req):
    DM.hourly_stats.clear(); DM.save(); return J({"ok": True})

async def api_export(req):
    payload = {
        "users": DM.users, "blocked": list(DM.blocked),
        "whitelist": list(DM.whitelist), "settings": DM.settings,
        "scheduled": DM.scheduled, "hourly": dict(DM.hourly_stats),
    }
    return web.Response(
        text=json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        content_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="cyber_backup.json"'},
    )

async def api_export_csv(req):
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["id", "name", "username", "msgs", "level", "points", "tags", "notes", "last"])
    for u in DM.users.values():
        w.writerow([u.get("id"), u.get("name"), u.get("username"),
                    u.get("msgs"), u.get("level"), u.get("points"),
                    "|".join(u.get("tags") or []), u.get("notes", ""), u.get("last", "")])
    return web.Response(text=buf.getvalue(), content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="users.csv"'})

async def api_import(req):
    try:
        d = await req.json()
        if "users" in d: DM.users = {int(k): v for k, v in d["users"].items()}
        if "blocked" in d: DM.blocked = set(int(x) for x in d["blocked"])
        if "whitelist" in d: DM.whitelist = set(int(x) for x in d["whitelist"])
        if "settings" in d:
            for k, v in d["settings"].items(): DM.settings[k] = v
        if "scheduled" in d: DM.scheduled = d["scheduled"]
        DM.save(); return J({"ok": True})
    except Exception as e:
        return J({"ok": False, "error": str(e)})

# ===================================================================
# 🚀 التشغيل
# ===================================================================
async def run_web():
    app = web.Application()
    app.router.add_get("/", page)
    app.router.add_get("/api/all", api_all)
    app.router.add_post("/api/block", api_block)
    app.router.add_post("/api/unblock", api_unblock)
    app.router.add_post("/api/unblock_all", api_unblock_all)
    app.router.add_post("/api/temp_ban", api_temp_ban)
    app.router.add_post("/api/whitelist_add", api_white_add)
    app.router.add_post("/api/whitelist_del", api_white_del)
    app.router.add_post("/api/user_edit", api_user_edit)
    app.router.add_post("/api/settings", api_settings)
    app.router.add_post("/api/rule_add", api_rule_add)
    app.router.add_post("/api/rule_del", api_rule_del)
    app.router.add_post("/api/tpl_set", api_tpl_set)
    app.router.add_post("/api/tpl_del", api_tpl_del)
    app.router.add_post("/api/banned_add", api_banned_add)
    app.router.add_post("/api/banned_del", api_banned_del)
    app.router.add_post("/api/send", api_send)
    app.router.add_post("/api/broadcast", api_broadcast)
    app.router.add_post("/api/sched_add", api_sched_add)
    app.router.add_post("/api/sched_del", api_sched_del)
    app.router.add_post("/api/logs_clear", api_logs_clear)
    app.router.add_post("/api/reset_stats", api_reset_stats)
    app.router.add_get("/api/export", api_export)
    app.router.add_get("/api/export_csv", api_export_csv)
    app.router.add_post("/api/import", api_import)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT); await site.start()
    print(f"🌐 Dashboard: http://0.0.0.0:{PORT}  (بدون مصادقة)")

async def main():
    await client.start()
    me = await client.get_me()
    print("=" * 60)
    print(f"💀 CYBER ULTIMATE v3 — مفعّل لـ @{me.username or me.id}")
    print(f"🌐 لوحة التحكم على المنفذ: {PORT}")
    print("🎯 15+ ميزة جاهزة")
    print("=" * 60)
    asyncio.create_task(cleanup_loop())
    asyncio.create_task(scheduler_loop())
    await run_web()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
