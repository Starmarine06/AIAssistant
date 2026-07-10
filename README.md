# AI Assistant

AI Assistant is a Windows-based personal assistant that runs a Telegram bot and system tray application. Powered by an LLM via NVIDIA's API, it allows you to control your PC, run macros, schedule tasks, and integrate with Google Calendar and WhatsApp.

---

## Key Features

- **PC Automation & Control**:
  - Run terminal commands (`cmd.exe`).
  - Open applications, files, or websites.
  - Lock or unlock your Windows workstation.
  - View, copy, or update the clipboard.
- **Mouse & Keyboard Simulation**:
  - Coordinate percentage-based mouse clicks and keyboard typing/shortcuts.
  - Grid screenshots overlaying a coordinate grid (A1-J10) to click precisely where you need.
- **File Management**:
  - Search files by name or extension.
  - Read/write text files and download files directly to your device via Telegram.
- **Productivity & Scheduler**:
  - Google Calendar integration to schedule single or multiple events/reminders.
  - Background task scheduler supporting one-off and periodic interval tasks.
  - Custom reminders/timers with relative delays.
  - Local Address Book: Save contacts and send WhatsApp messages.
- **Custom Skills**:
  - Dynamically register and run Python scripts to execute custom logic.
- **Tray Icon & Settings GUI**:
  - System Tray menu allows quick access to view logs, open the AppData data folder, launch the Configuration GUI, start the Macro Recorder, or exit.

---

## Installation & Setup

Choose one of the two setup methods below:

### Option A: Standard Setup (Development / Source Mode)

#### 1. Setup Virtual Environment
Ensure you have Python 3.8+ installed on your Windows machine, then run:

```powershell
# Clone the repository and navigate into the folder
cd AIAssistant

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

#### 2. Configuration
Run the Settings GUI to configure your credentials:
```powershell
python settings_gui.py
```
This GUI allows you to enter:
- **Telegram Bot Token** (obtain from `@BotFather`).
- **NVIDIA API Key** (for LLM reasoning).
- **Google Calendar Credentials** (importing a `credentials.json` file from Google Cloud Console).

#### 3. Start the Bot
Run the bot via Python:
```powershell
python bot.py
```
- If the configuration is missing, the Settings GUI will automatically launch.
- A system tray icon will appear in the Windows notification area.

---

### Option B: Executable Setup (Release / Installer Mode)

You can compile the app into a standalone Windows installer.

#### 1. Compile the Binaries
With dependencies installed in your virtual environment, run:
```powershell
python build_release.py
```
This compiles two executables using PyInstaller:
- `bot.exe` (Standalone bot backend)
- `AIAssistant_Setup.exe` (CustomTkinter Setup Wizard bundling `bot.exe`)

Both executables will be generated in the `dist/` directory and copied to the repository root.

#### 2. Run the Installer
Launch `AIAssistant_Setup.exe` to open the setup wizard:
- Select the installation directory (defaults to `%USERPROFILE%\AppData\Local\Programs\AIAssistant`).
- Opt to launch AI Assistant automatically when Windows boots.
- Start the application immediately after installation.

---

## Security & First-Time Use

AI Assistant is private by default to prevent unauthorized users from controlling your computer.

1. Once the bot starts for the first time, send it any message on Telegram.
2. The bot will automatically register your Telegram account as the **Owner** and save your Chat ID.
3. Once registered, all messages from other Telegram accounts are blocked.

---

## Configuration & Data Storage

- **Source Mode**: Configuration files (`config.json`, `macros.json`, `tasks.json`, `reminders.json`, `contacts.json`, `token.json`, `credentials.json`) are stored directly in the repository folder.
- **Compiled/Installed Mode**: Configuration files and logs are stored globally under `%APPDATA%\AIAssistant\`.
