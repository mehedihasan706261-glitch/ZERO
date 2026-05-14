import asyncio
import logging
import re
import json
import random
from collections import deque
import aiohttp

# ======================== টেলিগ্রাম কনফিগারেশন ========================
TELEGRAM_TOKEN = "8647348457:AAEi5Kre2Df4Xeig80aZzsd_7zR9MFO739Y"
TELEGRAM_CHAT_ID = "-1003860008126"

# ======================== 1. রিয়েল API কনফিগারেশন (API Key) ========================
REAL_API_URL = "https://x.mnitnetwork.com/mapi/v1/public/numsuccess/info"
REAL_API_KEY = "M_A4UFFVM8R"
REAL_HEADERS = {
    "mapikey": REAL_API_KEY,
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ======================== 2. কনসোল API কনফিগারেশন (Cookie/Token) ========================
CONSOLE_API_URL = "https://x.mnitnetwork.com/mapi/v1/mdashboard/console/info"
CONSOLE_MAUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJNX0k0VkE3RkU2UiIsInJvbGUiOiJ1c2VyIiwiYWNjZXNzX3BhdGgiOlsiL2Rhc2hib2FyZCJdLCJleHBpcnkiOjE3Nzg3NzI2OTgsImNyZWF0ZWQiOjE3Nzg2ODYyOTgsIjJvbzkiOiJNc0giLCJleHAiOjE3Nzg3NzI2OTgsImlhdCI6MTc3ODY4NjI5OCwic3ViIjoiTV9JNFZBN0ZFNlIifQ.qJz3Gy7o1FEbUztRw4kLQ5BCvdFnPrsf38nIMRppuvU"
CONSOLE_COOKIE = "twk_uuid_681787a55d55ef191a9da720=%7B%22uuid%22%3A%221.Ws5rtI1DBXbfg9clSSSnihv47mLuGJSa2VyRZk2db9EAJnufdxbwP2izEkQtS2oEDxi8dbdNAteM8CrelxX9WMdm12gPCxyGtlkVkx4UG5gpvy3hMsRwMJAI4%22%2C%22version%22%3A3%2C%22domain%22%3A%22mnitnetwork.com%22%2C%22ts%22%3A1778349703415%7D; cf_clearance=YsQCKQ24g9l2p7Fb2k.QLnZxh577O95vsCIkl8ZjFQA-1778686295-1.2.1.1-LpaFrqq3182kexzYl1Ja4qA8AUhXnw2iaJkGWw3OJsJQoHEEOh9M0WsECNAJg7Z_6C6IusJCntzEO7Qx_xv9jTkuO8kDFkcLDJF9UYm8JjqqWfvi9zq1JOTd_pGgMSm0ZctkYk8H1L9Sae540Wh1Vsct1vXS3W9AiZN_545hN9zvPqp5SMao03kkXVMekm7vxg8wBvh5ktSBlNDUz7K0DAOVfaNkokssE2lUNMaHovmi12SRZp6jflmCg9zv5pnDuUJcAiJ0BBZFpESg1bF5xx7gih3jacGA0Y04.DeoxpDUhLO8LY.TJWtXk2aPp9Ivq3wRCNwD9mhlSlcqQz2nQQ; mauthtoken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJNX0k0VkE3RkU2UiIsInJvbGUiOiJ1c2VyIiwiYWNjZXNzX3BhdGgiOlsiL2Rhc2hib2FyZCJdLCJleHBpcnkiOjE3Nzg3NzI2OTgsImNyZWF0ZWQiOjE3Nzg2ODYyOTgsIjJvbzkiOiJNc0giLCJleHAiOjE3Nzg3NzI2OTgsImlhdCI6MTc3ODY4NjI5OCwic3ViIjoiTV9JNFZBN0ZFNlIifQ.qJz3Gy7o1FEbUztRw4kLQ5BCvdFnPrsf38nIMRppuvU"

CONSOLE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Mauthtoken": CONSOLE_MAUTH_TOKEN,
    "Cookie": CONSOLE_COOKIE,
    "Referer": "https://x.mnitnetwork.com/mdashboard/console"
}

