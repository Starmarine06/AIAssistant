# AI Assistant

Lightweight Telegram bot + PC controller to help schedule events, control apps, and record macros on Windows.

**Quick start**

1. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create Google credentials and bot config:

- Copy `credentials.example.json` → `credentials.json` and fill values from your Google Cloud Console.
- Do NOT commit `credentials.json` or `token.json` — they are ignored by `.gitignore`.

4. Run the settings GUI to configure tokens and import `credentials.json`:

```powershell
python settings_gui.py
```

5. Start the bot:

```powershell
python bot.py
```

Contributing: open a PR. The repository includes a basic GitHub Actions workflow for CI.
