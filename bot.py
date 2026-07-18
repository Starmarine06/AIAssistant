import os, json, logging, datetime, re, requests, subprocess, pyautogui, io, base64, time, asyncio, uuid, urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

import sys
import threading

# ─── PATH SETUP ────────────────────────────────────────
if getattr(sys, 'frozen', False):
    CONFIG_DIR = os.path.join(os.environ["APPDATA"], "AIAssistant")
else:
    CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(CONFIG_DIR, exist_ok=True)

# Ensure working directory is correct when not packaged
if not getattr(sys, 'frozen', False):
    os.chdir(CONFIG_DIR)

if os.path.exists(".env"):
    load_dotenv()

# ─── CONFIG INITIALIZATION ─────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
AUTHORIZED_CHAT_ID = None

NVIDIA_URL      = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL    = "meta/llama-3.3-70b-instruct"
NVIDIA_VISION   = "meta/llama-3.2-90b-vision-instruct"
GCAL_SCOPES     = ["https://www.googleapis.com/auth/calendar"]

def save_authorized_chat_id(chat_id):
    global AUTHORIZED_CHAT_ID
    AUTHORIZED_CHAT_ID = chat_id
    config_path = os.path.join(CONFIG_DIR, "config.json")
    try:
        data = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = json.load(f)
        data["authorized_chat_id"] = chat_id
        with open(config_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving chat ID: {e}")

def load_config():
    global TELEGRAM_TOKEN, NVIDIA_API_KEY, AUTHORIZED_CHAT_ID
    config_path = os.path.join(CONFIG_DIR, "config.json")
    
    # Fallback to AppData config if running in dev mode and local config is missing
    if not getattr(sys, 'frozen', False) and not os.path.exists(config_path):
        appdata_path = os.path.join(os.environ.get("APPDATA", ""), "AIAssistant", "config.json")
        if os.path.exists(appdata_path):
            config_path = appdata_path
            
    if not os.path.exists(config_path):
        from settings_gui import show_settings_gui
        show_settings_gui(CONFIG_DIR)
        
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
        TELEGRAM_TOKEN = data.get("telegram_token") or TELEGRAM_TOKEN
        NVIDIA_API_KEY = data.get("nvidia_api_key") or NVIDIA_API_KEY
        AUTHORIZED_CHAT_ID = data.get("authorized_chat_id")
    except Exception:
        from settings_gui import show_settings_gui
        show_settings_gui(CONFIG_DIR)
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            TELEGRAM_TOKEN = data.get("telegram_token") or TELEGRAM_TOKEN
            NVIDIA_API_KEY = data.get("nvidia_api_key") or NVIDIA_API_KEY
            AUTHORIZED_CHAT_ID = data.get("authorized_chat_id")
        except Exception:
            pass

# Load config
load_config()

# ─── PERSISTENT REMINDERS ────────────────────────────────
REMINDERS_FILE = os.path.join(CONFIG_DIR, "reminders.json")

def load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return {}
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading reminders: {e}")
        return {}

def save_reminder(reminder):
    reminders = load_reminders()
    reminders[reminder["id"]] = reminder
    try:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(reminders, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving reminder: {e}")

def remove_reminder(reminder_id):
    reminders = load_reminders()
    if reminder_id in reminders:
        del reminders[reminder_id]
        try:
            with open(REMINDERS_FILE, "w") as f:
                json.dump(reminders, f, indent=4)
        except Exception as e:
            logging.error(f"Error removing reminder: {e}")

async def schedule_reminder(reminder, bot):
    delay = reminder["target_timestamp"] - time.time()
    if delay > 0:
        await asyncio.sleep(delay)
    
    # Check if still untriggered (could have been deleted or handled already)
    reminders = load_reminders()
    curr_rem = reminders.get(reminder["id"])
    if not curr_rem or curr_rem.get("triggered", False):
        return
        
    # Mark as triggered
    curr_rem["triggered"] = True
    save_reminder(curr_rem)
    
    # Send message with inline keyboard to add to calendar
    keyboard = [[
        InlineKeyboardButton("📅 Add to Google Calendar", callback_data=f"remcal_{reminder['id']}")
    ]]
    try:
        await bot.send_message(
            chat_id=reminder["chat_id"],
            text=f"🔔 *Reminder:* {curr_rem['message']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logging.error(f"Error sending reminder message: {e}")

# ─── UPDATE SYSTEM ────────────────────────────────────
VERSION = "1.0.0"

def is_newer_version(current, remote):
    try:
        c_parts = [int(x) for x in current.strip('v').split('.')]
        r_parts = [int(x) for x in remote.strip('v').split('.')]
        return r_parts > c_parts
    except Exception:
        return remote != current

def get_latest_update_info():
    import requests
    url = "https://raw.githubusercontent.com/Starmarine06/AIAssistant/main/version.json"
    try:
        r = requests.get(url, headers={"User-Agent": "AIAssistant-Updater"}, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        logging.error(f"Error fetching version.json: {e}")
    return None

async def check_for_updates_startup(application):
    if not AUTHORIZED_CHAT_ID:
        return
    try:
        await asyncio.sleep(5)
        await run_update_check_silent(application.bot)
    except Exception as e:
        logging.error(f"Startup update check failed: {e}")

async def run_update_check_silent(bot):
    update_info = get_latest_update_info()
    if update_info and is_newer_version(VERSION, update_info.get("version")):
        latest_ver = update_info.get("version")
        notes = update_info.get("release_notes", "No release notes.")
        msg = (
            f"🔔 *New Update Available!*\n"
            f"Current: `v{VERSION}`\n"
            f"Latest: `v{latest_ver}`\n\n"
            f"*Release Notes:*\n{notes}\n\n"
            f"Would you like to update now?"
        )
        keyboard = [[
            InlineKeyboardButton("⬇️ Update Bot", callback_data="update_bot")
        ]]
        await bot.send_message(
            chat_id=AUTHORIZED_CHAT_ID,
            text=msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def check_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if AUTHORIZED_CHAT_ID and uid != AUTHORIZED_CHAT_ID:
        return
        
    status_msg = await update.message.reply_text("🔍 Checking for updates...")
    update_info = get_latest_update_info()
    
    if not update_info:
        await status_msg.edit_text("❌ Failed to fetch update information from GitHub.")
        return
        
    latest_ver = update_info.get("version")
    if is_newer_version(VERSION, latest_ver):
        notes = update_info.get("release_notes", "No release notes.")
        msg = (
            f"🔔 *New Update Available!*\n"
            f"Current: `v{VERSION}`\n"
            f"Latest: `v{latest_ver}`\n\n"
            f"*Release Notes:*\n{notes}\n\n"
            f"Would you like to update now?"
        )
        keyboard = [[
            InlineKeyboardButton("⬇️ Update Bot", callback_data="update_bot")
        ]]
        await status_msg.edit_text(
            text=msg,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await status_msg.edit_text(f"✅ Your AI Assistant is up-to-date (Version `v{VERSION}`).")

async def update_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    uid = query.from_user.id
    if AUTHORIZED_CHAT_ID and uid != AUTHORIZED_CHAT_ID:
        return
        
    await query.edit_message_text("📥 Fetching latest update info...")
    
    update_info = get_latest_update_info()
    if not update_info:
        await query.edit_message_text("❌ Failed to fetch update information. Update cancelled.")
        return
        
    latest_ver = update_info.get("version")
    
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        download_url = update_info.get("download_url")
        target_filename = "bot.exe"
    else:
        download_url = update_info.get("download_py_url")
        target_filename = "bot.py"
        
    if not download_url:
        await query.edit_message_text(f"❌ No download URL found for {'executable' if is_frozen else 'Python script'}.")
        return
        
    await query.edit_message_text(f"⬇️ Downloading `v{latest_ver}`...")
    
    import requests
    exe_dir = os.path.dirname(sys.executable) if is_frozen else os.path.dirname(os.path.abspath(__file__))
    new_filepath = os.path.join(exe_dir, f"{target_filename}.new")
    current_filepath = sys.executable if is_frozen else os.path.abspath(__file__)
    
    try:
        r = requests.get(download_url, stream=True, timeout=30)
        r.raise_for_status()
        with open(new_filepath, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        if os.path.exists(new_filepath):
            try: os.remove(new_filepath)
            except: pass
        await query.edit_message_text(f"❌ Download failed: {e}")
        return
        
    await query.edit_message_text("🔄 Applying update & restarting...")
    
    try:
        old_filepath = current_filepath + ".old"
        if os.path.exists(old_filepath):
            try: os.remove(old_filepath)
            except: pass
            
        os.rename(current_filepath, old_filepath)
        os.rename(new_filepath, current_filepath)
        
        if is_frozen:
            subprocess.Popen([current_filepath] + sys.argv[1:], cwd=exe_dir, start_new_session=True)
        else:
            subprocess.Popen([sys.executable, current_filepath] + sys.argv[1:], cwd=exe_dir, start_new_session=True)
            
        await query.edit_message_text("✅ Bot successfully updated and restarted!")
        os._exit(0)
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to swap files: {e}. Please manually restart.")

async def post_init(application):
    # Initialize reminders
    reminders = load_reminders()
    now = time.time()
    
    for r_id, r in list(reminders.items()):
        if not r.get("triggered", False):
            if r["target_timestamp"] <= now:
                # Missed reminder
                orig_time = datetime.datetime.fromtimestamp(r["target_timestamp"]).strftime("%Y-%m-%d %H:%M")
                msg = f"⚠️ *Missed reminder while offline:*\n• {r['message']} (scheduled for {orig_time})"
                keyboard = [[
                    InlineKeyboardButton("📅 Add to Google Calendar", callback_data=f"remcal_{r['id']}")
                ]]
                try:
                    await application.bot.send_message(
                        chat_id=r["chat_id"],
                        text=msg,
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    logging.error(f"Error sending missed reminder: {e}")
                
                r["triggered"] = True
                save_reminder(r)
                # Schedule future reminder
                asyncio.create_task(schedule_reminder(r, application.bot))

    # Start background task scheduler
    asyncio.create_task(run_task_scheduler(application.bot))
    # Start background update check
    asyncio.create_task(check_for_updates_startup(application))

# ─── SAVED CONTACTS ADDRESS BOOK ─────────────────────────
CONTACTS_FILE = os.path.join(CONFIG_DIR, "contacts.json")

def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return {}
    try:
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading contacts: {e}")
        return {}

def save_contact_to_file(name, phone):
    contacts = load_contacts()
    contacts[name.strip().lower()] = phone.strip()
    try:
        with open(CONTACTS_FILE, "w") as f:
            json.dump(contacts, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving contact: {e}")
        return False

async def is_authorized(update: Update):
    global AUTHORIZED_CHAT_ID
    if update.effective_user is None:
        return False
    uid = update.effective_user.id
    if AUTHORIZED_CHAT_ID is None or AUTHORIZED_CHAT_ID == 0:
        save_authorized_chat_id(uid)
        if update.effective_message:
            await update.effective_message.reply_text(
                f"🔒 *Owner Registered!*\n\n"
                f"You have been successfully registered as the owner of this AI Assistant.\n"
                f"Authorized Chat ID: `{uid}`\n"
                f"All other users are now blocked.",
                parse_mode="Markdown"
            )
        return True
    return uid == AUTHORIZED_CHAT_ID

# Configure Logging to file in AppData and console
log_file = os.path.join(CONFIG_DIR, "bot.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
histories = {}
search_results = {}  # uid -> [filepath, ...]

def escape_md(text):
    """Escape special characters for Telegram Markdown."""
    for ch in ('_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'):
        text = text.replace(ch, f'\\{ch}')
    return text
calendar_service = None

# ─── NVIDIA TEXT CALL ──────────────────────────────────
def call_nvidia(messages, model=None):
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": model or NVIDIA_MODEL,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1.00,
        "stream": True,
    }
    response = requests.post(NVIDIA_URL, headers=headers, json=payload, stream=True)
    response.raise_for_status()

    full_text = ""
    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if decoded.startswith("data: "):
            decoded = decoded[6:]
        if decoded == "[DONE]":
            break
        try:
            chunk = json.loads(decoded)
            delta = chunk["choices"][0]["delta"]
            full_text += delta.get("content", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    return full_text.strip()

# ─── VISION: ANALYZE IMAGE WITH AI ──────────────────────
def analyze_image_with_vision(image_bytes, caption=""):
    """Send image and caption to vision model to decide if it's a calendar event or general question/description."""
    image_bytes.seek(0)
    b64 = base64.b64encode(image_bytes.read()).decode("utf-8")
    today = datetime.date.today().isoformat()

    prompt = f"""Today is {today}. Analyze this image carefully.
The user might have provided a caption, question, or instruction: "{caption}"

Your task is to judge whether this image (and any caption) represents calendar events, schedules, timetables, meeting reminders, appointment confirmations, exam/quiz/submission deadlines, or anything that should be scheduled on a calendar.
- Only schedule the events if the image content is clearly calendar/event/deadline related AND the user's caption doesn't indicate they are just asking a general question about the image.
- If it is a calendar event/schedule to add, extract the event(s) and set "is_calendar_event" to true.
- If it is NOT a calendar event to add (e.g. it's a photo of an object, text to read/explain, math problem, general question, or they are just asking what the image is), set "is_calendar_event" to false, and answer their question or describe the image in "response".

You must respond ONLY with a valid JSON object in the following format:
{{
  "is_calendar_event": true,
  "events": [
    {{
      "title": "Subject/Course - Event name",
      "date": "YYYY-MM-DD",
      "time": "HH:MM",  // (optional, 24-hour format, omit if not specified)
      "description": "Any additional context or details extracted from the image"
    }}
  ],
  "response": ""
}}
OR:
{{
  "is_calendar_event": false,
  "events": [],
  "response": "Detailed text answering the user's question, translating/explaining the image, or describing it if no caption was provided."
}}

Rules:
- Be extremely accurate and thorough when converting dates. Ensure the year is correct (current year is {today[:4]}).
- Standardize all dates to YYYY-MM-DD.
- Convert 12-hour times to 24-hour HH:MM format.
- Ensure the JSON is well-formed. Do not add any conversational text or markdown formatting around the JSON object.
"""

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": NVIDIA_VISION,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.2,
        "stream": True,
    }

    response = requests.post(NVIDIA_URL, headers=headers, json=payload, stream=True)
    response.raise_for_status()

    full_text = ""
    for line in response.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if decoded.startswith("data: "):
            decoded = decoded[6:]
        if decoded == "[DONE]":
            break
        try:
            chunk = json.loads(decoded)
            delta = chunk["choices"][0]["delta"]
            full_text += delta.get("content", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    return full_text.strip()

# ─── GOOGLE CALENDAR ───────────────────────────────────
def init_calendar():
    global calendar_service
    creds = None
    token_path = os.path.join(CONFIG_DIR, "token.json")
    creds_path = os.path.join(CONFIG_DIR, "credentials.json")
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, GCAL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logging.info("🔐 Opening browser for Google Calendar authorization...")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, GCAL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())
        logging.info("✅ Google Calendar authorized!")
    calendar_service = build("calendar", "v3", credentials=creds)
    logging.info("✅ Google Calendar connected!")

def create_calendar_event(title, date_str, time_str=None, description=""):
    if time_str:
        start = f"{date_str}T{time_str}:00"
        end_dt = datetime.datetime.fromisoformat(start) + datetime.timedelta(hours=1)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": "Asia/Kolkata"},
            "end":   {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }
    else:
        event = {
            "summary": title,
            "description": description,
            "start": {"date": date_str},
            "end":   {"date": date_str},
        }
    result = calendar_service.events().insert(calendarId="primary", body=event).execute()
    return result.get("htmlLink")

def create_multiple_events(events_list):
    created = []
    failed = []
    for ev in events_list:
        try:
            link = create_calendar_event(
                ev["title"], ev["date"],
                ev.get("time"), ev.get("description", "")
            )
            created.append({
                "title": ev["title"],
                "date": ev["date"],
                "time": ev.get("time", "All day"),
                "link": link
            })
        except Exception as e:
            failed.append(f"{ev.get('title','?')} ({e})")
    return created, failed

# ─── COMPUTER CONTROL ──────────────────────────────────
def take_screenshot():
    screenshot = pyautogui.screenshot()
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

def score_match(target_clean, target_words, candidate_name):
    cand_clean = re.sub(r'[^a-z0-9]', '', candidate_name.lower())
    if not cand_clean:
        return 0
    # Exact match of cleaned names
    if cand_clean == target_clean:
        return 100
    # Substring match
    score = 0
    if target_clean in cand_clean:
        score += 50
    elif cand_clean in target_clean:
        score += 30
    # Word matches
    word_matches = sum(1 for w in target_words if w in cand_clean)
    score += word_matches * 10
    return score

def find_executable_smart(target):
    target_clean = re.sub(r'[^a-z0-9]', '', target.lower())
    target_words = [w for w in re.split(r'[\s_\-]+', target.lower()) if len(w) > 1]
    if not target_words and target:
        target_words = [target.lower()]
        
    if not target_words:
        return None

    # Common directories for shortcuts (.lnk)
    shortcut_dirs = [
        "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs",
        os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.expandvars("%USERPROFILE%\\Desktop"),
        "C:\\Users\\Public\\Desktop"
    ]
    
    best_candidate = None
    best_score = 0
    
    # 1. Search shortcuts (very fast)
    for sdir in shortcut_dirs:
        if not os.path.exists(sdir):
            continue
        try:
            for root, dirs, files in os.walk(sdir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name_no_ext = f[:-4]
                        score = score_match(target_clean, target_words, name_no_ext)
                        if score > best_score:
                            best_score = score
                            best_candidate = os.path.join(root, f)
        except Exception:
            pass
            
    # If we found a high quality shortcut match (score >= 50), return it immediately
    if best_score >= 50:
        return best_candidate

    # 2. Search common installer locations for executables (.exe)
    exe_dirs = [
        os.path.expandvars("%PROGRAMFILES%"),
        os.path.expandvars("%PROGRAMFILES(X86)%"),
        os.path.expandvars("%LOCALAPPDATA%\\Programs"),
        os.path.expandvars("%LOCALAPPDATA%"),
        os.path.expandvars("%APPDATA%")
    ]
    
    # Search up to depth 3 to keep it extremely fast
    def search_exes(path, depth=0, max_depth=3):
        nonlocal best_score, best_candidate
        if depth > max_depth or not os.path.exists(path):
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_dir():
                        # Skip system/large directories for speed
                        if entry.name.lower() not in {"windows", "system32", "syswow64", "common files", "microsoft", "cache", "temp", "tmp", "node_modules", ".git"}:
                            search_exes(entry.path, depth + 1, max_depth)
                    elif entry.is_file() and entry.name.lower().endswith(".exe"):
                        name_no_ext = entry.name[:-4]
                        score = score_match(target_clean, target_words, name_no_ext)
                        score -= 5 # slight penalty for exes vs shortcuts
                        if score > best_score:
                            best_score = score
                            best_candidate = entry.path
        except Exception:
            pass

    for edir in exe_dirs:
        search_exes(edir)
        # If we find a good match in Program Files, we don't need to search all of AppData
        if best_score >= 50:
            break
            
    if best_score >= 10:
        return best_candidate
        
    return None

def open_app_or_website(target):
    target_clean = target.strip().lower()
    
    # 1. Check if it's a URL
    if ("." in target_clean and " " not in target_clean) or target_clean.startswith("http"):
        if not target_clean.startswith("http"):
            target_clean = "https://" + target_clean
        try:
            subprocess.Popen(f'start {target_clean}', shell=True)
            return f"✅ Opened website: {target_clean}"
        except Exception as e:
            return f"❌ Could not open website {target_clean}: {e}"

    # 2. Hardcoded aliases mapping for quick launch
    apps = {
        "chrome": "chrome", 
        "firefox": "firefox", 
        "notepad": "notepad",
        "calculator": "calc", 
        "explorer": "explorer",
        "file explorer": "explorer", 
        "word": "winword", 
        "excel": "excel",
        "powerpoint": "powerpnt", 
        "vscode": "code", 
        "vs code": "code",
        "spotify": "spotify", 
        "discord": "discord", 
        "whatsapp": "whatsapp",
        "terminal": "cmd", 
        "cmd": "cmd", 
        "command prompt": "cmd",
        "task manager": "taskmgr", 
        "paint": "mspaint", 
        "vlc": "vlc",
        "teams": "teams", 
        "zoom": "zoom", 
        "telegram": "telegram",
    }
    
    for key, cmd in apps.items():
        if key == target_clean:
            try:
                subprocess.Popen(cmd, shell=True)
                return f"✅ Opened {key}"
            except Exception:
                pass

    # 3. Smart search for shortcuts (.lnk) and executables (.exe)
    match_path = find_executable_smart(target)
    if match_path:
        try:
            os.startfile(match_path)
            app_name = os.path.splitext(os.path.basename(match_path))[0]
            return f"✅ Opened '{app_name}'"
        except Exception as e:
            return f"❌ Found '{match_path}' but failed to open: {e}"

    # 4. Fallback execution
    try:
        subprocess.Popen(target_clean, shell=True)
        return f"✅ Executed: {target_clean}"
    except Exception as e:
        return f"❌ Could not open '{target_clean}': {e}"

def search_files_python(search_dir, query, search_type, max_results=20):
    """Pure Python search using os.scandir for speed and no dependencies."""
    results = []
    query_clean = query.lower().lstrip(".")
    
    # Folders to skip for speed and permissions
    skip_dirs = {
        "windows", "program files", "program files (x86)", "appdata", 
        "local settings", "application data", "node_modules", ".git", 
        ".venv", "venv", "env", "__pycache__", "cookies", "history", "temp", "tmp"
    }

    def walk_dir(path, current_depth=0, max_depth=4):
        if len(results) >= max_results or current_depth > max_depth:
            return
            
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if len(results) >= max_results:
                        break
                        
                    # Skip symlinks and hidden/system files
                    if entry.is_symlink() or entry.name.startswith('.'):
                        continue
                        
                    if entry.is_dir():
                        if entry.name.lower() not in skip_dirs:
                            walk_dir(entry.path, current_depth + 1, max_depth)
                    elif entry.is_file():
                        name_lower = entry.name.lower()
                        if search_type == "extension":
                            if name_lower.endswith(f".{query_clean}"):
                                results.append(entry.path)
                        else: # search_type == "name"
                            if query_clean in name_lower:
                                results.append(entry.path)
        except PermissionError:
            pass
        except Exception:
            pass

    walk_dir(search_dir)
    return results

def search_files_raw(query, search_type="name"):
    """Search for files. Tries fd (sharkdp/fd) first, falls back to pure Python."""
    query = query.strip().strip('"').strip("'")

    # Directories to search first (user folders = fast)
    priority_dirs = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Pictures"),
        os.path.expanduser("~/Videos"),
        os.path.expanduser("~/Music"),
    ]

    def run_fd(search_dir, max_results=20):
        """Run fd in a given directory and return list of file paths."""
        cmd = ["fd", "--type", "f", "--max-results", str(max_results)]
        if search_type == "extension":
            cmd += ["--extension", query.lstrip(".")]
        else:
            cmd.append(query)
        cmd += ["--search-path", search_dir]
        try:
            output = subprocess.check_output(
                cmd, timeout=15, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="ignore")
            return [l.strip() for l in output.strip().splitlines() if l.strip()]
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # Return None to indicate fd failed/is not available
            return None

    results = []
    fd_available = True

    # Step 1: Search user folders first
    for d in priority_dirs:
        if os.path.exists(d):
            fd_res = run_fd(d, max_results=20 - len(results))
            if fd_res is None:
                fd_available = False
                break
            results.extend(fd_res)
        if len(results) >= 20:
            break

    # If fd is available, try searching full C: drive
    if fd_available and len(results) < 20:
        full_results = run_fd("C:\\", max_results=20 - len(results))
        if full_results is not None:
            existing = set(results)
            for f in full_results:
                if f not in existing:
                    results.append(f)
                if len(results) >= 20:
                    break

    # Fallback: If fd is not available, use pure Python search
    if not fd_available:
        results = []
        for d in priority_dirs:
            if os.path.exists(d):
                results.extend(search_files_python(d, query, search_type, max_results=20 - len(results)))
                if len(results) >= 20:
                    break
        
        # If still not enough results, scan C:\ but with limited depth to keep it fast
        if len(results) < 20:
            c_results = search_files_python("C:\\", query, search_type, max_results=20 - len(results))
            existing = set(results)
            for f in c_results:
                if f not in existing:
                    results.append(f)
                if len(results) >= 20:
                    break

    return results

# ─── CUSTOM SKILLS DYNAMIC REGISTRY ─────────────────────
CUSTOM_SKILLS_DIR = os.path.join(CONFIG_DIR, "custom_skills")
os.makedirs(CUSTOM_SKILLS_DIR, exist_ok=True)

restart_pending = False

def get_custom_skills_metadata():
    """Scan custom_skills directory for skill definitions and return metadata for prompt."""
    skills_meta = []
    if not os.path.exists(CUSTOM_SKILLS_DIR):
        return skills_meta
        
    for filename in os.listdir(CUSTOM_SKILLS_DIR):
        if filename.endswith(".json"):
            name = filename.removesuffix(".json")
            json_path = os.path.join(CUSTOM_SKILLS_DIR, filename)
            py_path = os.path.join(CUSTOM_SKILLS_DIR, name + ".py")
            if os.path.exists(py_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    skills_meta.append({
                        "name": name,
                        "description": meta.get("description", "No description provided."),
                        "parameters": meta.get("parameters", {})
                    })
                except Exception as e:
                    logging.error(f"Error loading custom skill metadata for {name}: {e}")
    return skills_meta

def execute_custom_skill(name, parameters, update, context):
    """Dynamically import and run a custom skill."""
    py_path = os.path.join(CUSTOM_SKILLS_DIR, name + ".py")
    if not os.path.exists(py_path):
        return {"output": f"Error: Custom skill '{name}' does not exist.", "feed_back_to_ai": True}
        
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, py_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if not hasattr(module, "run"):
            return {"output": f"Error: Custom skill '{name}' is missing the 'run(parameters, update, context)' function.", "feed_back_to_ai": True}
            
        result = module.run(parameters, update, context)
        # Handle simple return formats (like just a string or dict without feedback flag)
        if isinstance(result, str):
            return {"output": result, "feed_back_to_ai": True}
        elif isinstance(result, dict):
            return {
                "output": result.get("output", "Success"),
                "feed_back_to_ai": result.get("feed_back_to_ai", True)
            }
        else:
            return {"output": "Skill executed successfully.", "feed_back_to_ai": True}
    except Exception as e:
        import traceback
        error_msg = f"Error executing custom skill '{name}': {e}\n{traceback.format_exc()}"
        logging.error(error_msg)
        return {"output": error_msg, "feed_back_to_ai": True}

def create_custom_skill(name, description, code, parameters_schema=None):
    """Create a new custom skill by saving Python code and json metadata."""
    # Clean up name: only alphanumeric and underscores
    name = re.sub(r'[^a-zA-Z0-9_]', '', name).strip().lower()
    if not name:
        return "Error: Invalid skill name."
        
    py_path = os.path.join(CUSTOM_SKILLS_DIR, name + ".py")
    json_path = os.path.join(CUSTOM_SKILLS_DIR, name + ".json")
    
    # Verify it compiles as valid python
    try:
        compile(code, py_path, 'exec')
    except SyntaxError as e:
        return f"Error: Python syntax error in the provided code: {e}"
        
    try:
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        meta = {
            "description": description,
            "parameters": parameters_schema or {}
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4)
            
        return f"Success: Custom skill '{name}' created successfully!"
    except Exception as e:
        return f"Error saving custom skill: {e}"

# ─── MOCK CLASSES FOR BACKGROUND TASKS ─────────────────
class MockMessage:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        
    async def reply_text(self, text, *args, **kwargs):
        return await self.bot.send_message(chat_id=self.chat_id, text=text, *args, **kwargs)

class MockUpdate:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.effective_chat = type('Chat', (object,), {'id': chat_id})()
        self.effective_user = type('User', (object,), {'id': chat_id})()
        self.message = MockMessage(bot, chat_id)
        self.effective_message = self.message

class MockContext:
    def __init__(self, bot):
        self.bot = bot

# ─── NATIVE WINDOWS CLIPBOARD HELPERS ──────────────────
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

def get_clipboard_text():
    import ctypes
    try:
        if not ctypes.windll.user32.OpenClipboard(None):
            return "Error: Could not open clipboard"
        try:
            handle = ctypes.windll.user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            ptr = ctypes.windll.kernel32.GlobalLock(handle)
            if not ptr:
                return ""
            text = ctypes.c_wchar_p(ptr).value
            ctypes.windll.kernel32.GlobalUnlock(handle)
            return text or ""
        finally:
            ctypes.windll.user32.CloseClipboard()
    except Exception as e:
        return f"Error: {e}"

def set_clipboard_text(text):
    import ctypes
    try:
        if not ctypes.windll.user32.OpenClipboard(None):
            return False
        try:
            ctypes.windll.user32.EmptyClipboard()
            text_bytes = (text + '\0').encode('utf-16le')
            size = len(text_bytes)
            handle = ctypes.windll.kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
            if not handle:
                return False
            ptr = ctypes.windll.kernel32.GlobalLock(handle)
            if not ptr:
                ctypes.windll.kernel32.GlobalFree(handle)
                return False
            ctypes.memmove(ptr, text_bytes, size)
            ctypes.windll.kernel32.GlobalUnlock(handle)
            if not ctypes.windll.user32.SetClipboardData(CF_UNICODETEXT, handle):
                ctypes.windll.kernel32.GlobalFree(handle)
                return False
            return True
        finally:
            ctypes.windll.user32.CloseClipboard()
    except Exception as e:
        logging.error(f"Error setting clipboard: {e}")
        return False

# ─── GRID SCREENSHOT & INTERACTIVE CONTROL ─────────────
def generate_grid_screenshot():
    from PIL import ImageDraw, ImageFont
    screenshot = pyautogui.screenshot()
    draw = ImageDraw.Draw(screenshot, "RGBA")
    width, height = screenshot.size
    
    cols = 10
    rows = 10
    col_width = width / cols
    row_height = height / rows
    
    for i in range(1, cols):
        x = int(i * col_width)
        draw.line([(x, 0), (x, height)], fill=(255, 0, 0, 120), width=2)
        
    for j in range(1, rows):
        y = int(j * row_height)
        draw.line([(0, y), (width, y)], fill=(255, 0, 0, 120), width=2)
        
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        font = ImageFont.load_default()
        
    for i in range(cols):
        col_label = chr(65 + i)
        for j in range(rows):
            row_label = str(j + 1)
            label = f"{col_label}{row_label}"
            
            cx = int((i + 0.5) * col_width)
            cy = int((j + 0.5) * row_height)
            
            r = 18
            draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(0, 0, 0, 180), outline=(255, 255, 255, 255), width=1)
            
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            except AttributeError:
                tw, th = draw.textsize(label, font=font) if hasattr(draw, 'textsize') else (14, 14)
            
            draw.text((cx - tw/2, cy - th/2 - 2), label, fill=(255, 255, 0, 255), font=font)
            
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return img_bytes

def get_grid_cell_center(cell_name):
    cell_name = cell_name.strip().upper()
    if len(cell_name) < 2:
        return None
    col_char = cell_name[0]
    row_str = cell_name[1:]
    
    if not ('A' <= col_char <= 'J'):
        return None
    try:
        row_num = int(row_str)
        if not (1 <= row_num <= 10):
            return None
    except ValueError:
        return None
        
    width, height = pyautogui.size()
    col_width = width / 10.0
    row_height = height / 10.0
    
    col_idx = ord(col_char) - 65
    row_idx = row_num - 1
    
    cx = int((col_idx + 0.5) * col_width)
    cy = int((row_idx + 0.5) * row_height)
    return cx, cy

# ─── SCHEDULER ENGINE ──────────────────────────────────
TASKS_FILE = os.path.join(CONFIG_DIR, "tasks.json")

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading tasks: {e}")
        return {}

def save_task(task):
    tasks = load_tasks()
    tasks[task["id"]] = task
    try:
        with open(TASKS_FILE, "w") as f:
            json.dump(tasks, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving task: {e}")

def remove_task(task_id):
    tasks = load_tasks()
    if task_id in tasks:
        del tasks[task_id]
        try:
            with open(TASKS_FILE, "w") as f:
                json.dump(tasks, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Error removing task: {e}")
            return False
    return False

async def execute_scheduled_task(t, bot):
    chat_id = t.get("chat_id")
    skill_name = t.get("action")
    parameters = t.get("action_parameters", {})
    
    mock_update = MockUpdate(bot, chat_id)
    mock_context = MockContext(bot)
    
    try:
        await bot.send_message(
            chat_id=chat_id, 
            text=f"⏰ *Executing Scheduled Task:* {t.get('name')}\nAction: `{skill_name}`",
            parse_mode="Markdown"
        )
        res = await execute_skill(skill_name, parameters, mock_update, mock_context)
        if res and res.get("output"):
            await bot.send_message(
                chat_id=chat_id,
                text=f"📋 *Task Output:*\n{res['output']}"
            )
    except Exception as e:
        logging.error(f"Error executing scheduled task {t.get('id')}: {e}")
        try:
            await bot.send_message(chat_id=chat_id, text=f"❌ *Failed to execute task '{t.get('name')}':* {e}", parse_mode="Markdown")
        except Exception:
            pass

# ─── MACRO REPLAY LOGIC & HELPERS ──────────────────────
MACROS_FILE = os.path.join(CONFIG_DIR, "macros.json")

def load_macros():
    if not os.path.exists(MACROS_FILE):
        return {}
    try:
        with open(MACROS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading macros: {e}")
        return {}

def save_macros(macros):
    try:
        with open(MACROS_FILE, "w") as f:
            json.dump(macros, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving macros: {e}")

async def replay_macro(events):
    from pynput import mouse, keyboard
    mouse_ctrl = mouse.Controller()
    keyboard_ctrl = keyboard.Controller()
    
    start_time = time.time()
    for ev in events:
        target_time = start_time + ev["time"]
        delay = target_time - time.time()
        if delay > 0:
            await asyncio.sleep(delay)
            
        ev_type = ev["type"]
        try:
            if ev_type == "click":
                mouse_ctrl.position = (ev["x"], ev["y"])
                button_name = ev.get("button", "left").lower()
                button = mouse.Button.left
                if button_name == "right":
                    button = mouse.Button.right
                elif button_name == "middle":
                    button = mouse.Button.middle
                mouse_ctrl.click(button)
            elif ev_type in ("key_down", "key_up"):
                key_name = ev["key"]
                key_obj = None
                if hasattr(keyboard.Key, key_name):
                    key_obj = getattr(keyboard.Key, key_name)
                elif len(key_name) == 1:
                    key_obj = key_name
                else:
                    key_obj = key_name
                
                if key_obj:
                    if ev_type == "key_down":
                        keyboard_ctrl.press(key_obj)
                    else:
                        keyboard_ctrl.release(key_obj)
        except Exception as e:
            logging.error(f"Error playing back event {ev}: {e}")

def calculate_next_daily_run(time_str):
    try:
        now = datetime.datetime.now()
        h, m = map(int, time_str.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return target.timestamp()
    except Exception as e:
        logging.error(f"Error calculating next daily run: {e}")
        return time.time() + 86400

def calculate_next_weekly_run(day_str, time_str):
    try:
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        target_day_idx = days.index(day_str.lower())
        
        now = datetime.datetime.now()
        h, m = map(int, time_str.split(":"))
        
        curr_day_idx = now.weekday()
        days_ahead = target_day_idx - curr_day_idx
        if days_ahead < 0:
            days_ahead += 7
        elif days_ahead == 0:
            target_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if target_time <= now:
                days_ahead = 7
                
        target = now.replace(hour=h, minute=m, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
        return target.timestamp()
    except Exception as e:
        logging.error(f"Error calculating next weekly run: {e}")
        return time.time() + 86400 * 7

async def run_task_scheduler(bot):
    logging.info("Starting background task scheduler...")
    while True:
        try:
            tasks = load_tasks()
            now = time.time()
            for t_id, t in list(tasks.items()):
                if not t.get("active", True):
                    continue
                next_run = t.get("next_run", 0)
                if now >= next_run:
                    asyncio.create_task(execute_scheduled_task(t, bot))
                    
                    t["last_run"] = now
                    if t.get("task_type") == "interval":
                        t["next_run"] = now + t.get("interval_seconds", 60)
                    elif t.get("task_type") == "daily":
                        t["next_run"] = calculate_next_daily_run(t.get("time_str", "00:00"))
                    elif t.get("task_type") == "weekly":
                        t["next_run"] = calculate_next_weekly_run(t.get("day_str", "Monday"), t.get("time_str", "00:00"))
                    else:
                        t["active"] = False
                    save_task(t)
        except Exception as e:
            logging.error(f"Error in task scheduler loop: {e}")
        await asyncio.sleep(10)

def make_system_prompt():
    today = datetime.date.today().isoformat()
    custom_skills = get_custom_skills_metadata()
    
    custom_skills_text = ""
    if custom_skills:
        custom_skills_text = "\nAvailable Custom Skills (Dynamic):\n"
        for cs in custom_skills:
            params_str = json.dumps(cs["parameters"])
            custom_skills_text += f"- {cs['name']}: {cs['description']}\n  Parameters: {params_str}\n"

    contacts = load_contacts()
    contacts_text = ""
    if contacts:
        contacts_text = "\nSaved Contacts (Address Book):\n"
        for name, phone in contacts.items():
            contacts_text += f"- {name}: {phone}\n"

    prompt = f"""You are a smart personal AI assistant on Telegram controlling the user's Windows PC.
You can talk to the user normally or execute skills/actions on their computer.

To reply normally, respond with a JSON object containing a "reply" field:
{{
  "thought": "Short chain-of-thought explaining what the user wants and what you will do.",
  "reply": "Your conversational response here."
}}

To execute a skill, respond with a JSON object containing "skill" and "parameters" fields:
{{
  "thought": "Short chain-of-thought.",
  "skill": "name_of_skill",
  "parameters": {{"param_name": "value"}}
}}

You can also combine a skill with a reply if you want to notify the user before running it (the reply will be sent before the skill runs):
{{
  "thought": "Short chain-of-thought.",
  "reply": "I am taking a screenshot for you...",
  "skill": "take_screenshot"
}}

CRITICAL: You must ALWAYS respond with a SINGLE valid JSON object. Do not include any text outside the JSON block (e.g. no markdown fences or intro/outro text).

List of available built-in skills:

1. open_app: Open an application or website.
   - target (string): The application name (e.g. "chrome", "notepad", "spotify", "vscode") or a website URL (e.g. "https://google.com").
   - Examples: {{"target": "chrome"}} or {{"target": "https://github.com"}}

2. lock_pc: Lock the Windows computer workstation.
   - (no parameters)

3. unlock_pc: Unlock the Windows computer workstation (simulates pressing keys and entering PIN).
   - (no parameters)

4. take_screenshot: Take a screenshot of the PC screen and send it.
   - (no parameters)

5. search_files: Search for files on the PC. The user will be presented with a list of matching files to download.
   - query (string): The search term or file extension.
   - search_type (string): Either "name" (for filename matches) or "extension" (for file extensions, e.g. "pdf", "mp3").
   - Examples: {{"query": "resume", "search_type": "name"}} or {{"query": "png", "search_type": "extension"}}

6. send_file: Directly upload/send a file from a specified PC path.
   - filepath (string): The absolute path to the file.
   - Example: {{"filepath": "C:\\\\Users\\\\flame\\\\Desktop\\\\document.pdf"}}

7. create_calendar_events: Add events or reminders to Google Calendar.
   - events (array of objects): A list of events to create. Each event has:
     - title (string): The title of the event.
     - date (string): The date in YYYY-MM-DD format.
     - time (string, optional): The start time in HH:MM format (24-hour).
     - description (string, optional): Extra description/notes.
   - Example: {{"events": [{{"title": "Dentist", "date": "2026-06-25", "time": "14:30"}}]}}

8. run_command: Execute a command in the Windows Command Prompt (cmd.exe) and see the output.
   - command (string): The command line to execute.
   - Example: {{"command": "ipconfig"}}

9. read_file: Read the content of a text-based file from the computer.
   - filepath (string): The absolute path to the file.
   - Example: {{"filepath": "C:\\\\Users\\\\flame\\\\Documents\\\\todo.txt"}}

10. write_file: Write text content to a file on the computer.
    - filepath (string): The absolute path to the file.
    - content (string): The content to write.
    - Example: {{"filepath": "C:\\\\Users\\\\flame\\\\Desktop\\\\notes.txt", "content": "Hello world!"}}

11. media_control: Control media playback or system volume.
    - action (string): One of: "play_pause", "next", "prev", "volume_up", "volume_down", "mute".
    - Example: {{"action": "play_pause"}}

12. create_custom_skill: Create a new custom skill/command for this AI Assistant. You should write a python script that implements a run(parameters, update, context) function.
    - name (string): The name of the skill, e.g. "get_weather" (alphanumeric and underscores only).
    - description (string): Explain what the skill does and what parameters it takes.
    - code (string): The complete Python code. It must define:
      def run(parameters, update, context):
          # your logic here
          # return a string or dict {{"output": "...", "feed_back_to_ai": True}}
    - parameters_schema (object, optional): A JSON object describing the parameter names and types.
    - Example: {{"name": "get_weather", "description": "Get current weather for a city.", "code": "import requests\\ndef run(parameters, update, context):\\n    city = parameters.get('city', 'New York')\\n    r = requests.get(f'https://wttr.in/{{city}}?format=3')\\n    return r.text", "parameters_schema": {{"city": "string"}}}}

13. set_reminder: Set a reminder/timer for a specific relative time.
    - delay_seconds (number): Seconds from now until the reminder should trigger.
    - message (string): The reminder message.
    - Example: {{"delay_seconds": 600, "message": "Check the oven"}}

14. send_whatsapp: Send a WhatsApp message to a specific phone number.
    - phone (string): Recipient's phone number with country code (e.g. "+1234567890"). If the user specifies a saved contact name (e.g. "Mom"), look it up in the Saved Contacts list first to resolve the phone number.
    - message (string): The text message to send.
    - Example: {{"phone": "+1234567890", "message": "Hey, I am on my way"}}

15. save_contact: Save a new contact name and phone number to the local address book.
    - name (string): The contact's name (e.g. "John" or "Mom").
    - phone (string): The contact's phone number.
    - Example: {{"name": "mom", "phone": "+919876543210"}}

16. get_clipboard: Get the text currently copied to the Windows clipboard.
    - (no parameters)

17. set_clipboard: Copy a specified text to the Windows clipboard.
    - text (string): The text content to set on the clipboard.

18. take_grid_screenshot: Take a screenshot of the PC screen overlaid with a coordinate grid (A1-J10) to let the user select where they want to click.
    - (no parameters)

19. grid_click: Click at the center of a specified cell coordinate from the grid screenshot (A1 to J10).
    - cell (string): The grid coordinate to click (e.g., "A1", "B5").
    - click_type (string, optional): One of "single", "double", or "right". Default is "single".

20. mouse_click: Click at specific screen coordinates specified as percentages of screen width and height.
    - x_pct (number): X coordinate from 0 to 100.
    - y_pct (number): Y coordinate from 0 to 100.
    - click_type (string, optional): One of "single", "double", or "right". Default is "single".

21. keyboard_input: Type text or press key/shortcut combinations on the computer.
    - text (string, optional): The text to type.
    - keys (array of strings, optional): The list of keys to press/hold in combination (e.g. ["ctrl", "c"] or ["win", "d"] or ["enter"]).

22. schedule_task: Schedule a task/action to be executed automatically in the background at a specific interval or delay.
    - name (string): Descriptive name for this scheduled task.
    - task_type (string): Either "one_off" or "interval".
    - delay_seconds (number): Time delay or interval period in seconds.
    - action (string): The name of the skill to execute (e.g., "take_screenshot", "run_command").
    - action_parameters (object, optional): Parameters to pass to the action.

23. list_tasks: List all currently active scheduled tasks.
    - (no parameters)

24. delete_task: Cancel/delete an active scheduled task.
    - task_id (string): The ID of the task to delete.

25. run_macro: Play back a recorded mouse and keyboard macro.
    - macro_name (string): The name of the macro to replay (e.g. "my_macro").

{custom_skills_text}{contacts_text}
Today's date is: {today}
"""
    return prompt

def parse_json_response(reply):
    clean = reply.strip()
    if clean.startswith("```"):
        match = re.search(r'```(?:json)?\s*(.*?)\s*```', clean, re.DOTALL)
        if match:
            clean = match.group(1).strip()
    if not (clean.startswith("{") and clean.endswith("}")):
        match = re.search(r'(\{.*\})', clean, re.DOTALL)
        if match:
            clean = match.group(1).strip()
    return json.loads(clean)

async def execute_skill(skill_name, parameters, update, context):
    """Execute built-in or custom skills."""
    logging.info(f"Executing skill '{skill_name}' with parameters {parameters}")
    
    # Check custom skills first
    custom_skills = get_custom_skills_metadata()
    custom_skill_names = [cs["name"] for cs in custom_skills]
    if skill_name in custom_skill_names:
        return execute_custom_skill(skill_name, parameters, update, context)
        
    # Built-in skills
    if skill_name == "open_app":
        target = parameters.get("target")
        if not target:
            return {"output": "Error: Missing parameter 'target'.", "feed_back_to_ai": True}
        res = open_app_or_website(target)
        return {"output": res, "feed_back_to_ai": True}
        
    elif skill_name == "lock_pc":
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        import time
        time.sleep(1.5)
        try:
            img_bytes = take_screenshot()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_bytes,
                caption="🔒 PC is locked!"
            )
        except Exception:
            await update.message.reply_text("🔒 PC is locked! (Screenshot protected by Windows)")
        return {"output": "PC locked successfully.", "feed_back_to_ai": True}
        
    elif skill_name == "unlock_pc":
        await update.message.reply_text("🔓 Sending unlock keystrokes...")
        import time
        pyautogui.press('space')
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(2)
        pyautogui.write('0603018720')
        time.sleep(2)
        try:
            img_bytes = take_screenshot()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_bytes,
                caption="🖥️ Screen unlocked!"
            )
            return {"output": "Screen unlocked successfully.", "feed_back_to_ai": True}
        except Exception:
            return {"output": "Unlock keystrokes sent, but could not take a screenshot.", "feed_back_to_ai": True}
            
    elif skill_name == "take_screenshot":
        await update.message.reply_text("📸 Taking screenshot...")
        try:
            img_bytes = take_screenshot()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_bytes,
                caption="🖥️ Here's your screen!"
            )
            return {"output": "Screenshot sent successfully.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error taking screenshot: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "search_files":
        query = parameters.get("query")
        search_type = parameters.get("search_type", "name")
        if not query:
            return {"output": "Error: Missing parameter 'query'.", "feed_back_to_ai": True}
            
        found_files = search_files_raw(query, search_type)
        if not found_files:
            return {"output": f"No files found matching '{query}'", "feed_back_to_ai": True}
            
        uid = update.effective_user.id
        search_results[uid] = found_files
        
        keyboard = []
        for i, filepath in enumerate(found_files):
            filename = os.path.basename(filepath)
            size = os.path.getsize(filepath)
            size_str = f"{size // 1024 // 1024} MB" if size >= 1024 * 1024 else f"{size // 1024} KB"
            keyboard.append([InlineKeyboardButton(
                f"{i+1}. {filename} ({size_str})",
                callback_data=f"file_{i}"
            )])
            
        await update.message.reply_text(
            f"📂 Found {len(found_files)} file(s). Pick one to download:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return {"output": f"Found {len(found_files)} files and presented selection buttons to the user.", "feed_back_to_ai": False}
        
    elif skill_name == "send_file":
        filepath = parameters.get("filepath")
        if not filepath:
            return {"output": "Error: Missing parameter 'filepath'.", "feed_back_to_ai": True}
        if not os.path.exists(filepath):
            return {"output": f"Error: File not found at '{filepath}'.", "feed_back_to_ai": True}
            
        filename = os.path.basename(filepath)
        try:
            size = os.path.getsize(filepath)
            if size > 50 * 1024 * 1024:
                return {"output": f"Error: File '{filename}' is too large. Telegram limit is 50 MB.", "feed_back_to_ai": True}
                
            await update.message.reply_text(f"📤 Sending {filename}...")
            with open(filepath, "rb") as f:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=f,
                    filename=filename,
                    caption=f"📄 {filepath}"
                )
            return {"output": f"Successfully sent file '{filename}' to user.", "feed_back_to_ai": True}
        except PermissionError:
            return {"output": f"Error: Permission denied accessing '{filepath}'.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error sending file: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "create_calendar_events":
        events_list = parameters.get("events", [])
        if not events_list:
            return {"output": "Error: Missing or empty parameter 'events'.", "feed_back_to_ai": True}
            
        created, failed = create_multiple_events(events_list)
        msg = f"✅ Added {len(created)} event(s)!\n\n"
        for ev in created:
            safe_t = escape_md(ev['title'])
            safe_d = escape_md(ev['date'])
            safe_tm = escape_md(ev['time'])
            msg += f"• *{safe_t}* — {safe_d} {safe_tm}\n"
        if failed:
            safe_failed = "\n".join(escape_md(f) for f in failed)
            msg += f"\n❌ Failed to add:\n{safe_failed}"
            
        await update.message.reply_text(msg, parse_mode="MarkdownV2")
        return {"output": f"Successfully added {len(created)} calendar events.", "feed_back_to_ai": False}
        
    elif skill_name == "run_command":
        command = parameters.get("command")
        if not command:
            return {"output": "Error: Missing parameter 'command'.", "feed_back_to_ai": True}
            
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            combined_output = ""
            if result.stdout:
                combined_output += f"Output:\n{result.stdout}\n"
            if result.stderr:
                combined_output += f"Errors:\n{result.stderr}\n"
            if not combined_output:
                combined_output = "Command executed successfully with no output."
                
            if len(combined_output) > 2000:
                combined_output = combined_output[:2000] + "\n...[Output truncated]..."
            return {"output": combined_output, "feed_back_to_ai": True}
        except subprocess.TimeoutExpired:
            return {"output": "Error: Command timed out after 15 seconds.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error running command: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "read_file":
        filepath = parameters.get("filepath")
        if not filepath:
            return {"output": "Error: Missing parameter 'filepath'.", "feed_back_to_ai": True}
        if not os.path.exists(filepath):
            return {"output": f"Error: File not found at '{filepath}'.", "feed_back_to_ai": True}
            
        try:
            size = os.path.getsize(filepath)
            if size > 1 * 1024 * 1024:
                return {"output": f"Error: File too large to read. Max size is 1 MB.", "feed_back_to_ai": True}
                
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if len(content) > 3000:
                content = content[:3000] + "\n...[Content truncated]..."
            return {"output": f"File content of '{filepath}':\n{content}", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error reading file: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "write_file":
        filepath = parameters.get("filepath")
        content = parameters.get("content", "")
        if not filepath:
            return {"output": "Error: Missing parameter 'filepath'.", "feed_back_to_ai": True}
            
        try:
            dir_name = os.path.dirname(filepath)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"output": f"Successfully wrote file to '{filepath}'", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error writing file: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "media_control":
        action = parameters.get("action")
        if not action:
            return {"output": "Error: Missing parameter 'action'.", "feed_back_to_ai": True}
            
        valid_actions = {
            "play_pause": "playpause",
            "next": "nexttrack",
            "prev": "prevtrack",
            "volume_up": "volumeup",
            "volume_down": "volumedown",
            "mute": "volumemute"
        }
        if action not in valid_actions:
            return {"output": f"Error: Invalid action '{action}'.", "feed_back_to_ai": True}
            
        try:
            pyautogui.press(valid_actions[action])
            return {"output": f"Triggered media action '{action}'", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error triggering media: {e}", "feed_back_to_ai": True}
            
    elif skill_name == "create_custom_skill":
        global restart_pending
        name = parameters.get("name")
        description = parameters.get("description")
        code = parameters.get("code")
        schema = parameters.get("parameters_schema")
        
        if not name or not description or not code:
            return {"output": "Error: Missing 'name', 'description', or 'code' parameters.", "feed_back_to_ai": True}
            
        res = create_custom_skill(name, description, code, schema)
        if res.startswith("Success"):
            restart_pending = True
            return {"output": f"{res} The bot will restart to apply this new skill.", "feed_back_to_ai": True}
        else:
            return {"output": res, "feed_back_to_ai": True}
            
    elif skill_name == "set_reminder":
        delay_seconds = parameters.get("delay_seconds")
        message = parameters.get("message")
        if delay_seconds is None or not message:
            return {"output": "Error: Missing parameter 'delay_seconds' or 'message'.", "feed_back_to_ai": True}
            
        try:
            delay_seconds = int(delay_seconds)
        except ValueError:
            return {"output": "Error: 'delay_seconds' must be a valid integer.", "feed_back_to_ai": True}
            
        reminder_id = str(uuid.uuid4())[:8]
        target_timestamp = time.time() + delay_seconds
        
        reminder = {
            "id": reminder_id,
            "target_timestamp": target_timestamp,
            "message": message,
            "chat_id": update.effective_chat.id,
            "triggered": False
        }
        
        save_reminder(reminder)
        asyncio.create_task(schedule_reminder(reminder, context.bot))
        
        if delay_seconds < 60:
            delay_str = f"{delay_seconds} seconds"
        elif delay_seconds < 3600:
            delay_str = f"{delay_seconds // 60} minutes"
        else:
            delay_str = f"{delay_seconds // 3600} hours and {(delay_seconds % 3600) // 60} minutes"
            
        keyboard = [[
            InlineKeyboardButton("📅 Add to Google Calendar", callback_data=f"remcal_{reminder_id}")
        ]]
        
        safe_msg = escape_md(message)
        safe_delay = escape_md(delay_str)
        
        await update.effective_message.reply_text(
            f"🔔 *Reminder Set\\!*\n"
            f"I will remind you about *\"{safe_msg}\"* in {safe_delay}\\.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return {"output": f"Successfully set reminder to trigger in {delay_seconds} seconds.", "feed_back_to_ai": False}
        
    elif skill_name == "send_whatsapp":
        phone = parameters.get("phone")
        message = parameters.get("message")
        if not phone or not message:
            return {"output": "Error: Missing parameter 'phone' or 'message'.", "feed_back_to_ai": True}
            
        phone_clean = re.sub(r'[^\d+]', '', phone)
        quoted_msg = urllib.parse.quote(message)
        
        web_url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={quoted_msg}"
        import webbrowser
        webbrowser.open(web_url)
            
        safe_phone = escape_md(phone)
        safe_msg = escape_md(message)
        await update.effective_message.reply_text(
            f"📤 Opening WhatsApp Web to send message to `{safe_phone}`\\.\\.\\.\n"
            f"Message: *\"{safe_msg}\"*",
            parse_mode="MarkdownV2"
        )
        
        async def trigger_send_and_close():
            await asyncio.sleep(15)
            
            import pygetwindow as gw
            target_win = None
            try:
                for win in gw.getAllWindows():
                    if "whatsapp" in win.title.lower():
                        target_win = win
                        break
            except Exception as e:
                logging.error(f"Error listing windows for WhatsApp: {e}")
                
            if target_win:
                try:
                    if target_win.isMinimized:
                        target_win.restore()
                    target_win.activate()
                    await asyncio.sleep(1)
                except Exception as e:
                    logging.error(f"Error focusing WhatsApp window: {e}")
                
                pyautogui.press('enter')
                await asyncio.sleep(2)
                pyautogui.hotkey('ctrl', 'w')
            else:
                logging.warning("WhatsApp window not found, attempting fallback enter press.")
                pyautogui.press('enter')
            
        asyncio.create_task(trigger_send_and_close())
        return {"output": f"Opened WhatsApp Web to send message to {phone_clean} and scheduled window focus/send/close sequence.", "feed_back_to_ai": False}
        
    elif skill_name == "save_contact":
        name = parameters.get("name")
        phone = parameters.get("phone")
        if not name or not phone:
            return {"output": "Error: Missing parameter 'name' or 'phone'.", "feed_back_to_ai": True}
            
        success = save_contact_to_file(name, phone)
        if success:
            safe_name = escape_md(name)
            safe_phone = escape_md(phone)
            await update.effective_message.reply_text(
                f"👤 Contact saved\\!\n"
                f"• *Name:* {safe_name}\n"
                f"• *Phone:* `{safe_phone}`",
                parse_mode="MarkdownV2"
            )
            return {"output": f"Successfully saved contact '{name}' with phone '{phone}'.", "feed_back_to_ai": False}
        else:
            return {"output": "Error: Failed to write contact to file.", "feed_back_to_ai": True}
            
    elif skill_name == "get_clipboard":
        text = get_clipboard_text()
        return {"output": f"Clipboard content:\n{text}", "feed_back_to_ai": True}

    elif skill_name == "set_clipboard":
        text = parameters.get("text")
        if text is None:
            return {"output": "Error: Missing parameter 'text'.", "feed_back_to_ai": True}
        success = set_clipboard_text(text)
        if success:
            return {"output": "Successfully set clipboard content.", "feed_back_to_ai": True}
        else:
            return {"output": "Failed to set clipboard content.", "feed_back_to_ai": True}

    elif skill_name == "take_grid_screenshot":
        await update.message.reply_text("📸 Taking grid screenshot...")
        try:
            img_bytes = generate_grid_screenshot()
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_bytes,
                caption="🖥️ Labeled screen grid (A1-J10). Use the coordinates to click!"
            )
            return {"output": "Grid screenshot sent successfully.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error taking grid screenshot: {e}", "feed_back_to_ai": True}

    elif skill_name == "grid_click":
        cell = parameters.get("cell")
        click_type = parameters.get("click_type", "single")
        if not cell:
            return {"output": "Error: Missing parameter 'cell'.", "feed_back_to_ai": True}
        coords = get_grid_cell_center(cell)
        if not coords:
            return {"output": f"Error: Invalid cell label '{cell}'. Use A1-J10.", "feed_back_to_ai": True}
        
        cx, cy = coords
        try:
            if click_type == "double":
                pyautogui.doubleClick(cx, cy)
            elif click_type == "right":
                pyautogui.rightClick(cx, cy)
            else:
                pyautogui.click(cx, cy)
            return {"output": f"Successfully clicked {click_type} on grid cell {cell} ({cx}, {cy}).", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error performing grid click: {e}", "feed_back_to_ai": True}

    elif skill_name == "mouse_click":
        x_pct = parameters.get("x_pct")
        y_pct = parameters.get("y_pct")
        click_type = parameters.get("click_type", "single")
        if x_pct is None or y_pct is None:
            return {"output": "Error: Missing parameter 'x_pct' or 'y_pct'.", "feed_back_to_ai": True}
        try:
            width, height = pyautogui.size()
            cx = int(x_pct * width / 100.0)
            cy = int(y_pct * height / 100.0)
            if click_type == "double":
                pyautogui.doubleClick(cx, cy)
            elif click_type == "right":
                pyautogui.rightClick(cx, cy)
            else:
                pyautogui.click(cx, cy)
            return {"output": f"Successfully clicked {click_type} at coordinates ({cx}, {cy}) [{x_pct}%, {y_pct}%].", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error performing mouse click: {e}", "feed_back_to_ai": True}

    elif skill_name == "keyboard_input":
        text = parameters.get("text")
        keys = parameters.get("keys", [])
        if not text and not keys:
            return {"output": "Error: Missing both 'text' and 'keys' parameters.", "feed_back_to_ai": True}
        
        try:
            if text:
                pyautogui.write(text)
            if keys:
                if len(keys) == 1:
                    pyautogui.press(keys[0])
                else:
                    pyautogui.hotkey(*keys)
            return {"output": "Keyboard input executed successfully.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error executing keyboard input: {e}", "feed_back_to_ai": True}

    elif skill_name == "schedule_task":
        name = parameters.get("name")
        task_type = parameters.get("task_type")
        delay_seconds = parameters.get("delay_seconds")
        action = parameters.get("action")
        action_parameters = parameters.get("action_parameters", {})
        
        if not name or not task_type or delay_seconds is None or not action:
            return {"output": "Error: Missing 'name', 'task_type', 'delay_seconds', or 'action'.", "feed_back_to_ai": True}
            
        try:
            delay_seconds = int(delay_seconds)
        except ValueError:
            return {"output": "Error: 'delay_seconds' must be an integer.", "feed_back_to_ai": True}
            
        task_id = str(uuid.uuid4())[:8]
        next_run = time.time() + delay_seconds
        
        task = {
            "id": task_id,
            "name": name,
            "task_type": task_type,
            "interval_seconds": delay_seconds if task_type == "interval" else None,
            "action": action,
            "action_parameters": action_parameters,
            "chat_id": update.effective_chat.id,
            "next_run": next_run,
            "last_run": None,
            "active": True
        }
        
        save_task(task)
        return {"output": f"Successfully scheduled task '{name}' (ID: {task_id}). Runs in {delay_seconds} seconds.", "feed_back_to_ai": True}

    elif skill_name == "list_tasks":
        tasks = load_tasks()
        active_tasks = [t for t in tasks.values() if t.get("active", True)]
        if not active_tasks:
            return {"output": "No active scheduled tasks found.", "feed_back_to_ai": True}
            
        res_str = "Active Scheduled Tasks:\n"
        for t in active_tasks:
            next_run_dt = datetime.datetime.fromtimestamp(t['next_run']).strftime("%Y-%m-%d %H:%M:%S")
            res_str += f"- {t['name']} (ID: {t['id']}): Runs `{t['action']}`. Next run: {next_run_dt} (interval: {t.get('interval_seconds')}s)\n"
        return {"output": res_str, "feed_back_to_ai": True}

    elif skill_name == "delete_task":
        task_id = parameters.get("task_id")
        if not task_id:
            return {"output": "Error: Missing 'task_id'.", "feed_back_to_ai": True}
        success = remove_task(task_id)
        if success:
            return {"output": f"Successfully deleted task {task_id}.", "feed_back_to_ai": True}
        else:
            return {"output": f"Error: Task with ID {task_id} not found.", "feed_back_to_ai": True}

    elif skill_name == "run_macro":
        macro_name = parameters.get("macro_name")
        if not macro_name:
            return {"output": "Error: Missing parameter 'macro_name'.", "feed_back_to_ai": True}
        macros = load_macros()
        macro = macros.get(macro_name)
        if not macro:
            return {"output": f"Error: Macro '{macro_name}' not found.", "feed_back_to_ai": True}
            
        await update.message.reply_text(f"🎬 Playing back macro '{macro_name}'...")
        try:
            await replay_macro(macro.get("events", []))
            return {"output": f"Macro '{macro_name}' completed playback successfully.", "feed_back_to_ai": True}
        except Exception as e:
            return {"output": f"Error replaying macro: {e}", "feed_back_to_ai": True}

    else:
        return {"output": f"Error: Skill '{skill_name}' is not registered.", "feed_back_to_ai": True}

# ─── PROCESS AI REPLY ──────────────────────────────────
async def process_reply(reply, update, context):
    try:
        clean = reply.strip()
        clean = clean.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(clean)

        if data.get("action") == "create_event":
            link = create_calendar_event(
                data["title"], data["date"],
                data.get("time"), data.get("description", "")
            )
            safe_title = escape_md(data['title'])
            safe_date = escape_md(data['date'])
            safe_time = escape_md(data.get('time', 'All day'))
            await update.message.reply_text(
                f"✅ Added to Google Calendar\\!\n"
                f"📅 *{safe_title}*\n"
                f"🗓 {safe_date} {safe_time}\n"
                f"🔗 [View event]({link})",
                parse_mode="MarkdownV2"
            )
            return True

        if data.get("action") == "create_multiple_events" or data.get("action") == "create_calendar_events":
            events_list = data.get("events", [])
            await update.message.reply_text(
                f"📅 Adding {len(events_list)} events to Google Calendar..."
            )
            created, failed = create_multiple_events(events_list)
            msg = f"✅ Added {len(created)} events\\!\n\n"
            for ev in created:
                safe_t = escape_md(ev['title'])
                safe_d = escape_md(ev['date'])
                safe_tm = escape_md(ev['time'])
                msg += f"• *{safe_t}* \— {safe_d} {safe_tm}\n"
            if failed:
                safe_failed = "\n".join(escape_md(f) for f in failed)
                msg += f"\n❌ Failed to add:\n{safe_failed}"
            await update.message.reply_text(msg, parse_mode="MarkdownV2")
            return True

    except Exception:
        pass

    return False

# ─── IMAGE HANDLER ─────────────────────────────────────
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    caption = update.message.caption or ""
    await update.message.reply_text(
        "🔍 Reading your image with AI vision\\.\\.\\.\n"
        "_\\(This may take a few seconds\\)_",
        parse_mode="MarkdownV2"
    )
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Download image
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    img_bytes = io.BytesIO()
    await file.download_to_memory(img_bytes)
    img_bytes.seek(0)

    try:
        # Unified vision analysis
        result_text = analyze_image_with_vision(img_bytes, caption)
        
        uid = update.effective_user.id
        if uid not in histories:
            histories[uid] = []
            
        try:
            data = parse_json_response(result_text)
        except Exception as json_err:
            logging.error(f"Failed to parse vision response as JSON: {json_err}. Raw: {result_text}")
            # Fallback: treat raw response as text reply
            histories[uid].append({"role": "user", "content": f"[Uploaded Image] {caption}".strip()})
            histories[uid].append({"role": "assistant", "content": result_text})
            await update.message.reply_text(result_text)
            return

        is_calendar = data.get("is_calendar_event", False)
        
        if is_calendar and data.get("events"):
            events_list = data.get("events", [])
            # Format and show events
            msg = f"📅 Detected {len(events_list)} event(s) to add:\n"
            for ev in events_list:
                msg += f"• *{ev.get('title')}* — {ev.get('date')} {ev.get('time', 'All day')}\n"
            await update.message.reply_text(msg)
            
            # Now add events to calendar
            created, failed = create_multiple_events(events_list)
            gcal_msg = f"✅ Added {len(created)} event(s) to Google Calendar\\!\n\n"
            for ev in created:
                safe_t = escape_md(ev['title'])
                safe_d = escape_md(ev['date'])
                safe_tm = escape_md(ev['time'])
                gcal_msg += f"• *{safe_t}* \— {safe_d} {safe_tm}\n"
            if failed:
                safe_failed = "\n".join(escape_md(f) for f in failed)
                gcal_msg += f"\n❌ Failed to add:\n{safe_failed}"
            await update.message.reply_text(gcal_msg, parse_mode="MarkdownV2")
            
            # Also record in history
            histories[uid].append({"role": "user", "content": f"[Uploaded Calendar Image] {caption}".strip()})
            histories[uid].append({"role": "assistant", "content": f"Added {len(created)} events to calendar."})
        else:
            # It's a general question/analysis
            response_text = data.get("response", "")
            if not response_text:
                response_text = "I analyzed the image but didn't find any calendar events, and no question was asked."
            
            # Send reply
            await update.message.reply_text(response_text)
            
            # Record in history
            histories[uid].append({"role": "user", "content": f"[Uploaded Image] {caption}".strip()})
            histories[uid].append({"role": "assistant", "content": response_text})

    except requests.HTTPError as e:
        await update.message.reply_text(f"⚠️ Vision API error: {e}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error processing image: {e}")

# ─── CHAT HANDLER ──────────────────────────────────────
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global restart_pending
    if not await is_authorized(update):
        return
    uid = update.effective_user.id
    user_msg = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    if uid not in histories:
        histories[uid] = []
        
    histories[uid].append({"role": "user", "content": user_msg})
    
    max_iterations = 5
    current_iteration = 0
    restart_pending = False
    
    messages_base = [{"role": "system", "content": make_system_prompt()}]
    
    while current_iteration < max_iterations:
        messages = messages_base + histories[uid][-20:]
        
        try:
            reply = call_nvidia(messages)
        except requests.HTTPError as e:
            await update.message.reply_text(f"⚠️ API error: {e}")
            return
            
        logging.info(f"LLM Reply: {reply}")
        
        parsed_data = None
        try:
            parsed_data = parse_json_response(reply)
        except Exception:
            pass
            
        if not parsed_data:
            histories[uid].append({"role": "assistant", "content": reply})
            await update.message.reply_text(reply)
            break
            
        histories[uid].append({"role": "assistant", "content": reply})
        
        reply_text = parsed_data.get("reply")
        skill_name = parsed_data.get("skill")
        parameters = parsed_data.get("parameters", {})
        
        if reply_text:
            await update.message.reply_text(reply_text)
            
        if skill_name:
            if not reply_text:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action="typing"
                )
                
            skill_result = await execute_skill(skill_name, parameters, update, context)
            
            if skill_result.get("feed_back_to_ai"):
                histories[uid].append({
                    "role": "user",
                    "content": f"Skill '{skill_name}' output:\n{skill_result['output']}"
                })
                current_iteration += 1
                continue
            else:
                break
        else:
            break
            
    if restart_pending:
        import time
        time.sleep(2)
        restart_bot()

# ─── START HANDLER ─────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    await update.message.reply_text(
        "👋 Hi! I'm your AI assistant.\n\n"
        "📸 *Send any image* — I'll read it and add events to your calendar!\n\n"
        "💻 *Computer control:*\n"
        "• 'Lock/Unlock PC'\n"
        "• 'Open Chrome' / 'Open youtube.com'\n"
        "• 'Take a screenshot'\n"
        "• 'Find resume.pdf'\n\n"
        "📅 *Calendar:*\n"
        "• 'Dentist this Friday at 3pm'\n\n"
        "💬 Or just chat with me!",
        parse_mode="Markdown"
    )

# ─── REMINDER CALENDAR CALLBACK ────────────────────────
async def reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid != AUTHORIZED_CHAT_ID:
        return
        
    data = query.data  # e.g. "remcal_abc123"
    reminder_id = data.split("_")[1]
    
    reminders = load_reminders()
    reminder = reminders.get(reminder_id)
    if not reminder:
        await query.edit_message_text("❌ Reminder not found or expired.")
        return
        
    # Extract date and time
    target_dt = datetime.datetime.fromtimestamp(reminder["target_timestamp"])
    date_str = target_dt.strftime("%Y-%m-%d")
    time_str = target_dt.strftime("%H:%M")
    title = f"Reminder: {reminder['message']}"
    
    await query.edit_message_text("📅 Adding to Google Calendar...")
    
    try:
        # Create event in Google Calendar
        link = create_calendar_event(title, date_str, time_str)
        safe_title = escape_md(title)
        safe_date = escape_md(date_str)
        safe_time = escape_md(time_str)
        
        await query.edit_message_text(
            f"✅ Added to Google Calendar\\!\n"
            f"📅 *{safe_title}*\n"
            f"🗓 {safe_date} {safe_time}\n"
            f"🔗 [View event]({link})",
            parse_mode="MarkdownV2"
        )
    except Exception as e:
        logging.error(f"Error adding reminder to calendar: {e}")
        await query.edit_message_text(f"❌ Failed to add to Calendar: {e}")

# ─── FILE SELECTION CALLBACK ───────────────────────────
async def file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if AUTHORIZED_CHAT_ID is None:
        save_authorized_chat_id(uid)
        await query.message.reply_text(f"🔒 Owner Registered! ID: {uid}")
    elif uid != AUTHORIZED_CHAT_ID:
        return
    data = query.data  # e.g. "file_3"

    if not data.startswith("file_") or uid not in search_results:
        await query.edit_message_text("❌ Session expired. Please search again.")
        return

    idx = int(data.split("_")[1])
    files = search_results[uid]

    if idx < 0 or idx >= len(files):
        await query.edit_message_text("❌ Invalid selection.")
        return

    filepath = files[idx]
    filename = os.path.basename(filepath)

    try:
        size = os.path.getsize(filepath)
        if size > 50 * 1024 * 1024:
            await query.edit_message_text(
                f"⚠️ {filename} is too large ({size // 1024 // 1024} MB).\n"
                f"Telegram limit is 50 MB."
            )
            return

        await query.edit_message_text(f"📤 Sending {filename}...")
        with open(filepath, "rb") as f:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=f,
                filename=filename,
                caption=f"📄 {filepath}"
            )
    except PermissionError:
        await query.edit_message_text(f"🔒 No permission to access: {filepath}")
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

# ─── FILE DOWNLOAD HANDLER ─────────────────────────────
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    uid = update.effective_user.id

    doc = update.message.document
    filename = doc.file_name
    file_size = doc.file_size

    # Telegram bot API limit is 20MB for downloads
    if file_size > 20 * 1024 * 1024:
        await update.message.reply_text(
            f"⚠️ File too large ({file_size // 1024 // 1024}MB).\n"
            f"Telegram bots can only receive files up to 20MB."
        )
        return

    # Choose download location
    download_dir = os.path.expanduser("~/Downloads")
    os.makedirs(download_dir, exist_ok=True)
    save_path = os.path.join(download_dir, filename)

    # Handle duplicate filenames
    if os.path.exists(save_path):
        name, ext = os.path.splitext(filename)
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        save_path = os.path.join(download_dir, f"{name}_{timestamp}{ext}")

    await update.message.reply_text(f"⬇️ Downloading *{filename}*...", parse_mode="Markdown")

    try:
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(save_path)
        size_str = f"{file_size // 1024}KB" if file_size < 1024*1024 else f"{file_size // 1024 // 1024}MB"
        await update.message.reply_text(
            f"✅ Saved to your PC!\n"
            f"📄 *{os.path.basename(save_path)}*\n"
            f"📁 `{save_path}`\n"
            f"💾 {size_str}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to download: {e}")

# ─── MAIN ──────────────────────────────────────────────
def wait_for_internet():
    import socket
    logging.info("Checking internet connection...")
    logged_waiting = False
    while True:
        try:
            with socket.create_connection(("oauth2.googleapis.com", 443), timeout=3):
                logging.info("Internet connection detected. Continuing bot startup...")
                return
        except Exception:
            if not logged_waiting:
                logging.info("Offline. Waiting for internet connection to restore...")
                logged_waiting = True
            time.sleep(5)

def stop_bot():
    logging.info("Stopping bot...")
    os._exit(0)

def cleanup_old_version():
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    old_exe = os.path.join(exe_dir, "bot.exe.old")
    old_py = os.path.join(exe_dir, "bot.py.old")
    for old_file in [old_exe, old_py]:
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                logging.info(f"Cleaned up old version file: {old_file}")
            except Exception as e:
                logging.warning(f"Could not remove old version file {old_file}: {e}")

def restart_bot():
    logging.info("Restarting bot process...")
    if getattr(sys, 'frozen', False):
        subprocess.Popen([sys.executable] + sys.argv[1:])
    else:
        subprocess.Popen([sys.executable, __file__] + sys.argv[1:])
    os._exit(0)

if __name__ == "__main__":
    # Start system tray icon in a background thread
    from tray_icon import BotTrayIcon
    tray = BotTrayIcon(CONFIG_DIR, stop_callback=stop_bot, restart_callback=restart_bot)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # Start the bot
    if not TELEGRAM_TOKEN or not NVIDIA_API_KEY:
        logging.error("Configuration missing. Exiting.")
        sys.exit(1)
        
    wait_for_internet()
    cleanup_old_version()
    init_calendar()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(file_callback, pattern="^file_"))
    app.add_handler(CallbackQueryHandler(reminder_callback, pattern="^remcal_"))
    app.add_handler(CommandHandler("checkupdate", check_update_command))
    app.add_handler(CallbackQueryHandler(update_callback, pattern="^update_bot$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logging.info("✅ Bot running — Vision OCR + Calendar + Computer Control")
    app.run_polling()