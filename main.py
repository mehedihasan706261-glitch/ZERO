import asyncio
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CopyTextButton
import re
import json
import time
import logging
from collections import deque
import random

# ================= CONFIGURATION =================
TOKEN = "8647348457:AAEi5Kre2Df4Xeig80aZzsd_7zR9MFO739Y"

# --- Panel 1 (MNIT Network Only) ---
API_BASE_URL = "https://x.mnitnetwork.com"
API_KEY = "M_A4UFFVM8R"

# --- Panel 2 (Hadi API Engine Token) ---
API_2_TOKEN = "Q1ZQNEVBmWRoT1GGcmuJSVuIiEV3ZFJeYXeUVllmhkJeYIBrWoM"

# --- Panel 3 (Shahrukh Panel) ---
SHAHRUKH_COOKIE = "PHPSESSID=a3dc9fc506af3f1d833ae944367fe1c1"
SHAHRUKH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-E236B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.137 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://65.109.111.158/ints/agent/SMSCDRStats",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Cookie": SHAHRUKH_COOKIE
}

# --- Panel 4 (MSI Panel) ---
MSI_API_KEY = "ZIaAfHKXgIV5T088QlFUREg="
MSI_COOKIE = "PHPSESSID=m0gfslir4h1aig0qcm1e6gtlu1"
MSI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-E236B Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.7727.137 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "http://145.239.130.45/ints/agent/SMSCDRStats",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Cookie": MSI_COOKIE
}

OTP_GROUP_LINK = "https://t.me/+4nMAFt2hYk04YTRl"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================
db = sqlite3.connect("otp_pro_panel.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance REAL DEFAULT 0.0, username TEXT, fullname TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS services (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, range_val TEXT, country_code TEXT, flag TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)")
cursor.execute("INSERT OR IGNORE INTO config VALUES ('min_withdraw', '100')")
cursor.execute("INSERT OR IGNORE INTO config VALUES ('earning_per_otp', '10')")
cursor.execute("INSERT OR IGNORE INTO config VALUES ('maintenance_mode', 'off')")
cursor.execute("INSERT OR IGNORE INTO config VALUES ('withdraw_enabled', 'on')")
cursor.execute("""CREATE TABLE IF NOT EXISTS withdraw_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    bkash_number TEXT,
    status TEXT DEFAULT 'pending',
    requested_at TEXT
)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS used_numbers (
    user_id INTEGER,
    number_id TEXT,
    phone_number TEXT,
    service_id INTEGER,
    used_at TEXT,
    PRIMARY KEY (user_id, number_id)
)""")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (user_id TEXT PRIMARY KEY)")
cursor.execute("""CREATE TABLE IF NOT EXISTS otp_success_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_id INTEGER, 
    timestamp TEXT
)""")
cursor.execute("INSERT OR IGNORE INTO admins VALUES ('6820798198')")
cursor.execute("INSERT OR IGNORE INTO admins VALUES ('7689218221')")

# ========== MANUAL NUMBERS TABLES ==========
cursor.execute("""CREATE TABLE IF NOT EXISTS manual_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT,
    country_name TEXT,
    flag TEXT,
    give_amount INTEGER DEFAULT 1,
    otp_rate REAL DEFAULT 0.0,
    stock INTEGER DEFAULT 0,
    cooldown INTEGER DEFAULT 0
)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS manual_numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_id INTEGER,
    number TEXT,
    FOREIGN KEY(service_id) REFERENCES manual_services(id)
)""")

try: cursor.execute("ALTER TABLE users ADD COLUMN active_manual TEXT")
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN manual_cooldowns TEXT")
except: pass
try: cursor.execute("ALTER TABLE manual_services ADD COLUMN cooldown INTEGER DEFAULT 0")
except: pass

db.commit()

# ================= HELPERS =================
COUNTRY_PREFIXES = {
    "1": ("US", "🇺🇸"), "7": ("RU", "🇷🇺"), "20": ("EG", "🇪🇬"), "27": ("ZA", "🇿🇦"),
    "30": ("GR", "🇬🇷"), "31": ("NL", "🇳🇱"), "32": ("BE", "🇧🇪"), "33": ("FR", "🇫🇷"),
    "34": ("ES", "🇪🇸"), "36": ("HU", "🇭🇺"), "39": ("IT", "🇮🇹"), "40": ("RO", "🇷🇴"),
    "41": ("CH", "🇨🇭"), "43": ("AT", "🇦🇹"), "44": ("GB", "🇬🇧"), "45": ("DK", "🇩🇰"),
    "46": ("SE", "🇸🇪"), "47": ("NO", "🇳🇴"), "48": ("PL", "🇵🇱"), "49": ("DE", "🇩🇪"),
    "51": ("PE", "🇵🇪"), "52": ("MX", "🇲🇽"), "53": ("CU", "🇨🇺"), "54": ("AR", "🇦🇷"),
    "55": ("BR", "🇧🇷"), "56": ("CL", "🇨🇱"), "57": ("CO", "🇨🇴"), "58": ("VE", "🇻🇪"),
    "60": ("MY", "🇲🇾"), "61": ("AU", "🇦🇺"), "62": ("ID", "🇮🇩"), "63": ("PH", "🇵🇭"),
    "64": ("NZ", "🇳🇿"), "65": ("SG", "🇸🇬"), "66": ("TH", "🇹🇭"), "81": ("JP", "🇯🇵"),
    "82": ("KR", "🇰🇷"), "84": ("VN", "🇻🇳"), "86": ("CN", "🇨🇳"), "90": ("TR", "🇹🇷"),
    "91": ("IN", "🇮🇳"), "92": ("PK", "🇵🇰"), "93": ("AF", "🇦🇫"), "94": ("LK", "🇱🇰"),
    "95": ("MM", "🇲🇲"), "98": ("IR", "🇮🇷"), "211": ("SS", "🇸🇸"), "212": ("MA", "🇲🇦"),
    "213": ("DZ", "🇩🇿"), "216": ("TN", "🇹🇳"), "218": ("LY", "🇱🇾"), "220": ("GM", "🇬🇲"),
    "221": ("SN", "🇸🇳"), "222": ("MR", "🇲🇷"), "223": ("ML", "🇲🇱"), "224": ("GN", "🇬🇳"),
    "225": ("CI", "🇨🇮"), "226": ("BF", "🇧🇫"), "227": ("NE", "🇳🇪"), "228": ("TG", "🇹🇬"),
    "229": ("BJ", "🇧🇯"), "230": ("MU", "🇲🇺"), "231": ("LR", "🇱🇷"), "232": ("SL", "🇸🇱"),
    "233": ("GH", "🇬🇭"), "234": ("NG", "🇳🇬"), "235": ("TD", "🇹🇩"), "236": ("CF", "🇨🇫"),
    "237": ("CM", "🇨🇲"), "238": ("CV", "🇨🇻"), "239": ("ST", "🇸🇹"), "240": ("GQ", "🇬🇶"),
    "241": ("GA", "🇬🇦"), "242": ("CG", "🇨🇬"), "243": ("CD", "🇨🇩"), "244": ("AO", "🇦🇴"),
    "245": ("GW", "🇬🇼"), "246": ("IO", "🇮🇴"), "247": ("AC", "🇦🇨"), "248": ("SC", "🇸🇨"),
    "249": ("SD", "🇸🇩"), "250": ("RW", "🇷🇼"), "251": ("ET", "🇪🇹"), "252": ("SO", "🇸🇴"),
    "253": ("DJ", "🇩🇯"), "254": ("KE", "🇰🇪"), "255": ("TZ", "🇹🇿"), "256": ("UG", "🇺🇬"),
    "257": ("BI", "🇧🇮"), "258": ("MZ", "🇲🇿"), "260": ("ZM", "🇿🇲"), "261": ("MG", "🇲🇬"),
    "262": ("RE", "🇷🇪"), "263": ("ZW", "🇿🇼"), "264": ("NA", "🇳🇦"), "265": ("MW", "🇲🇼"),
    "266": ("LS", "🇱🇸"), "267": ("BW", "🇧🇼"), "268": ("SZ", "🇸🇿"), "269": ("KM", "🇰🇲"),
    "290": ("SH", "🇸🇭"), "291": ("ER", "🇪🇷"), "297": ("AW", "🇦🇼"), "298": ("FO", "🇫🇴"),
    "299": ("GL", "🇬🇱"), "350": ("GI", "🇬🇮"), "351": ("PT", "🇵🇹"), "352": ("LU", "🇱🇺"),
    "353": ("IE", "🇮🇪"), "354": ("IS", "🇮🇸"), "355": ("AL", "🇦🇱"), "356": ("MT", "🇲🇹"),
    "357": ("CY", "🇨🇾"), "358": ("FI", "🇫🇮"), "359": ("BG", "🇧🇬"), "370": ("LT", "🇱🇹"),
    "371": ("LV", "🇱🇻"), "372": ("EE", "🇪🇪"), "373": ("MD", "🇲🇩"), "374": ("AM", "🇦🇲"),
    "375": ("BY", "🇧🇾"), "376": ("AD", "🇦🇩"), "377": ("MC", "🇲🇨"), "378": ("SM", "🇸🇲"),
    "379": ("VA", "🇻🇦"), "380": ("UA", "🇺🇦"), "381": ("RS", "🇷🇸"), "382": ("ME", "🇲🇪"),
    "385": ("HR", "🇭🇷"), "386": ("SI", "🇸🇮"), "387": ("BA", "🇧🇦"), "389": ("MK", "🇲🇰"),
    "420": ("CZ", "🇨🇿"), "421": ("SK", "🇸🇰"), "423": ("LI", "🇱🇮"), "500": ("FK", "🇫🇰"),
    "501": ("BZ", "🇧🇿"), "502": ("GT", "🇬🇹"), "503": ("SV", "🇸🇻"), "504": ("HN", "🇭🇳"),
    "505": ("NI", "🇳🇮"), "506": ("CR", "🇨🇷"), "507": ("PA", "🇵🇦"), "508": ("PM", "🇵🇲"),
    "509": ("HT", "🇭🇹"), "590": ("GP", "🇬🇵"), "591": ("BO", "🇧🇴"), "592": ("GY", "🇬🇾"),
    "593": ("EC", "🇪🇨"), "594": ("GF", "🇬🇫"), "595": ("PY", "🇵🇾"), "596": ("MQ", "🇲🇶"),
    "597": ("SR", "🇸🇷"), "598": ("UY", "🇺🇾"), "599": ("CW", "🇨🇼"), "670": ("TL", "🇹🇱"),
    "672": ("NF", "🇳🇫"), "673": ("BN", "🇧🇳"), "674": ("NR", "🇳🇷"), "675": ("PG", "🇵🇬"),
    "676": ("TO", "🇹🇴"), "677": ("SB", "🇸🇧"), "678": ("VU", "🇻🇺"), "679": ("FJ", "🇫🇯"),
    "680": ("PW", "🇵🇼"), "681": ("WF", "🇼🇫"), "682": ("CK", "🇨🇰"), "683": ("NU", "🇳🇺"),
    "685": ("WS", "🇼🇸"), "686": ("KI", "🇰🇮"), "687": ("NC", "🇳🇨"), "688": ("TV", "🇹🇻"),
    "689": ("PF", "🇵🇫"), "690": ("TK", "🇹🇰"), "691": ("FM", "🇫🇲"), "692": ("MH", "🇲🇭"),
    "850": ("KP", "🇰🇵"), "852": ("HK", "🇭🇰"), "853": ("MO", "🇲🇴"), "855": ("KH", "🇰🇭"),
    "856": ("LA", "🇱🇦"), "880": ("BD", "🇧🇩"), "886": ("TW", "🇹🇼"), "960": ("MV", "🇲🇻"),
    "961": ("LB", "🇱🇧"), "962": ("JO", "🇯🇴"), "963": ("SY", "🇸🇾"), "964": ("IQ", "🇮🇶"),
    "965": ("KW", "🇰🇼"), "966": ("SA", "🇸🇦"), "967": ("YE", "🇾🇪"), "968": ("OM", "🇴🇲"),
    "970": ("PS", "🇵🇸"), "971": ("AE", "🇦🇪"), "972": ("IL", "🇮🇱"), "973": ("BH", "🇧🇭"),
    "974": ("QA", "🇶🇦"), "975": ("BT", "🇧🇹"), "976": ("MN", "🇲🇳"), "977": ("NP", "🇳🇵"),
    "992": ("TJ", "🇹🇯"), "993": ("TM", "🇹🇲"), "994": ("AZ", "🇦🇿"), "995": ("GE", "🇬🇪"),
    "996": ("KG", "🇰🇬"), "998": ("UZ", "🇺🇿")
}

