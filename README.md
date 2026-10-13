# AI Assistant

<p align="center">
  <video src="https://github.com/user-attachments/assets/ae858151-cdcf-460c-bbfe-1b32e27a3f3d" poster="https://raw.githubusercontent.com/Starmarine06/AIAssistant/main/promo-video/assets/promo-poster.png" width="70%" autoplay loop muted playsinline></video>
</p>

AI Assistant is a Windows-based personal assistant that runs a Telegram bot and system tray application. Powered by an LLM via NVIDIA, Groq or OpenRouter, it allows you to control your PC, run macros, schedule tasks, and integrate with Google Calendar and WhatsApp.

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
- **Claude Code from Telegram**:
  - `/claude <task>` runs Claude Code headlessly on your PC (needs the `claude` CLI installed and logged in), streams tool-call progress, and sends back the result. Follow-up tasks continue the same session.
  - `/claude on` / `off` routes every message to Claude Code; `/claude cd <folder>`, `/claude mode <default|acceptEdits|plan|bypassPermissions>`, `/claude new`, `/claude stop`.
  - Default permission mode is `acceptEdits`. If Claude Code is blocked from something (e.g. a shell command), the bot offers a one-tap "Re-run with full permissions" button.
  - You can also just ask in plain language ("have Claude Code fix the tests in my project").
- **Plan workflow**:
  - `/project <folder>` sets (and creates, if needed) the project folder. Claude Code also works in this folder.
  - Send a `plan.md` (any `.md` file) to the bot and it is saved into the project folder; an existing plan is backed up as `plan.md.<timestamp>.bak`.
  - Buttons (or `/plan review|design|implement [extra instructions]`): **Critique** gives a ranked, constructive review saved to `plan-review.md`; **Design** produces architecture and a milestone checklist saved to `plan-design.md`; **Implement** builds it in the project folder, tracking progress in `PROGRESS.md`. Critique and Design run in Claude Code's read-only plan mode. `/plan show` sends the plan back to you.
- **Multiple LLM providers**:
  - `/provider` switches between NVIDIA, Groq and OpenRouter; `/setkey <provider> <key>` stores a key (and deletes your message).
  - With OpenRouter active, `/model [search]` lists all OpenRouter models (with a free-only filter) so you can pick one.
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
- **NVIDIA, Groq and/or OpenRouter API Key** (at least one, for LLM reasoning).
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