# ======================== 3. হাদী প্যানেল (API 2) কনফিগারেশন ========================
HADI_API_URL = "http://147.135.212.197/crapi/had/viewstats"
HADI_API_TOKEN = "Q1ZQNEVBmWRoT1GGcmuJSVuIiEV3ZFJeYXeUVllmhkJeYIBrWoM"
FETCH_RECORDS = 50

# ======================== দেশের কোড ও পতাকা ========================
COUNTRY_CODES = {
    "+93": ("🇦🇫", "AF"), "+355": ("🇦🇱", "AL"), "+213": ("🇩🇿", "DZ"), "+376": ("🇦🇩", "AD"),
    "+244": ("🇦🇴", "AO"), "+54": ("🇦🇷", "AR"), "+374": ("🇦🇲", "AM"), "+61": ("🇦🇺", "AU"),
    "+43": ("🇦🇹", "AT"), "+994": ("🇦🇿", "AZ"), "+973": ("🇧🇭", "BH"), "+880": ("🇧🇩", "BD"),
    "+375": ("🇧🇾", "BY"), "+32": ("🇧🇪", "BE"), "+501": ("🇧🇿", "BZ"), "+229": ("🇧🇯", "BJ"),
    "+975": ("🇧🇹", "BT"), "+591": ("🇧🇴", "BO"), "+387": ("🇧🇦", "BA"), "+267": ("🇧🇼", "BW"),
    "+55": ("🇧🇷", "BR"), "+673": ("🇧🇳", "BN"), "+359": ("🇧🇬", "BG"), "+226": ("🇧🇫", "BF"),
    "+257": ("🇧🇮", "BI"), "+855": ("🇰🇭", "KH"), "+237": ("🇨🇲", "CM"), "+1": ("🇺🇸/🇨🇦", "US/CA"),
    "+238": ("🇨🇻", "CV"), "+236": ("🇨🇫", "CF"), "+235": ("🇹🇩", "TD"), "+56": ("🇨🇱", "CL"),
    "+86": ("🇨🇳", "CN"), "+57": ("🇨🇴", "CO"), "+269": ("🇰🇲", "KM"), "+242": ("🇨🇬", "CG"),
    "+243": ("🇨🇩", "CD"), "+506": ("🇨🇷", "CR"), "+385": ("🇭🇷", "HR"), "+53": ("🇨🇺", "CU"),
    "+357": ("🇨🇾", "CY"), "+420": ("🇨🇿", "CZ"), "+45": ("🇩🇰", "DK"), "+253": ("🇩🇯", "DJ"),
    "+593": ("🇪🇨", "EC"), "+20": ("🇪🇬", "EG"), "+503": ("🇸🇻", "SV"), "+240": ("🇬🇶", "GQ"),
    "+291": ("🇪🇷", "ER"), "+372": ("🇪🇪", "EE"), "+251": ("🇪🇹", "ET"), "+679": ("🇫🇯", "FJ"),
    "+358": ("🇫🇮", "FI"), "+33": ("🇫🇷", "FR"), "+241": ("🇬🇦", "GA"), "+220": ("🇬🇲", "GM"),
    "+995": ("🇬🇪", "GE"), "+49": ("🇩🇪", "DE"), "+233": ("🇬🇭", "GH"), "+30": ("🇬🇷", "GR"),
    "+502": ("🇬🇹", "GT"), "+224": ("🇬🇳", "GN"), "+245": ("🇬🇼", "GW"), "+592": ("🇬🇾", "GY"),
    "+509": ("🇭🇹", "HT"), "+504": ("🇭🇳", "HN"), "+36": ("🇭🇺", "HU"), "+354": ("🇮🇸", "IS"),
    "+91": ("🇮🇳", "IN"), "+62": ("🇮🇩", "ID"), "+98": ("🇮🇷", "IR"), "+964": ("🇮🇶", "IQ"),
    "+353": ("🇮🇪", "IE"), "+972": ("🇮🇱", "IL"), "+39": ("🇮🇹", "IT"), "+225": ("🇨🇮", "CI"),
    "+81": ("🇯🇵", "JP"), "+962": ("🇯🇴", "JO"), "+7": ("🇷🇺/🇰🇿", "RU/KZ"), "+254": ("🇰🇪", "KE"),
    "+686": ("🇰🇮", "KI"), "+383": ("🇽🇰", "XK"), "+965": ("🇰🇼", "KW"), "+996": ("🇰🇬", "KG"),
    "+856": ("🇱🇦", "LA"), "+371": ("🇱🇻", "LV"), "+961": ("🇱🇧", "LB"), "+266": ("🇱🇸", "LS"),
    "+231": ("🇱🇷", "LR"), "+218": ("🇱🇾", "LY"), "+423": ("🇱🇮", "LI"), "+370": ("🇱🇹", "LT"),
    "+352": ("🇱🇺", "LU"), "+261": ("🇲🇬", "MG"), "+265": ("🇲🇼", "MW"), "+60": ("🇲🇾", "MY"),
    "+960": ("🇲🇻", "MV"), "+223": ("🇲🇱", "ML"), "+356": ("🇲🇹", "MT"), "+222": ("🇲🇷", "MR"),
    "+230": ("🇲🇺", "MU"), "+52": ("🇲🇽", "MX"), "+691": ("🇫🇲", "FM"), "+373": ("🇲🇩", "MD"),
    "+377": ("🇲🇨", "MC"), "+976": ("🇲🇳", "MN"), "+382": ("🇲🇪", "ME"), "+212": ("🇲🇦", "MA"),
    "+258": ("🇲🇿", "MZ"), "+95": ("🇲🇲", "MM"), "+264": ("🇳🇦", "NA"), "+674": ("🇳🇷", "NR"),
    "+977": ("🇳🇵", "NP"), "+31": ("🇳🇱", "NL"), "+64": ("🇳🇿", "NZ"), "+505": ("🇳🇮", "NI"),
    "+227": ("🇳🇪", "NE"), "+234": ("🇳🇬", "NG"), "+850": ("🇰🇵", "KP"), "+389": ("🇲🇰", "MK"),
    "+47": ("🇳🇴", "NO"), "+968": ("🇴🇲", "OM"), "+92": ("🇵🇰", "PK"), "+680": ("🇵🇼", "PW"),
    "+970": ("🇵🇸", "PS"), "+507": ("🇵🇦", "PA"), "+675": ("🇵🇬", "PG"), "+595": ("🇵🇾", "PY"),
    "+51": ("🇵🇪", "PE"), "+63": ("🇵🇭", "PH"), "+48": ("🇵🇱", "PL"), "+351": ("🇵🇹", "PT"),
    "+974": ("🇶🇦", "QA"), "+40": ("🇷🇴", "RO"), "+250": ("🇷🇼", "RW"), "+966": ("🇸🇦", "SA"),
    "+221": ("🇸🇳", "SN"), "+381": ("🇷🇸", "RS"), "+248": ("🇸🇨", "SC"), "+232": ("🇸🇱", "SL"),
    "+65": ("🇸🇬", "SG"), "+421": ("🇸🇰", "SK"), "+386": ("🇸🇮", "SI"), "+677": ("🇸🇧", "SB"),
    "+252": ("🇸🇴", "SO"), "+27": ("🇿🇦", "ZA"), "+82": ("🇰🇷", "KR"), "+211": ("🇸🇸", "SS"),
    "+34": ("🇪🇸", "ES"), "+94": ("🇱🇰", "LK"), "+249": ("🇸🇩", "SD"), "+597": ("🇸🇷", "SR"),
    "+268": ("🇸🇿", "SZ"), "+46": ("🇸🇪", "SE"), "+41": ("🇨🇭", "CH"), "+963": ("🇸🇾", "SY"),
    "+886": ("🇹🇼", "TW"), "+992": ("🇹🇯", "TJ"), "+255": ("🇹🇿", "TZ"), "+66": ("🇹🇭", "TH"),
    "+228": ("🇹🇬", "TG"), "+676": ("🇹🇴", "TO"), "+216": ("🇹🇳", "TN"), "+90": ("🇹🇷", "TR"),
    "+993": ("🇹🇲", "TM"), "+688": ("🇹🇻", "TV"), "+256": ("🇺🇬", "UG"), "+380": ("🇺🇦", "UA"),
    "+971": ("🇦🇪", "AE"), "+44": ("🇬🇧", "GB"), "+598": ("🇺🇾", "UY"), "+998": ("🇺🇿", "UZ"),
    "+678": ("🇻🇺", "VU"), "+379": ("🇻🇦", "VA"), "+58": ("🇻🇪", "VE"), "+84": ("🇻🇳", "VN"),
    "+967": ("🇾🇪", "YE"), "+260": ("🇿🇲", "ZM"), "+263": ("🇿🇼", "ZW")
}