def get_country_from_phone(phone: str) -> tuple:
    digits = ''.join(filter(str.isdigit, phone))
    if not digits:
        return "BD", "🇧🇩"
    for length in range(5, 0, -1):
        prefix = digits[:length]
        if prefix in COUNTRY_PREFIXES:
            return COUNTRY_PREFIXES[prefix]
    for length in range(3, 0, -1):
        prefix = digits[:length]
        if prefix in COUNTRY_PREFIXES:
            return COUNTRY_PREFIXES[prefix]
    return "BD", "🇧🇩"

def format_number_with_flag(phone: str) -> str:
    _, flag = get_country_from_phone(phone)
    return f"{flag} {phone}"

def is_admin(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (str(user_id),))
    return cursor.fetchone() is not None

def get_flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return "🌍"
    return chr(ord('🇦') + (ord(country_code[0].upper()) - ord('A'))) + chr(ord('🇦') + (ord(country_code[1].upper()) - ord('A')))

def is_maintenance_mode() -> bool:
    cursor.execute("SELECT value FROM config WHERE key='maintenance_mode'")
    row = cursor.fetchone()
    return row and row[0] == 'on'

def is_withdraw_enabled() -> bool:
    cursor.execute("SELECT value FROM config WHERE key='withdraw_enabled'")
    row = cursor.fetchone()
    return row and row[0] == 'on'

async def check_maintenance(user_id: int, message: types.Message = None, callback: types.CallbackQuery = None):
    """If maintenance mode is on and user is not admin, send alert and return True (blocked)."""
    if is_maintenance_mode() and not is_admin(user_id):
        text = "🔧 *Bot is under maintenance.* Please try again later."
        if callback:
            await callback.answer("Maintenance mode is ON", show_alert=True)
            await callback.message.edit_text(text, parse_mode="Markdown")
        elif message:
            await message.answer(text, parse_mode="Markdown")
        return True
    return False

# ================= FSM =================
class AdminStates(StatesGroup):
    waiting_service_name = State()
    waiting_range_val = State()
    waiting_country_code = State()
    waiting_broadcast = State()
    waiting_min_withdraw = State()
    waiting_earning_rate = State()
    waiting_add_admin = State()
    waiting_remove_admin = State()
    waiting_add_balance_id = State()
    waiting_add_balance_amount = State()
    waiting_manual_file = State()
    waiting_manual_svc_name = State()
    waiting_manual_country = State()
    waiting_manual_give_amount = State()
    waiting_manual_otp_rate = State()
    waiting_manual_cooldown = State()

class WithdrawState(StatesGroup):
    waiting_number = State()
    waiting_amount = State()

class CustomRangeState(StatesGroup):
    waiting_range_value = State()

# ================= API & OTP POLLING =================
http_session = None

async def get_session():
    global http_session
    if http_session is None:
        http_session = aiohttp.ClientSession()
    return http_session

async def poll_for_otp(chat_id: int, phones: list, duration_sec: int = 300):
    session = await get_session()
    end_time = datetime.now().timestamp() + duration_sec
    seen_ids = set()
    
    url_A = f"{API_BASE_URL}/mapi/v1/public/numsuccess/info"
    headers_A = {"mapikey": API_KEY}
    
    active_phones = list(phones)
    
    while datetime.now().timestamp() < end_time and active_phones:
        unified_logs = []
        
        try:
            async with session.get(url_A, headers=headers_A, timeout=10, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw_data = data.get("data", [])
                    logs = raw_data.get("otps", []) if isinstance(raw_data, dict) else raw_data
                    if isinstance(logs, list):
                        for log in logs:
                            unified_logs.append({
                                "id": log.get("nid", log.get("id")),
                                "phone": str(log.get("number", log.get("phone", ""))).replace("+", ""),
                                "sms": log.get("otp", log.get("sms", "")),
                                "service": log.get("operator", log.get("service", "FB"))
                            })
        except Exception: pass

        for log in unified_logs:
            base_id = log.get("id")
            phone = log.get("phone", "")
            sms = log.get("sms", "")
            
            unique_key = f"{base_id}_{sms}" if base_id else sms
            
            if unique_key in seen_ids:
                continue
            
            for p in active_phones[:]:
                p_clean = str(p).replace("+", "")
                if p_clean and (p_clean in phone or phone in p_clean):
                    seen_ids.add(unique_key)
                    
                    raw_service = log.get("service")
                    if not raw_service:
                        service = "FB"
                    else:
                        svc_upper = str(raw_service).upper().strip()
                        if "WHATSAPP" in svc_upper or "WA" in svc_upper:
                            service = "WA"
                        elif "INSTAGRAM" in svc_upper or "IG" in svc_upper:
                            service = "IG"
                        elif "TELEGRAM" in svc_upper or "TG" in svc_upper:
                            service = "TG"
                        else:
                            service = "FB"
                        
                    cursor.execute("SELECT value FROM config WHERE key='earning_per_otp'")
                    rate_row = cursor.fetchone()
                    rate_val = rate_row[0] if rate_row else "0.00"
                    
                    try:
                        cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (float(rate_val), chat_id))
                        cursor.execute("INSERT INTO otp_success_logs (user_id, timestamp) VALUES (?, ?)", (chat_id, datetime.now().isoformat()))
                        db.commit()
                    except Exception: pass

                    country_code, flag = get_country_from_phone(p)
                    
                    clean_sms = sms.replace("-", "")
                    match = re.search(r'\b\d{4,10}\b', clean_sms)
                    otp = match.group(0) if match else "Found in text"
                    
                    content = f"{flag} {country_code}➔{service}➔+৳{rate_val}"
                    border_len = len(content) + 2 
                    top_border = "╔" + "═" * border_len + "╗"
                    bottom_border = "╚" + "═" * border_len + "╝"
                    
                    text = (
                        f"{top_border}\n"
                        f"║ {content} ║\n"
                        f"{bottom_border}"
                    )
                    
                    builder = InlineKeyboardBuilder()
                    builder.row(types.InlineKeyboardButton(text=f"{flag} {p}", copy_text=CopyTextButton(text=p)))
                    builder.row(types.InlineKeyboardButton(text=f"🔑 {otp}", copy_text=CopyTextButton(text=otp)))
                    
                    await bot.send_message(chat_id, text, reply_markup=builder.as_markup(), parse_mode="Markdown")
                    break
        await asyncio.sleep(5)

