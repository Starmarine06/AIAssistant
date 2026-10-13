"""Headless project agent for TrueNAS / Docker: Telegram -> Claude Code -> GitHub.

No PC-control skills here (screenshots, mouse, WhatsApp...) - those need a desktop.
"""
import os, sys, logging

DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
logging.getLogger("httpx").setLevel(logging.WARNING)

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import llm_providers
import claude_bridge
import agent_core

llm_providers.init(DATA_DIR)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
histories = {}

SYSTEM_PROMPT = ("You are the chat side of a headless project agent running on a home server. The user manages software "
                 "projects from Telegram: /project <name> picks a project, they send a plan.md, then Critique, Design and "
                 "Implement it with Claude Code, and the code is pushed to GitHub. Be brief. For real coding work, tell "
                 "them to use /claude <task> or /claude on.")


def owner_id():
    env = os.getenv("AUTHORIZED_CHAT_ID")
    if env and env.isdigit():
        return int(env)
    return llm_providers.cfg_read().get("authorized_chat_id")


async def is_authorized(update: Update):
    if update.effective_user is None:
        return False
    uid = update.effective_user.id
    owner = owner_id()
    if owner is None:
        # first user to talk to the bot becomes the owner (set AUTHORIZED_CHAT_ID to avoid this)
        llm_providers.cfg_update(authorized_chat_id=uid)
        if update.effective_message:
            await update.effective_message.reply_text(f"🔒 Owner registered: {uid}. Everyone else is blocked.")
        return True
    return uid == owner


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    s = claude_bridge.get_settings()
    await update.message.reply_text(
        "👋 Project agent online.\n\n"
        "📂 /projects — list projects, /project <name> — switch or create\n"
        "📝 Send a plan.md — then Critique, Design, Implement\n"
        "🤖 /claude <task> — run Claude Code (chat mode is "
        f"{'ON: every message goes to Claude Code' if s['chat_mode'] else 'off'})\n"
        "🐙 /github — repo sync status\n"
        "🧠 /provider, /model — chat model (NVIDIA / Groq / OpenRouter)")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    chat_id = update.effective_chat.id
    text = update.message.text
    if claude_bridge.get_settings()["chat_mode"]:
        if not agent_core.project_dir():
            await update.message.reply_text("📁 Pick a project first: /project <name>")
            return
        if not agent_core.start_claude_task(context.bot, chat_id, text):
            await update.message.reply_text("⏳ Claude Code is still working. /claude stop to cancel.")
        return
    hist = histories.setdefault(chat_id, [])
    hist.append({"role": "user", "content": text})
    try:
        import asyncio
        reply = await asyncio.to_thread(
            llm_providers.chat_completion, [{"role": "system", "content": SYSTEM_PROMPT}] + hist[-20:])
    except Exception as e:
        await update.message.reply_text(f"⚠️ LLM error: {e}")
        return
    hist.append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply or "(empty reply)")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    doc = update.message.document
    name = os.path.basename(doc.file_name or "file")
    chat_id = update.effective_chat.id
    if not agent_core.project_dir():
        await update.message.reply_text("📁 Pick a project first with /project <name>, then send the file again.")
        return
    if (doc.file_size or 0) > 20 * 1024 * 1024:
        await update.message.reply_text("⚠️ Telegram bots can only receive files up to 20MB.")
        return
    data = bytes(await (await context.bot.get_file(doc.file_id)).download_as_bytearray())
    if name.lower().endswith((".md", ".markdown")):
        target = agent_core.save_plan_document(name, data)
        await update.message.reply_text(f"📝 Plan saved:\n{target}\n\nWhat should I do with it?",
                                        reply_markup=agent_core.plan_buttons())
        await agent_core.sync_project(context.bot, chat_id, f"Add {name}")
    else:
        target = os.path.join(agent_core.project_dir(), name)
        with open(target, "wb") as f:
            f.write(data)
        await update.message.reply_text(f"📄 Saved to the project: {target}")


def main():
    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_TOKEN is not set.")
        sys.exit(1)
    if not llm_providers.has_any_key():
        logging.warning("No NVIDIA/Groq/OpenRouter key set - plain chat is disabled, Claude Code still works.")

    cfg = llm_providers.cfg_read()
    defaults = {}
    if "claude_chat_mode" not in cfg:
        defaults["claude_chat_mode"] = True  # headless agent: messages go straight to Claude Code
    if "claude_permission_mode" not in cfg:
        # No one is at the keyboard to approve prompts; the container is the sandbox.
        defaults["claude_permission_mode"] = os.getenv("CLAUDE_PERMISSION_MODE", "bypassPermissions")
    if defaults:
        llm_providers.cfg_update(**defaults)
    if not claude_bridge.find_claude():
        logging.error("Claude Code CLI not found in the container.")

    agent_core.configure(is_authorized, owner_id)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    agent_core.register(app)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    logging.info("Project agent running.")
    app.run_polling()


if __name__ == "__main__":
    main()