def get_country_info(phone: str) -> tuple:
    if not phone: return "🌍", "GLOBAL"
    phone_str = str(phone).strip()
    if not phone_str.startswith("+"): phone_str = "+" + phone_str
    for code, (flag, short_name) in sorted(COUNTRY_CODES.items(), key=lambda x: len(x[0]), reverse=True):
        if phone_str.startswith(code): return flag, short_name
    return "🌍", "GLOBAL"

# ডাবল ওটিপি ঠেকানোর জন্য গ্লোবাল ক্যাশ (যে কোনো প্যানেল থেকে আসুক, ১ বারই যাবে)
global_processed_otps = deque(maxlen=5000)

def extract_otp(text: str) -> str | None:
    if not text: return None
    ast_match = re.search(r'\*{4,8}', text)
    if ast_match:
        length = len(ast_match.group(0))
        return ''.join(random.choices('0123456789', k=length))
        
    text = str(text).upper()
    fb_ig_match = re.search(r'(?:FB|IG)[\s\-]*(\d{5,8})', text)
    if fb_ig_match: return fb_ig_match.group(1)
    clean_text = text.replace("-", " ").replace("=", " ").replace(":", " ")
    for match in re.findall(r'\b\d{4,8}\b', clean_text):
        if not re.match(r'^0+$', match): return match
    for match in re.findall(r'\d{4,8}', text.replace("-", "").replace(" ", "")):
        if not re.match(r'^0+$', match): return match
    return None