async def process_manual_expiry():
    while True:
        try:
            now = time.time()
            rows = cursor.execute("SELECT id, active_manual FROM users WHERE active_manual IS NOT NULL").fetchall()
            for user_id, active_raw in rows:
                if not active_raw: continue
                active = json.loads(active_raw)
                if now - active.get("buy_time", 0) > 1200:
                    nums = active.get("nums", [])
                    cursor.execute("UPDATE users SET active_manual=NULL WHERE id=?", (user_id,))
                    svc_id = active.get("svc_id")
                    if svc_id:
                        for num in nums:
                            cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?, ?)", (svc_id, num))
                        cursor.execute("UPDATE manual_services SET stock = stock + ? WHERE id=?", (len(nums), svc_id))
                    db.commit()
                    try: await bot.send_message(user_id, "⚠️ আপনার ম্যানুয়াল নাম্বারের মেয়াদ শেষ হয়েছে।")
                    except: pass
        except Exception: pass
        await asyncio.sleep(60)

async def sync_services_from_api():
    url = f"{API_BASE_URL}/app/console"
    headers = {"mapikey": API_KEY, "Content-Type": "application/json"}
    try:
        session = await get_session()
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                api_services = []
                if isinstance(data, dict):
                    if "services" in data:
                        api_services = data["services"]
                    elif "data" in data:
                        api_services = data["data"]
                    else:
                        api_services = [data]
                elif isinstance(data, list):
                    api_services = data
                
                if api_services and isinstance(api_services, list):
                    for item in api_services:
                        name = item.get("name") or item.get("service") or item.get("title") or "Unknown"
                        rval = item.get("range") or item.get("range_val") or item.get("value") or ""
                        cc = item.get("country_code") or item.get("country") or "BD"
                        cc = cc.upper()
                        flag = get_flag_emoji(cc)
                        if not rval:
                            continue
                        cursor.execute("SELECT id FROM services WHERE range_val=?", (rval,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute("UPDATE services SET name=?, country_code=?, flag=? WHERE range_val=?", 
                                           (name, cc, flag, rval))
                        else:
                            cursor.execute("INSERT INTO services (name, range_val, country_code, flag) VALUES (?,?,?,?)", 
                                           (name, rval, cc, flag))
                    db.commit()
                    return True
    except Exception as e:
        print(f"API sync error: {e}")
    return False

async def fetch_one_number(range_val: str, attempt: int = 0):
    url = f"{API_BASE_URL}/mapi/v1/public/getnum/number"
    headers = {"mapikey": API_KEY, "Content-Type": "application/json"}
    payload = {"range": range_val}
    try:
        session = await get_session()
        async with session.post(url, json=payload, headers=headers, timeout=15, ssl=False) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, dict):
                    num_data = data.get('data', {}) if 'data' in data else data
                    num = num_data.get('full_number') or num_data.get('number') or num_data.get('phone')
                    if num:
                        return (str(num), str(num))
            elif resp.status == 405: 
                async with session.get(url, params=payload, headers={"mapikey": API_KEY}, timeout=15, ssl=False) as resp_get:
                    if resp_get.status == 200:
                        data = await resp_get.json()
                        if isinstance(data, dict):
                            num_data = data.get('data', {}) if 'data' in data else data
                            num = num_data.get('full_number') or num_data.get('number') or num_data.get('phone')
                            if num:
                                return (str(num), str(num))
        if attempt < 2:
            await asyncio.sleep(2)
            return await fetch_one_number(range_val, attempt=attempt+1)
    except Exception as e:
        if attempt < 2:
            await asyncio.sleep(2)
            return await fetch_one_number(range_val, attempt=attempt+1)
    return None

async def fetch_numbers_by_range(range_val: str, limit: int = 2):
    tasks = [fetch_one_number(range_val) for _ in range(limit)]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res is not None]

def main_menu(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📞 𝑮𝑬𝑻 𝑵𝑼𝑴𝑩𝑬𝑹"),
        types.KeyboardButton(text="💰 𝑩𝑨𝑳𝑨𝑵𝑪𝑬")
    )
    if is_admin(user_id):
        builder.row(types.KeyboardButton(text="⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳"))
    return builder.as_markup(resize_keyboard=True)

def get_grouped_services():
    cursor.execute("""
        SELECT name, flag, COUNT(*) as cnt
        FROM services
        GROUP BY name, flag
        ORDER BY name
    """)
    return cursor.fetchall()

def grouped_services_keyboard():
    groups = get_grouped_services()
    builder = InlineKeyboardBuilder()
    for name, flag, cnt in groups:
        builder.row(types.InlineKeyboardButton(
            text=f"{flag} {name} ({cnt})",
            callback_data=f"app_{name}"
        ))
    builder.row(types.InlineKeyboardButton(text="🔍 Custom Range", callback_data="custom_range"))
    builder.row(types.InlineKeyboardButton(text="🌟 Manual Numbers", callback_data="open_manual_services"))
    return builder.as_markup()

def manual_services_keyboard():
    items = cursor.execute("SELECT DISTINCT service_name FROM manual_services WHERE stock > 0").fetchall()
    builder = InlineKeyboardBuilder()
    for (svc,) in items:
        builder.row(types.InlineKeyboardButton(text=f"{svc}", callback_data=f"manual_svc_{svc}"))
    if not items: builder.row(types.InlineKeyboardButton(text="🚫 No services available", callback_data="none"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="main_menu"))
    return builder.as_markup()

def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📂 Manage Services", callback_data="manage_services")
    builder.button(text="➕ Add Service", callback_data="add_service")
    builder.button(text="🔄 Sync All Ranges", callback_data="sync_ranges")
    builder.button(text="👥 Manage Admins", callback_data="manage_admins")
    builder.button(text="📢 Broadcast", callback_data="admin_bc")
    builder.button(text="💰 Set OTP Rate", callback_data="set_earning_rate")
    builder.button(text="⚙️ Set Min Withdraw", callback_data="set_min_withdraw")
    builder.button(text="📋 Withdraw Requests", callback_data="view_withdraw_requests")
    builder.button(text="💳 Add Balance", callback_data="add_balance_btn")
    builder.button(text="🏆 Top 10 Users", callback_data="top_10_users")
    builder.button(text="👥 Total Users", callback_data="total_users")
    builder.button(text="➕ Add Manual Numbers", callback_data="add_manual_numbers")
    builder.button(text="📋 Manage Manual Num.", callback_data="manage_manual_numbers")
    
    current_w = "ON" if is_withdraw_enabled() else "OFF"
    builder.button(text=f"💸 𝑾𝑰𝑻𝑯𝑫𝑹𝑨𝑾 [{current_w}]", callback_data="toggle_withdraw")
    
    current_m = "ON" if is_maintenance_mode() else "OFF"
    builder.button(text=f"🔧 Maintenance Mode [{current_m}]", callback_data="toggle_maintenance")
    builder.button(text="🔙 Close", callback_data="close_admin_panel")
    
    builder.adjust(2)
    return builder.as_markup()