def generate_skypro_number(phone: str) -> str:
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) >= 6: return f"{digits[:3]}SKYPRO{digits[-3:]}"
    elif len(digits) > 3: return f"{digits[:3]}SKYPRO"
    return f"SKYPRO{digits}"

def detect_advanced_category(app_name, sms_text):
    combined = f"{str(app_name)} {str(sms_text)}".upper()
    if "WHATSAPP" in combined or "V-WHATSAPP" in combined: return "WHATSAPP", "WA"
    if "INSTAGRAM" in combined or " IG " in combined or "IG-" in combined: return "INSTAGRAM", "IG"
    if "FACEBOOK" in combined or " FB " in combined or "FB-" in combined: return "FACEBOOK", "FB"
    if "TELEGRAM" in combined: return "TELEGRAM", "TG"
    if "TIKTOK" in combined: return "TIKTOK", "TK"
    if "GOOGLE" in combined or " G-" in combined: return "GOOGLE", "GL"
    match = re.search(r'CODE FOR ([A-Z0-9]+)', combined)
    if match:
        cat = match.group(1).strip()
        return cat, cat[:6] 
    valid_app_name = str(app_name).strip().upper()
    invalid_names = ["", "******", "AUTHMSG", "FAILED CALLS", "AIRCOMM SA", "IRISTEL", "NONE", "NULL"]
    if valid_app_name and valid_app_name not in invalid_names: return valid_app_name, valid_app_name[:6]
    return "UNKNOWN", "UKN"

def format_telegram_message(otp_code: str, phone: str, category_short: str) -> str:
    flag, country_short = get_country_info(phone)
    skypro_number = generate_skypro_number(phone)
    inner_text = f"{flag} {country_short}➔{category_short}➔[ {skypro_number} ]"
    top_line = "┏━━━━━━━━━━━━━━━━━━━━━━━┓"
    mid_line = f"┃ {inner_text} ┃"
    bot_line = "┗━━━━━━━━━━━━━━━━━━━━━━━┛"
    return f"{top_line}\n{mid_line}\n{bot_line}\n\n🕋 **𝙿𝙾𝚆𝙴𝚁𝙴𝙳 𝙱𝚈 [𝐒𝐊𝐘](https://t.me/SKYSMSOWNER)** 🕋"

async def send_to_telegram(session, otp_code: str, phone: str, category_full: str, category_short: str, log_badge: str):
    text = format_telegram_message(otp_code, phone, category_short)
    reply_markup = {
        "inline_keyboard": [
            [{"text": f" {otp_code}", "copy_text": {"text": otp_code}}],
            [
                {"text": "‼️ 𝑷𝑨𝑵𝑬𝑳", "url": "https://t.me/SKYSMSPRO_BOT"},
                {"text": "📞 𝑪𝑯𝑨𝑵𝑵𝑬𝑳", "url": "https://t.me/SKYOFFICIALCHANNEL1"}
            ]
        ]
    }
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(reply_markup),
        "disable_web_page_preview": True
    }
    
    while True:
        try:
            async with session.post(url, json=payload, timeout=15) as resp:
                if resp.status == 200:
                    print(f"[{log_badge}] ✅ ফরোয়ার্ড হয়েছে: {otp_code} | {category_full}")
                    break 
                elif resp.status == 429: 
                    resp_json = await resp.json()
                    retry_after = resp_json.get("parameters", {}).get("retry_after", 15)
                    print(f"⚠️ টেলিগ্রাম রেট লিমিট! {retry_after} সেকেন্ড পর আবার পাঠানো হবে...")
                    await asyncio.sleep(retry_after + 1) 
                else:
                    error_text = await resp.text()
                    print(f"[{log_badge}] ❌ টেলিগ্রাম এরর (Status {resp.status}): {error_text}")
                    break
        except Exception as e:
            print(f"⚠️ টেলিগ্রামে কানেক্ট করতে সমস্যা: {e}")
            await asyncio.sleep(5)
            break