def admin_management_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="➕ Add Admin", callback_data="add_admin_btn"))
    builder.row(types.InlineKeyboardButton(text="❌ Remove Admin", callback_data="remove_admin_btn"))
    builder.row(types.InlineKeyboardButton(text="📋 List Admins", callback_data="list_admins"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    return builder.as_markup()

# ================= USER HANDLERS =================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    cursor.execute("INSERT OR IGNORE INTO users (id, username, fullname) VALUES (?, ?, ?)",
                   (message.from_user.id, message.from_user.username, message.from_user.full_name))
    db.commit()
    
    if is_maintenance_mode() and not is_admin(message.from_user.id):
        await message.answer(
            "🔧 *Bot is under maintenance.* Features are temporarily unavailable. Please try again later.",
            parse_mode="Markdown"
        )
        return
    
    user_name = message.from_user.full_name
    welcome_text = (
        f"আসসালামু আলাইকুম, **{user_name}**!! 👋\n"
        "**𝑺𝑲𝒀𝑺𝑴𝑺𝑷𝑹𝑶 𝑩𝑶𝑻**-এ আপনাকে স্বাগতম! 🚀\n\n"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu(message.from_user.id),
        parse_mode="Markdown" 
    )

@dp.message(F.text == "📞 𝑮𝑬𝑻 𝑵𝑼𝑴𝑩𝑬𝑹")
async def get_2_menu(message: types.Message):
    if await check_maintenance(message.from_user.id, message=message): return
    msg = await message.answer("⏳ 🔄 Syncing latest ranges from API...")
    await sync_services_from_api()
    await msg.delete()
    await message.answer("📱 Select an App:", reply_markup=grouped_services_keyboard())

@dp.callback_query(F.data == "open_manual_services")
async def open_manual_services(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    await callback.message.edit_text("📂 Select a Manual Service:", reply_markup=manual_services_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("app_"))
async def app_selected(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    app_name = callback.data[4:]
    cursor.execute("""
        SELECT id, name, flag, range_val
        FROM services
        WHERE name = ?
        ORDER BY range_val
    """, (app_name,))
    ranges = cursor.fetchall()
    if not ranges:
        await callback.answer("No ranges found for this app.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for sid, name, flag, rval in ranges:
        builder.row(types.InlineKeyboardButton(text=f"{flag} {name} [{rval}]", callback_data=f"service_{sid}"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="back_to_apps"))
    await callback.message.edit_text(f"📱 *{app_name}* - Select a range:", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_apps")
async def back_to_apps(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    await callback.message.edit_text("📱 Select an App:", reply_markup=grouped_services_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("service_"))
async def service_selected(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    service_id = int(callback.data.split("_")[1])
    cursor.execute("SELECT range_val FROM services WHERE id=?", (service_id,))
    row = cursor.fetchone()
    if not row:
        await callback.answer("Service not found!", show_alert=True)
        return
    await send_numbers_message(callback, row[0])

@dp.callback_query(F.data == "custom_range")
async def custom_range_prompt(callback: types.CallbackQuery, state: FSMContext):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    await callback.message.edit_text("✏️ Please send the range value (e.g., `99298XXX`):")
    await state.set_state(CustomRangeState.waiting_range_value)
    await callback.answer()

@dp.message(CustomRangeState.waiting_range_value)
async def custom_range_received(message: types.Message, state: FSMContext):
    if await check_maintenance(message.from_user.id, message=message):
        await state.clear()
        return
    range_val = message.text.strip().upper()
    if not range_val:
        await message.answer("❌ Invalid range. Please try again or /cancel.")
        return
    await send_numbers_message(message, range_val)
    await state.clear()

async def send_numbers_message(callback_or_msg, range_val: str, limit: int = 2):
    cursor.execute("SELECT name, flag, country_code FROM services WHERE range_val=?", (range_val,))
    row = cursor.fetchone()
    
    if isinstance(callback_or_msg, types.CallbackQuery):
        await callback_or_msg.answer(f"⏳ Fetching number...")
        target_message = callback_or_msg.message
    else:
        target_message = await callback_or_msg.answer("⏳ Fetching number...")
    
    numbers = await fetch_numbers_by_range(range_val, limit=limit)
    if not numbers:
        await target_message.edit_text(f"❌ Could not fetch any numbers for `{range_val}`. Please try again later.")
        return None
    
    country_map = {
        "BD": "Bangladesh", "US": "United States", "IN": "India", "MM": "Myanmar",
        "PK": "Pakistan", "RU": "Russia", "UA": "Ukraine", "GB": "United Kingdom",
        "FR": "France", "DE": "Germany", "IT": "Italy", "ES": "Spain",
        "BR": "Brazil", "AR": "Argentina", "MX": "Mexico", "ID": "Indonesia",
        "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand", "TR": "Turkey",
        "EG": "Egypt", "NG": "Nigeria", "ZA": "South Africa", "KE": "Kenya",
        "SL": "Sierra Leone", "LR": "Liberia", "GH": "Ghana", "CM": "Cameroon"
    }
    
    if row:
        name, flag, country_code = row
    else:
        name = "Custom Range"
        first_phone = numbers[0][1]
        country_code, flag = get_country_from_phone(first_phone)
        
    country_name = country_map.get(country_code, country_code)
    range_info = f"{flag} *{country_name}*➔`[{range_val}]`👀"
    
    # ইনভিজিবল স্পেস ট্রিক (হ্যাং ঠেকানোর জন্য)
    invisible_space = "\u200B" * random.randint(1, 15)
    text = f"{range_info}\n━━━━━━━━━━━━━━━━━━━━━━━\n⏳ *Waiting for OTP....*{invisible_space}"
    
    builder = InlineKeyboardBuilder()
    for idx, (nid, phone) in enumerate(numbers, 1):
        formatted = format_number_with_flag(phone)
        builder.row(types.InlineKeyboardButton(text=f" {formatted}", copy_text=CopyTextButton(text=phone)))
    
    callback_data_change = f"chg_{range_val}_{limit}"
    
    builder.row(
        types.InlineKeyboardButton(text="♻️ 𝑪𝑯𝑨𝑵𝑮𝑬", callback_data=callback_data_change),
        types.InlineKeyboardButton(text="💬 𝑮𝑬𝑻 𝑶𝑻𝑷", url=OTP_GROUP_LINK)
    )
    builder.row(types.InlineKeyboardButton(text="🔙 𝑴𝑬𝑵𝑼", callback_data="main_menu"))
    
    try: await target_message.delete()
    except Exception: pass
        
    if isinstance(callback_or_msg, types.CallbackQuery):
        sent = await callback_or_msg.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        sent = await callback_or_msg.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    phones_list = [p[1] for p in numbers]
    asyncio.create_task(poll_for_otp(sent.chat.id, phones_list, duration_sec=300))
    
    return sent

@dp.callback_query(F.data.startswith("chg_"))
async def change_number_panel(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    parts = callback.data.split("_", 2)
    range_val = parts[1]
    limit = int(parts[2])
    await send_numbers_message(callback, range_val, limit=limit)

@dp.callback_query(F.data == "main_menu")
async def cancel_all(callback: types.CallbackQuery, state: FSMContext):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    await callback.answer()
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("📍*Main Menu*📍", reply_markup=main_menu(callback.from_user.id), parse_mode="Markdown")

@dp.message(F.text == "💰 𝑩𝑨𝑳𝑨𝑵𝑪𝑬")
async def show_balance(message: types.Message):
    if await check_maintenance(message.from_user.id, message=message): return
    
    bal_row = cursor.execute("SELECT balance FROM users WHERE id=?", (message.from_user.id,)).fetchone()
    bal = bal_row[0] if bal_row else 0.0
    
    min_w_row = cursor.execute("SELECT value FROM config WHERE key='min_withdraw'").fetchone()
    min_w = min_w_row[0] if min_w_row else "100"
    
    earn_row = cursor.execute("SELECT value FROM config WHERE key='earning_per_otp'").fetchone()
    earn = earn_row[0] if earn_row else "10"
    
    text = f"💰 *Your Wallet*\n\n🏦 Balance: ৳{bal}\n⬇️ Min withdraw: ৳{min_w}\n💵 Per OTP: ৳{earn}"
    builder = InlineKeyboardBuilder()
    if is_withdraw_enabled():
        builder.row(types.InlineKeyboardButton(text="💸 𝑾𝑰𝑻𝑯𝑫𝑹𝑨𝑾", callback_data="withdraw_req"))
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "withdraw_req")
async def withdraw_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_withdraw_enabled():
        await callback.answer("❌ Withdraw is currently disabled by admin.", show_alert=True)
        return
    if await check_maintenance(callback.from_user.id, callback=callback): return
    uid = callback.from_user.id
    
    bal_row = cursor.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()
    if not bal_row:
        await callback.answer("❌ Error: User data not found. Please type /start first.", show_alert=True)
        return
    
    bal = bal_row[0]
    min_w = float(cursor.execute("SELECT value FROM config WHERE key='min_withdraw'").fetchone()[0])
    
    if bal < min_w:
        await callback.answer(f"Minimum withdraw is {min_w} TK. You have {bal} TK.", show_alert=True)
        return
        
    await callback.message.answer("✏️ Enter your bKash number (01XXXXXXXXX):")
    await state.set_state(WithdrawState.waiting_number)
    await state.update_data(user_id=uid, balance=bal)
    await callback.answer()

@dp.message(WithdrawState.waiting_number)
async def withdraw_number(message: types.Message, state: FSMContext):
    if not is_withdraw_enabled():
        await message.answer("❌ Withdraw is currently disabled by admin.")
        await state.clear()
        return
    if await check_maintenance(message.from_user.id, message=message):
        await state.clear()
        return
    num = message.text.strip()
    if not (num.isdigit() and len(num)==11 and num.startswith('01')):
        await message.answer("❌ Invalid number. Must be 11 digits starting with 01.")
        return
    await state.update_data(bkash=num)
    await message.answer("💰 How much TK do you want to withdraw?")
    await state.set_state(WithdrawState.waiting_amount)

@dp.message(WithdrawState.waiting_amount)
async def withdraw_amount(message: types.Message, state: FSMContext):
    if not is_withdraw_enabled():
        await message.answer("❌ Withdraw is currently disabled by admin.")
        await state.clear()
        return
    if await check_maintenance(message.from_user.id, message=message):
        await state.clear()
        return
    try:
        amt = float(message.text.strip())
        data = await state.get_data()
        uid = data['user_id']
        bal = data['balance']
        bkash = data['bkash']
        min_w = float(cursor.execute("SELECT value FROM config WHERE key='min_withdraw'").fetchone()[0])
        if amt <= 0 or amt > bal or amt < min_w:
            await message.answer("❌ Invalid amount.")
            return
        cursor.execute("INSERT INTO withdraw_requests (user_id, amount, bkash_number, requested_at) VALUES (?,?,?,?)",
                       (uid, amt, bkash, datetime.now().isoformat()))
        db.commit()
        await message.answer(f"✅ Withdraw request for {amt} TK submitted successfully.")
        for aid in cursor.execute("SELECT user_id FROM admins").fetchall():
            try: await bot.send_message(int(aid[0]), f"🔔 *New Withdraw Request*\n👤 User: `{uid}`\n📱 bKash: `{bkash}`\n💰 Amount: `৳{amt}`", parse_mode="Markdown")
            except: pass
    except: await message.answer("❌ Please enter a valid number.")
    finally: await state.clear()

# ================= ADMIN PANEL =================
@dp.message(F.text == "⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳")
async def admin_panel_button(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ You are not an admin.")
        return
    await message.answer("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.message(Command("admin"))
async def admin_main(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "add_balance_btn")
async def add_balance_btn(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("✏️ Enter the User ID to add balance:")
    await state.set_state(AdminStates.waiting_add_balance_id)
    await callback.answer()

@dp.message(AdminStates.waiting_add_balance_id)
async def add_balance_id(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("❌ Invalid User ID. Must be numeric.")
        return
    cursor.execute("SELECT id FROM users WHERE id=?", (uid,))
    if not cursor.fetchone():
        await message.answer("❌ User not found in database.")
        await state.clear()
        return
    await state.update_data(add_bal_id=uid)
    await message.answer("💰 Enter the amount of TK to add:")
    await state.set_state(AdminStates.waiting_add_balance_amount)

@dp.message(AdminStates.waiting_add_balance_amount)
async def add_balance_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        amt = float(message.text.strip())
        data = await state.get_data()
        uid = data['add_bal_id']
        cursor.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amt, uid))
        db.commit()
        await message.answer(f"✅ Successfully added `৳{amt}` to User `{uid}`.", parse_mode="Markdown")
        try: await bot.send_message(uid, f"🎁 *Congratulations!*\nAdmin has added `৳{amt}` to your wallet.\nCheck your /start -> Balance.", parse_mode="Markdown")
        except: pass
    except ValueError: await message.answer("❌ Invalid amount.")
    finally:
        await state.clear()
        await admin_main(message)

@dp.callback_query(F.data == "top_10_users")
async def show_top_10_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    try:
        cursor.execute("DELETE FROM otp_success_logs WHERE timestamp < ?", (thirty_days_ago,))
        db.commit()
    except: pass
        
    cursor.execute("""
        SELECT u.fullname, u.username, COUNT(o.id) as otp_count
        FROM otp_success_logs o
        JOIN users u ON o.user_id = u.id
        WHERE o.timestamp >= ?
        GROUP BY o.user_id
        ORDER BY otp_count DESC
        LIMIT 10
    """, (thirty_days_ago,))
    
    rows = cursor.fetchall()
    
    if not rows: text = "🏆 *Top 10 Users (Last 30 Days)*\n\nকোনো ইউজারের সফল OTP হিস্ট্রি পাওয়া যায়নি।"
    else:
        text = "🏆 *Top 10 Users (Last 30 Days)*\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for idx, row in enumerate(rows):
            fullname = row[0] or "Unknown"
            username = f"(@{row[1]})" if row[1] else ""
            count = row[2]
            rank = medals[idx] if idx < 3 else f"`{idx+1}.`"
            text += f"{rank} {fullname} {username} - `{count} OTP`\n"
            
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "total_users")
async def show_total_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    cursor.execute("SELECT COUNT(id) FROM users")
    count = cursor.fetchone()[0]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    await callback.message.edit_text(f"👥 *Total Registered Users:* `{count}`", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "manage_services")
async def manage_services(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    rows = cursor.execute("SELECT id, name, flag, range_val FROM services").fetchall()
    if not rows:
        await callback.message.edit_text("No services found.")
        return
    builder = InlineKeyboardBuilder()
    for sid, name, flag, rval in rows:
        builder.row(types.InlineKeyboardButton(text=f"🗑️ Delete: {flag} {name} [{rval}]", callback_data=f"del_srv_{sid}"))
    builder.row(types.InlineKeyboardButton(text="➕ Add Service", callback_data="add_service"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    await callback.message.edit_text("📂 *Service List* (Click to delete):", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "add_service")
async def add_service_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("✏️ Enter Service Name (e.g. Telegram, WhatsApp):")
    await state.set_state(AdminStates.waiting_service_name)
    await callback.answer()

@dp.message(AdminStates.waiting_service_name)
async def add_svc_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(name=message.text.strip())
    await message.answer("✏️ Enter Range Value (e.g., 99298XXX):")
    await state.set_state(AdminStates.waiting_range_val)

@dp.message(AdminStates.waiting_range_val)
async def add_svc_range(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(range_val=message.text.strip())
    await message.answer("✏️ Enter Country Code (2 letters, e.g., BD, US, IN):")
    await state.set_state(AdminStates.waiting_country_code)

@dp.message(AdminStates.waiting_country_code)
async def add_svc_country(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    cc = message.text.strip().upper()
    if len(cc) != 2:
        await message.answer("❌ Invalid code. Must be exactly 2 letters.")
        return
    data = await state.get_data()
    flag = get_flag_emoji(cc)
    cursor.execute("INSERT INTO services (name, range_val, country_code, flag) VALUES (?,?,?,?)",
                   (data['name'], data['range_val'], cc, flag))
    db.commit()
    await message.answer(f"✅ {flag} *{data['name']}* added successfully.", parse_mode="Markdown")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "sync_ranges")
async def sync_ranges_cb(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    await callback.message.edit_text("⏳ 🔄 Syncing ranges from API...")
    success = await sync_services_from_api()
    if success: await callback.message.edit_text("✅ Ranges synced successfully.")
    else: await callback.message.edit_text("❌ Sync failed. Check connection.")
    await asyncio.sleep(2)
    await callback.message.edit_text("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("del_srv_"))
async def delete_service(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    sid = int(callback.data.split("_")[-1])
    cursor.execute("DELETE FROM services WHERE id=?", (sid,))
    db.commit()
    await callback.answer("✅ Service deleted successfully.", show_alert=True)
    await manage_services(callback)

@dp.callback_query(F.data == "manage_admins")
async def manage_admins_menu(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("👥 *Admin Management*:", reply_markup=admin_management_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "add_admin_btn")
async def add_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("✏️ Enter the User ID to add as Admin:")
    await state.set_state(AdminStates.waiting_add_admin)
    await callback.answer()

@dp.message(AdminStates.waiting_add_admin)
async def add_admin(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    if not uid.isdigit():
        await message.answer("❌ Invalid ID. Please enter a numeric user ID.")
        return
    cursor.execute("INSERT OR IGNORE INTO admins VALUES (?)", (uid,))
    db.commit()
    await message.answer(f"✅ User `{uid}` is now an admin.", parse_mode="Markdown")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "remove_admin_btn")
async def remove_admin_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("✏️ Enter the User ID to remove from Admins:")
    await state.set_state(AdminStates.waiting_remove_admin)
    await callback.answer()

@dp.message(AdminStates.waiting_remove_admin)
async def remove_admin(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    uid = message.text.strip()
    if uid == str(message.from_user.id):
        await message.answer("❌ You cannot remove yourself.")
        return
    cursor.execute("DELETE FROM admins WHERE user_id=?", (uid,))
    db.commit()
    await message.answer(f"✅ User `{uid}` is no longer an admin.", parse_mode="Markdown")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "list_admins")
async def list_admins(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    rows = cursor.execute("SELECT user_id FROM admins").fetchall()
    if not rows: text = "No admins found."
    else:
        text = "👥 *Current Admins:*\n\n"
        for (uid,) in rows: text += f"• `{uid}`\n"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="manage_admins"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "admin_bc")
async def bc_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("✏️ Enter broadcast message (Markdown supported):")
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.answer()

@dp.message(AdminStates.waiting_broadcast)
async def bc_send(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    text = message.text
    users = cursor.execute("SELECT id FROM users").fetchall()
    success = 0
    await message.answer("⏳ Sending broadcast...")
    for (uid,) in users:
        try:
            await bot.send_message(uid[0], f"📢 *Broadcast Message*\n\n{text}", parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Broadcast sent successfully to {success} users.")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "set_earning_rate")
async def rate_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    current_row = cursor.execute("SELECT value FROM config WHERE key='earning_per_otp'").fetchone()
    current = current_row[0] if current_row else "10"
    await callback.message.edit_text(f"✏️ Enter new earning amount per OTP (Current: ৳{current}):")
    await state.set_state(AdminStates.waiting_earning_rate)
    await callback.answer()

@dp.message(AdminStates.waiting_earning_rate)
async def rate_save(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        rate = float(message.text.strip())
        if rate < 0: raise ValueError
        cursor.execute("UPDATE config SET value=? WHERE key='earning_per_otp'", (str(rate),))
        db.commit()
        await message.answer(f"✅ Rate successfully set to ৳{rate} per OTP.")
    except: await message.answer("❌ Invalid number.")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "set_min_withdraw")
async def minwd_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    current_row = cursor.execute("SELECT value FROM config WHERE key='min_withdraw'").fetchone()
    current = current_row[0] if current_row else "100"
    await callback.message.edit_text(f"✏️ Enter new minimum withdraw amount (Current: ৳{current}):")
    await state.set_state(AdminStates.waiting_min_withdraw)
    await callback.answer()

@dp.message(AdminStates.waiting_min_withdraw)
async def minwd_save(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        m = float(message.text.strip())
        if m < 0: raise ValueError
        cursor.execute("UPDATE config SET value=? WHERE key='min_withdraw'", (str(m),))
        db.commit()
        await message.answer(f"✅ Minimum withdraw amount set to ৳{m}.")
    except: await message.answer("❌ Invalid number.")
    await state.clear()
    await admin_main(message)

@dp.callback_query(F.data == "view_withdraw_requests")
async def view_wd(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    rows = cursor.execute("SELECT id, user_id, amount, bkash_number, requested_at FROM withdraw_requests WHERE status='pending' ORDER BY requested_at DESC").fetchall()
    if not rows:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
        await callback.message.edit_text("📭 No pending withdraw requests.", reply_markup=builder.as_markup())
        return
    await callback.message.delete()
    for req in rows:
        rid, uid, amt, bkash, tm = req
        uname_row = cursor.execute("SELECT username FROM users WHERE id=?", (uid,)).fetchone()
        uname = uname_row[0] if uname_row and uname_row[0] else "N/A"
        text = f"📋 *Request #{rid}*\n👤 User ID: `{uid}` (@{uname})\n💰 Amount: `৳{amt}`\n📱 bKash: `{bkash}`\n🕒 Time: {tm}"
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_wd_{rid}"), 
            types.InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_wd_{rid}")
        )
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    back = InlineKeyboardBuilder()
    back.row(types.InlineKeyboardButton(text="🔙 Back to Admin Panel", callback_data="admin_back"))
    await callback.message.answer("All pending requests listed above.", reply_markup=back.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("approve_wd_"))
async def approve_wd(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    rid = int(callback.data.split("_")[-1])
    row = cursor.execute("SELECT user_id, amount, status FROM withdraw_requests WHERE id=?", (rid,)).fetchone()
    if not row or row[2] != "pending":
        await callback.answer("Request not found or already processed.", show_alert=True)
        return
    uid, amt, _ = row
    bal = cursor.execute("SELECT balance FROM users WHERE id=?", (uid,)).fetchone()[0]
    if bal < amt:
        cursor.execute("UPDATE withdraw_requests SET status='rejected' WHERE id=?", (rid,))
        db.commit()
        try: await bot.send_message(uid, f"❌ Your withdrawal of ৳{amt} was rejected due to insufficient balance.")
        except: pass
        await callback.answer("User balance is too low. Rejected automatically.", show_alert=True)
        await callback.message.edit_text(f"❌ Request #{rid} Auto-Rejected (Low Balance).")
        return
    new_bal = bal - amt
    cursor.execute("UPDATE users SET balance=? WHERE id=?", (new_bal, uid))
    cursor.execute("UPDATE withdraw_requests SET status='approved' WHERE id=?", (rid,))
    db.commit()
    try: await bot.send_message(uid, f"✅ *Congratulations!*\nYour withdrawal request for `৳{amt}` has been approved and sent to your bKash number.\n🏦 Current Balance: `৳{new_bal}`", parse_mode="Markdown")
    except: pass
    await callback.answer("Successfully Approved!", show_alert=True)
    await callback.message.edit_text(f"✅ Request #{rid} has been *Approved*.", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("reject_wd_"))
async def reject_wd(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    rid = int(callback.data.split("_")[-1])
    row = cursor.execute("SELECT user_id, amount FROM withdraw_requests WHERE id=? AND status='pending'", (rid,)).fetchone()
    if not row:
        await callback.answer("Request not found or already processed.", show_alert=True)
        return
    uid, amt = row
    cursor.execute("UPDATE withdraw_requests SET status='rejected' WHERE id=?", (rid,))
    db.commit()
    try: await bot.send_message(uid, f"❌ Your withdrawal request for ৳{amt} has been rejected by the Admin.")
    except: pass
    await callback.answer("Request Rejected!", show_alert=True)
    await callback.message.edit_text(f"❌ Request #{rid} has been *Rejected*.", parse_mode="Markdown")

@dp.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    await callback.message.edit_text("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "close_admin_panel")
async def close_admin_panel(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    await callback.answer()
    await callback.message.delete()

@dp.callback_query(F.data == "toggle_maintenance")
async def toggle_maintenance(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized!", show_alert=True)
        return
    current = is_maintenance_mode()
    new_value = "off" if current else "on"
    cursor.execute("UPDATE config SET value=? WHERE key='maintenance_mode'", (new_value,))
    db.commit()
    status_text = "ON" if new_value == "on" else "OFF"
    await callback.answer(f"Maintenance mode turned {status_text}", show_alert=True)
    await callback.message.edit_text("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "toggle_withdraw")
async def toggle_withdraw(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized!", show_alert=True)
        return
    current = is_withdraw_enabled()
    new_value = "off" if current else "on"
    cursor.execute("UPDATE config SET value=? WHERE key='withdraw_enabled'", (new_value,))
    db.commit()
    status_text = "ON" if new_value == "on" else "OFF"
    await callback.answer(f"Withdraw mode turned {status_text}", show_alert=True)
    await callback.message.edit_text("⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳", reply_markup=admin_menu(), parse_mode="Markdown")

# ================= MANUAL NUMBER ADMIN =================
@dp.callback_query(F.data == "add_manual_numbers")
async def add_manual_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id): return
    await callback.message.edit_text("📂 Send a .txt file with one phone number per line:")
    await state.set_state(AdminStates.waiting_manual_file)
    await callback.answer()

@dp.message(AdminStates.waiting_manual_file, F.document)
async def manual_file_received(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    doc = message.document
    if not doc.file_name.endswith('.txt'):
        await message.answer("❌ Only .txt files accepted.")
        return
    try:
        file = await bot.get_file(doc.file_id)
        downloaded = await bot.download_file(file.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
    except Exception as e:
        await message.answer(f"❌ File read error: {e}")
        await state.clear()
        return

    numbers = [line.strip() for line in content.strip().split('\n') if line.strip()]
    if not numbers:
        await message.answer("No valid numbers found.")
        await state.clear()
        return
    await state.update_data(manual_numbers=numbers)
    await message.answer("✏️ Enter service name (e.g., WhatsApp):")
    await state.set_state(AdminStates.waiting_manual_svc_name)

@dp.message(AdminStates.waiting_manual_svc_name)
async def manual_svc_name(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(manual_svc=message.text.strip())
    await message.answer("🌍 Enter country name (e.g., Bangladesh):")
    await state.set_state(AdminStates.waiting_manual_country)

@dp.message(AdminStates.waiting_manual_country)
async def manual_country(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    await state.update_data(manual_country=message.text.strip())
    await message.answer("🔢 How many numbers to give per click? (e.g. 1):")
    await state.set_state(AdminStates.waiting_manual_give_amount)

@dp.message(AdminStates.waiting_manual_give_amount)
async def manual_give_amount(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        give = int(message.text)
        if give < 1: raise ValueError
    except ValueError:
        await message.answer("❌ Enter a positive number.")
        return
    await state.update_data(manual_give=give)
    await message.answer("💰 Set reward/earning per OTP for this service (৳):")
    await state.set_state(AdminStates.waiting_manual_otp_rate)

@dp.message(AdminStates.waiting_manual_otp_rate)
async def manual_otp_rate(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        rate = float(message.text)
        if rate < 0: raise ValueError
    except ValueError:
        await message.answer("❌ Invalid rate.")
        return
    await state.update_data(manual_rate=rate)
    await message.answer("⏱ Enter Cooldown Time for users (in seconds, e.g. 60 for 1 min):")
    await state.set_state(AdminStates.waiting_manual_cooldown)

@dp.message(AdminStates.waiting_manual_cooldown)
async def manual_cooldown_save(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        cooldown = int(message.text)
        if cooldown < 0: raise ValueError
    except ValueError:
        await message.answer("❌ Enter a valid number for seconds.")
        return

    data = await state.get_data()
    svc, country, give, numbers = data['manual_svc'], data['manual_country'], data['manual_give'], data['manual_numbers']
    rate = data['manual_rate']
    flag = get_country_from_phone(numbers[0])[1] if numbers else "🌍"
    
    cursor.execute("INSERT INTO manual_services (service_name, country_name, flag, give_amount, otp_rate, stock, cooldown) VALUES (?,?,?,?,?,?,?)",
                   (svc, country, flag, give, rate, len(numbers), cooldown))
    svc_id = cursor.lastrowid
    for num in numbers:
        cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?,?)", (svc_id, num))
    db.commit()
    
    text = f"✅ Added {len(numbers)} numbers to {svc} - {country} with {cooldown}s cooldown and ৳{rate} reward.\n\nDo you want to broadcast this to users?"
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Broadcast", callback_data=f"m_bc_{svc_id}")
    builder.button(text="❌ Close", callback_data="close_admin_panel")
    
    await message.answer(text, reply_markup=builder.as_markup())
    await state.clear()

@dp.callback_query(F.data.startswith("m_bc_"))
async def broadcast_manual_addition(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    svc_id = int(callback.data.split("_")[2])
    svc_row = cursor.execute("SELECT service_name, country_name, flag, otp_rate, stock FROM manual_services WHERE id=?", (svc_id,)).fetchone()
    if not svc_row:
        await callback.answer("Service not found.", show_alert=True)
        return
    svc, country, flag, rate, stock = svc_row
    
    bc_text = (
        f"🔥 **𝙽𝙴𝚆 𝙽𝚄𝙼𝙱𝙴𝚁𝚂 𝙰𝙳𝙳𝙴𝙳** 🔥\n\n"
        f"📂 **Service:** {svc}\n"
        f"🌍 **Country:** {flag} {country}\n"
        f"💰 **Reward:** ৳{rate} per OTP\n"
        f"📊 **Stock Added:** {stock} numbers\n\n"
        f"🚀 Go to **📞 𝑮𝑬𝑻 𝑵𝑼𝑴𝑩𝑬𝑹** and grab yours now!"
    )
    
    await callback.message.edit_text("⏳ Sending broadcast...")
    users = cursor.execute("SELECT id FROM users").fetchall()
    success = 0
    for (uid,) in users:
        try:
            await bot.send_message(uid[0], bc_text, parse_mode="Markdown")
            success += 1
            await asyncio.sleep(0.05)
        except: pass
    await callback.message.edit_text(f"✅ Broadcast sent successfully to {success} users.")

@dp.callback_query(F.data == "manage_manual_numbers")
async def manage_manual_numbers(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    services = cursor.execute("SELECT id, service_name, country_name, stock FROM manual_services").fetchall()
    if not services:
        await callback.answer("No manual services.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for svc_id, svc, country, stock in services:
        builder.row(types.InlineKeyboardButton(text=f"🗑 {svc} - {country} ({stock} left)", callback_data=f"del_manual_{svc_id}"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="admin_back"))
    await callback.message.edit_text("📋 Manual services - click to delete:", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("del_manual_"))
async def delete_manual_service(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    svc_id = int(callback.data[11:])
    cursor.execute("DELETE FROM manual_numbers WHERE service_id=?", (svc_id,))
    cursor.execute("DELETE FROM manual_services WHERE id=?", (svc_id,))
    db.commit()
    await callback.answer("Deleted.", show_alert=True)
    await manage_manual_numbers(callback)


# ================= MANUAL NUMBER USER FLOW =================
@dp.callback_query(F.data.startswith("manual_svc_"))
async def manual_svc_selected(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    svc_name = callback.data[11:]
    
    countries = cursor.execute("SELECT id, country_name, flag FROM manual_services WHERE service_name=? AND stock > 0", (svc_name,)).fetchall()
    if not countries:
        await callback.answer("No countries available for this service.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for svc_id, c_name, flag in countries:
        builder.row(types.InlineKeyboardButton(text=f"{flag} {c_name}", callback_data=f"man_cntry_{svc_id}"))
    builder.row(types.InlineKeyboardButton(text="🔙 Back", callback_data="open_manual_services"))
    await callback.message.edit_text(f"🌍 Select country for *{svc_name}*:", reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("man_cntry_"))
async def manual_country_selected(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    svc_id = int(callback.data[10:])
    uid = callback.from_user.id
    
    svc_row = cursor.execute("SELECT service_name, country_name, give_amount, otp_rate, stock, flag, cooldown FROM manual_services WHERE id=? AND stock > 0", (svc_id,)).fetchone()
    if not svc_row:
        await callback.answer("Service not available.", show_alert=True)
        return
    svc_name, c_name, give_amount, otp_rate, stock, flag, cooldown = svc_row

    user_cd_raw = cursor.execute("SELECT manual_cooldowns FROM users WHERE id=?", (uid,)).fetchone()
    user_cds = json.loads(user_cd_raw[0]) if user_cd_raw and user_cd_raw[0] else {}
    last_time = user_cds.get(str(svc_id), 0)
    
    if time.time() - last_time < cooldown:
        wait_sec = int(cooldown - (time.time() - last_time))
        await callback.answer(f"⏳ আপনি {wait_sec} সেকেন্ড পর নাম্বার নিতে পারবেন।", show_alert=True)
        return
    
    nums_rows = cursor.execute("SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?", (svc_id, give_amount)).fetchall()
    nums = [r[0] for r in nums_rows]
    if len(nums) < give_amount:
        await callback.answer("Not enough numbers in stock.", show_alert=True)
        return
        
    cursor.execute("DELETE FROM manual_numbers WHERE service_id=? AND number IN ({})".format(','.join('?'*len(nums))), (svc_id, *nums))
    cursor.execute("UPDATE manual_services SET stock = stock - ? WHERE id=?", (give_amount, svc_id))
    
    active_data = json.dumps({"svc_id": svc_id, "svc": svc_name, "c": c_name, "nums": nums, "rate": otp_rate, "buy_time": time.time()})
    user_cds[str(svc_id)] = time.time()
    
    cursor.execute("UPDATE users SET active_manual=?, manual_cooldowns=? WHERE id=?", (active_data, json.dumps(user_cds), uid))
    db.commit()
    
    invisible_space = "\u200B" * random.randint(1, 15)
    text = (f"🌐 <b>Country:</b> {flag} {c_name}\n💸 <b>Reward:</b> +৳{otp_rate} (Per OTP)\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"╔══════════════════════════╗\n║  ⏳ <i>Waiting for OTP...</i>  ║\n╚══════════════════════════╝{invisible_space}")
    
    builder = InlineKeyboardBuilder()
    for num in nums: builder.row(types.InlineKeyboardButton(text=f"📄 {num}", copy_text=CopyTextButton(text=num)))
    builder.row(types.InlineKeyboardButton(text="♻️ 𝑪𝑯𝑨𝑵𝑮𝑬 𝑵𝑼𝑴𝑩𝑬𝑹", callback_data=f"man_change_{svc_id}"), types.InlineKeyboardButton(text="🌍 𝑪𝑯𝑨𝑵𝑮𝑬 𝑪𝑶𝑼𝑵𝑻𝑹𝒀", callback_data=f"manual_svc_{svc_name}"))
    builder.row(types.InlineKeyboardButton(text="💬 𝑶𝑻𝑷 𝑮𝑹𝑶𝑼𝑷", url=OTP_GROUP_LINK))
    
    try: await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except: await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    asyncio.create_task(poll_for_otp(uid, nums, duration_sec=1200, is_manual=True))

@dp.callback_query(F.data.startswith("man_change_"))
async def man_change_numbers(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback): return
    svc_id = int(callback.data[11:])
    uid = callback.from_user.id
    
    active_row = cursor.execute("SELECT active_manual FROM users WHERE id=?", (uid,)).fetchone()
    if not active_row or not active_row[0]:
        await callback.answer("No active manual numbers to change.", show_alert=True)
        return
    
    active = json.loads(active_row[0])
    if active.get("svc_id") != svc_id:
        await callback.answer("Cannot change different service.", show_alert=True)
        return
    
    svc_row = cursor.execute("SELECT service_name, country_name, give_amount, otp_rate, flag, cooldown FROM manual_services WHERE id=?", (svc_id,)).fetchone()
    if not svc_row:
        await callback.answer("Service not found.", show_alert=True)
        return
    svc_name, c_name, give_amount, otp_rate, flag, cooldown = svc_row

    user_cd_raw = cursor.execute("SELECT manual_cooldowns FROM users WHERE id=?", (uid,)).fetchone()
    user_cds = json.loads(user_cd_raw[0]) if user_cd_raw and user_cd_raw[0] else {}
    last_time = user_cds.get(str(svc_id), 0)
    
    elapsed = time.time() - last_time
    if elapsed < cooldown:
        wait_sec = int(cooldown - elapsed)
        await callback.answer(f"⏳ আপনি {wait_sec} সেকেন্ড পর নাম্বার চেঞ্জ করতে পারবেন।", show_alert=True)
        return

    old_nums = active.get("nums", [])
    
    if old_nums:
        for num in old_nums:
            cursor.execute("INSERT INTO manual_numbers (service_id, number) VALUES (?, ?)", (svc_id, num))
            
    if old_nums:
        placeholders = ','.join('?' * len(old_nums))
        query = f"SELECT number FROM manual_numbers WHERE service_id=? AND number NOT IN ({placeholders}) ORDER BY RANDOM() LIMIT ?"
        params = [svc_id] + old_nums + [give_amount]
    else:
        query = "SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?"
        params = [svc_id, give_amount]
        
    new_nums_rows = cursor.execute(query, params).fetchall()
    new_nums = [r[0] for r in new_nums_rows]

    if len(new_nums) < give_amount:
        query = "SELECT number FROM manual_numbers WHERE service_id=? ORDER BY RANDOM() LIMIT ?"
        params = [svc_id, give_amount]
        new_nums_rows = cursor.execute(query, params).fetchall()
        new_nums = [r[0] for r in new_nums_rows]

    if len(new_nums) < give_amount:
        await callback.answer("স্টকে আর কোনো নাম্বার নেই!", show_alert=True)
        cursor.execute("UPDATE users SET active_manual=NULL WHERE id=?", (uid,))
        db.commit()
        return
        
    cursor.execute("DELETE FROM manual_numbers WHERE service_id=? AND number IN ({})".format(','.join('?'*len(new_nums))), (svc_id, *new_nums))
    
    active["nums"] = new_nums
    active["buy_time"] = time.time()
    
    user_cds[str(svc_id)] = time.time()
    cursor.execute("UPDATE users SET active_manual=?, manual_cooldowns=? WHERE id=?", (json.dumps(active), json.dumps(user_cds), uid))
    db.commit()
    
    invisible_space = "\u200B" * random.randint(1, 15)
    text = (f"🌐 <b>Country:</b> {flag} {c_name}\n💸 <b>Reward:</b> +৳{otp_rate} (Per OTP)\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"╔══════════════════════════╗\n║  ⏳ <i>Waiting for OTP...</i>  ║\n╚══════════════════════════╝{invisible_space}")
    
    builder = InlineKeyboardBuilder()
    for num in new_nums: builder.row(types.InlineKeyboardButton(text=f"📄 {num}", copy_text=CopyTextButton(text=num)))
    builder.row(types.InlineKeyboardButton(text="♻️ 𝑪𝑯𝑨𝑵𝑮𝑬 𝑵𝑼𝑴𝑩𝑬𝑹", callback_data=f"man_change_{svc_id}"), types.InlineKeyboardButton(text="🌍 𝑪𝑯𝑨𝑵𝑮𝑬 𝑪𝑶𝑼𝑵𝑻𝑹𝒀", callback_data=f"manual_svc_{svc_name}"))
    builder.row(types.InlineKeyboardButton(text="💬 𝑶𝑻𝑷 𝑮𝑹𝑶𝑼𝑷", url=OTP_GROUP_LINK))
    
    try: 
        await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    except Exception: 
        try: await callback.message.delete()
        except: pass
        await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        
    await callback.answer("নাম্বার সফলভাবে পরিবর্তন হয়েছে!", show_alert=False)
    asyncio.create_task(poll_for_otp(uid, new_nums, duration_sec=1200, is_manual=True))

# ================= AUTO RANGE DETECTION =================
RANGE_PATTERN = re.compile(r'[\+]?(\d{5,12}[Xx]{2,5})')

def extract_range_from_text(text: str) -> str:
    match = RANGE_PATTERN.search(text)
    if match:
        range_val = match.group(1).upper().replace('X', 'X')
        if range_val.startswith('+'):
            range_val = range_val[1:]
        return range_val
    return None

@dp.message()
async def auto_detect_range(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        return
    
    if message.text and message.text.startswith('/'):
        return
    
    if message.text in ["📞 𝑮𝑬𝑻 𝑵𝑼𝑴𝑩𝑬𝑹", "💰 𝑩𝑨𝑳𝑨𝑵𝑪𝑬", "⚙️ 𝑨𝑫𝑴𝑰𝑵 𝑷𝑨𝑵𝑬𝑳"]:
        return
    
    text_to_check = message.text or message.caption or ""
    if not text_to_check:
        return
    
    if await check_maintenance(message.from_user.id, message=message):
        return
    
    range_val = extract_range_from_text(text_to_check)
    if not range_val:
        return
    
    # আপনার রিকোয়েস্ট মতো ইউজার রেঞ্জ দিলে তার মেসেজ ডিলিট করে দেওয়া হলো
    try:
        await message.delete()
    except Exception:
        pass
    
    await send_numbers_message(message, range_val)

async def send_numbers_message(callback_or_msg, range_val: str, limit: int = 2):
    cursor.execute("SELECT name, flag, country_code FROM services WHERE range_val=?", (range_val,))
    row = cursor.fetchone()
    
    if isinstance(callback_or_msg, types.CallbackQuery):
        await callback_or_msg.answer(f"⏳ Fetching number...")
        target_message = callback_or_msg.message
    else:
        target_message = await callback_or_msg.answer("⏳ Fetching number...")
    
    numbers = await fetch_numbers_by_range(range_val, limit=limit)
    if not numbers:
        await target_message.edit_text(f"❌ Could not fetch any numbers for `{range_val}`. Please try again later.")
        return None
    
    country_map = {
        "BD": "Bangladesh", "US": "United States", "IN": "India", "MM": "Myanmar",
        "PK": "Pakistan", "RU": "Russia", "UA": "Ukraine", "GB": "United Kingdom",
        "FR": "France", "DE": "Germany", "IT": "Italy", "ES": "Spain",
        "BR": "Brazil", "AR": "Argentina", "MX": "Mexico", "ID": "Indonesia",
        "PH": "Philippines", "VN": "Vietnam", "TH": "Thailand", "TR": "Turkey",
        "EG": "Egypt", "NG": "Nigeria", "ZA": "South Africa", "KE": "Kenya",
        "SL": "Sierra Leone", "LR": "Liberia", "GH": "Ghana", "CM": "Cameroon"
    }
    
    if row:
        name, flag, country_code = row
    else:
        name = "Custom Range"
        first_phone = numbers[0][1]
        country_code, flag = get_country_from_phone(first_phone)
        
    country_name = country_map.get(country_code, country_code)
    
    invisible_space = "\u200B" * random.randint(1, 15)
    range_info = f"{flag} *{country_name}*➔`[{range_val}]`👀"
    text = f"{range_info}\n━━━━━━━━━━━━━━━━━━━━━━━\n⏳ *Waiting for OTP....*{invisible_space}"
    
    builder = InlineKeyboardBuilder()
    for idx, (nid, phone) in enumerate(numbers, 1):
        formatted = format_number_with_flag(phone)
        builder.row(types.InlineKeyboardButton(
            text=f" {formatted}",
            copy_text=CopyTextButton(text=phone)
        ))
    
    callback_data_change = f"chg_range_{range_val}_{limit}"
    
    builder.row(
        types.InlineKeyboardButton(text="♻️ 𝑪𝑯𝑨𝑵𝑮𝑬", callback_data=callback_data_change),
        types.InlineKeyboardButton(text="💬 𝑮𝑬𝑻 𝑶𝑻𝑷", url=OTP_GROUP_LINK)
    )
    builder.row(
        types.InlineKeyboardButton(text="🔙 𝑴𝑬𝑵𝑼", callback_data="main_menu")
    )
    
    try:
        await target_message.delete()
    except Exception:
        pass
        
    if isinstance(callback_or_msg, types.CallbackQuery):
        sent = await callback_or_msg.message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    else:
        sent = await callback_or_msg.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    
    phones_list = [p[1] for p in numbers]
    asyncio.create_task(poll_for_otp(sent.chat.id, phones_list, duration_sec=300))
    
    return sent

@dp.callback_query(F.data.startswith("chg_"))
async def change_number_panel(callback: types.CallbackQuery):
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    parts = callback.data.split("_", 3)
    if parts[1] == "range":
        range_val = parts[2]
        limit = int(parts[3])
        await send_numbers_message(callback, range_val, limit=limit)

@dp.callback_query(F.data == "main_menu")
async def cancel_all(callback: types.CallbackQuery, state: FSMContext):
    if await check_maintenance(callback.from_user.id, callback=callback):
        return
    await callback.answer()
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "📍*Main Menu*📍",
        reply_markup=main_menu(callback.from_user.id),
        parse_mode="Markdown"
    )

# ================= SHUTDOWN CLEANUP =================
async def on_shutdown():
    global http_session
    if http_session:
        await http_session.close()

dp.shutdown.register(on_shutdown)

# ================= STARTUP =================
async def on_startup():
    asyncio.create_task(master_otp_fetcher())

dp.startup.register(on_startup)

# ================= MAIN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