# ======================== ইঞ্জিন ১: রিয়েল OTP মনিটর ========================
async def monitor_real_api(session):
    print("🟢 [ইঞ্জিন ১] রিয়েল API মনিটরিং শুরু...")
    while True:
        try:
            async with session.get(REAL_API_URL, headers=REAL_HEADERS, timeout=15.0, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    logs = []
                    if isinstance(data, dict):
                        data_obj = data.get("data")
                        if data_obj and isinstance(data_obj, dict): logs = data_obj.get("otps", [])
                        elif "otps" in data: logs = data.get("otps", [])
                    
                    for log in reversed(logs):
                        raw_otp = str(log.get("otp", "")).strip()
                        full_sms = str(log.get("sms") or log.get("message") or log.get("text") or "")
                        text_to_parse = full_sms if (re.match(r'^0+$', raw_otp) or not raw_otp) else f"{raw_otp} {full_sms}"
                        
                        phone = str(log.get("number", "")).strip().replace("+", "")
                        otp = extract_otp(text_to_parse)
                        
                        if otp:
                            unique_key = f"{phone}_{otp}"
                            if unique_key not in global_processed_otps:
                                app_name_raw = str(log.get("operator") or log.get("app_name") or "")
                                cat_full, cat_short = detect_advanced_category(app_name_raw, text_to_parse)
                                
                                if cat_full != "UNKNOWN":
                                    global_processed_otps.append(unique_key)
                                    print(f"🟢 [REAL] আসল OTP পাওয়া গেছে! ({cat_full})")
                                    await send_to_telegram(session, otp, phone, cat_full, cat_short, "REAL")
                                    await asyncio.sleep(0.1) 
        except Exception as e: pass
        await asyncio.sleep(2) 

# ======================== ইঞ্জিন ২: কনসোল (TEST) মনিটর ========================
async def monitor_console_api(session):
    print("🔄 [ইঞ্জিন ২] কনসোল (TEST) মনিটরিং শুরু...")
    cookies_dict = {}
    if CONSOLE_COOKIE:
        for item in CONSOLE_COOKIE.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookies_dict[k] = v

    while True:
        try:
            async with session.get(CONSOLE_API_URL, headers=CONSOLE_HEADERS, cookies=cookies_dict, timeout=15.0, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logs = data.get("data", {}).get("logs", [])
                    for log in reversed(logs):
                        full_sms = str(log.get("sms") or log.get("message") or log.get("text") or "")
                        raw_otp = str(log.get("otp", "")).strip()
                        text_to_parse = full_sms if (re.match(r'^0+$', raw_otp) or not raw_otp) else f"{raw_otp} {full_sms}"
                        
                        phone = str(log.get("range") or log.get("number") or log.get("number_raw") or "").strip().replace("+", "")
                        otp = extract_otp(text_to_parse)
                        
                        if otp:
                            unique_key = f"TEST_{phone}_{otp}"
                            if unique_key not in global_processed_otps:
                                app_name_raw = str(log.get("app_name") or log.get("service") or log.get("operator") or "")
                                cat_full, cat_short = detect_advanced_category(app_name_raw, text_to_parse)
                                
                                if cat_full != "UNKNOWN":
                                    global_processed_otps.append(unique_key)
                                    print(f"🔄 [TEST] রেন্ডম OTP তৈরি হয়েছে! ({cat_full})")
                                    await send_to_telegram(session, otp, phone, cat_full, cat_short, "TEST")
                                    await asyncio.sleep(0.1) 
        except Exception as e: pass
        await asyncio.sleep(4) 

# ======================== ইঞ্জিন ৩: হাদী প্যানেল (API 2) মনিটর ========================
async def monitor_hadi_api(session):
    print("🔵 [ইঞ্জিন ৩] হাদী প্যানেল (API 2) মনিটরিং শুরু...")
    params = {"token": HADI_API_TOKEN, "records": FETCH_RECORDS}
    
    while True:
        try:
            async with session.get(HADI_API_URL, params=params, timeout=15.0, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    if data.get("status") == "success":
                        logs = data.get("data", [])
                        for log in reversed(logs):
                            message = str(log.get("message", "")).strip()
                            if not message or message.lower() in ['none', 'null', '']:
                                continue
                                
                            phone = str(log.get("num", "Unknown")).strip().replace("+", "")
                            otp = extract_otp(message)
                            
                            if otp:
                                unique_key = f"{phone}_{otp}"
                                if unique_key not in global_processed_otps:
                                    platform_raw = str(log.get("cli", "FACEBOOK"))
                                    cat_full, cat_short = detect_advanced_category(platform_raw, message)
                                    
                                    if cat_full != "UNKNOWN":
                                        global_processed_otps.append(unique_key)
                                        print(f"🔵 [HADI] হাদী প্যানেল থেকে OTP পাওয়া গেছে! ({cat_full})")
                                        await send_to_telegram(session, otp, phone, cat_full, cat_short, "HADI")
                                        await asyncio.sleep(0.1)
        except Exception as e: pass
        await asyncio.sleep(2) 

async def main():
    print("="*65)
    print("☁️ SKY SYSTEM INITIATED (TRIPLE ENGINE: REAL + TEST + HADI)")
    print("="*65)
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        await asyncio.gather(
            monitor_real_api(session), 
            monitor_console_api(session),
            monitor_hadi_api(session)
        )

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: print("\n🛑 বট বন্ধ করা হয়েছে।")
