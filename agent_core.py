"""Telegram handlers shared by the Windows bot and the headless NAS bot:
LLM provider/model selection, Claude Code bridge, plan workflow and GitHub sync."""
import os, time, asyncio, logging, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

import llm_providers
import claude_bridge
import github_sync

_is_authorized = None
_owner_id = lambda: None

def configure(is_authorized, owner_id):
    """is_authorized: async fn(update) -> bool; owner_id: fn() -> authorized chat id (or None)."""
    global _is_authorized, _owner_id
    _is_authorized, _owner_id = is_authorized, owner_id

# ─── PROVIDER / MODEL SELECTION ────────────────────────
OR_PAGE_SIZE = 8

def _cb_authorized(query):
    return _owner_id() is not None and query.from_user.id == _owner_id()

def provider_menu():
    cfg = llm_providers.cfg_read()
    active, _ = llm_providers.get_active(cfg)
    rows = []
    for p, info in llm_providers.PROVIDERS.items():
        mark = "✅ " if p == active else ""
        no_key = "" if llm_providers.get_key(p, cfg) else " (no key)"
        rows.append([InlineKeyboardButton(f"{mark}{info['label']}{no_key}", callback_data=f"prov_{p}")])
    if llm_providers.get_key("openrouter", cfg):
        rows.append([InlineKeyboardButton("🔀 Choose OpenRouter model", callback_data="orm_0")])
    text = (f"🧠 Active: {llm_providers.describe_active()}\n\n"
            "Tap a provider to switch. Add a key with:\n/setkey <nvidia|groq|openrouter> <key>")
    return text, InlineKeyboardMarkup(rows)

async def provider_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    text, markup = provider_menu()
    await update.message.reply_text(text, reply_markup=markup)

async def setkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    args = context.args or []
    if len(args) != 2 or args[0].lower() not in llm_providers.PROVIDERS:
        await update.message.reply_text("Usage: /setkey <nvidia|groq|openrouter> <api key>")
        return
    provider, key = args[0].lower(), args[1].strip()
    try:
        await update.message.delete()  # don't leave the key sitting in chat history
    except Exception:
        pass
    cfg = llm_providers.cfg_read()
    updates = {f"{provider}_api_key": key}
    if not cfg.get("provider") or not llm_providers.get_key(cfg.get("provider"), cfg):
        updates["provider"] = provider
    llm_providers.cfg_update(**updates)
    await context.bot.send_message(update.effective_chat.id,
                                   f"🔑 {llm_providers.PROVIDERS[provider]['label']} key saved (your message was deleted).\n"
                                   f"Active: {llm_providers.describe_active()}")

def _or_view(ud):
    models = llm_providers.list_openrouter_models()
    q = (ud.get("or_query") or "").lower()
    free = ud.get("or_free", False)
    found = [m for m in models if (not free or m["free"]) and (q in m["id"].lower() or q in m["name"].lower())]
    ud["or_list"] = [m["id"] for m in found]
    return found

def or_render(ud, page):
    found = _or_view(ud)
    pages = max(1, (len(found) + OR_PAGE_SIZE - 1) // OR_PAGE_SIZE)
    page = min(max(page, 0), pages - 1)
    current = llm_providers.get_model("openrouter")
    rows = []
    for i in range(page * OR_PAGE_SIZE, min(len(found), (page + 1) * OR_PAGE_SIZE)):
        m = found[i]
        label = ("✅ " if m["id"] == current else "") + ("🆓 " if m["free"] else "") + m["id"]
        rows.append([InlineKeyboardButton(label[:60], callback_data=f"orms_{i}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀", callback_data=f"orm_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{pages}", callback_data="orm_noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton("▶", callback_data=f"orm_{page+1}"))
    rows.append(nav)
    free = ud.get("or_free", False)
    rows.append([InlineKeyboardButton("Show all" if free else "🆓 Free only", callback_data=f"orf_{0 if free else 1}")])
    filt = f' matching "{ud["or_query"]}"' if ud.get("or_query") else ""
    text = (f"🔀 OpenRouter models{filt}: {len(found)} found\nCurrent: {current}\n"
            "Search with /model <text> (e.g. /model claude).")
    return text, InlineKeyboardMarkup(rows)

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    provider, _ = llm_providers.get_active()
    if provider != "openrouter":
        await update.message.reply_text(
            f"Model selection is only available on OpenRouter. Active: {llm_providers.describe_active()}\n"
            "Use /provider to switch.")
        return
    context.user_data["or_query"] = " ".join(context.args or [])
    context.user_data["or_free"] = False
    try:
        text, markup = or_render(context.user_data, 0)
    except Exception as e:
        await update.message.reply_text(f"❌ Couldn't fetch OpenRouter models: {e}")
        return
    await update.message.reply_text(text, reply_markup=markup)

async def provider_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _cb_authorized(query):
        await query.answer()
        return
    data = query.data
    if data == "orm_noop":
        await query.answer()
        return
    if data.startswith("prov_"):
        provider = data[5:]
        if provider not in llm_providers.PROVIDERS or not llm_providers.get_key(provider):
            await query.answer("No API key for that provider. Use /setkey.", show_alert=True)
            return
        llm_providers.cfg_update(provider=provider)
        await query.answer(f"Switched to {llm_providers.PROVIDERS[provider]['label']}")
        if provider == "openrouter":
            context.user_data["or_query"], context.user_data["or_free"] = "", False
            try:
                text, markup = or_render(context.user_data, 0)
                await query.edit_message_text(text, reply_markup=markup)
                return
            except Exception as e:
                logging.error(f"OpenRouter model list failed: {e}")
        text, markup = provider_menu()
        await query.edit_message_text(text, reply_markup=markup)
        return
    await query.answer()
    try:
        if data.startswith("orms_"):
            idx = int(data[5:])
            ids = context.user_data.get("or_list") or []
            if idx >= len(ids):
                await query.edit_message_text("Session expired. Run /model again.")
                return
            llm_providers.cfg_update(openrouter_model=ids[idx], provider="openrouter")
            await query.edit_message_text(f"✅ Model set: {ids[idx]}\nActive: {llm_providers.describe_active()}")
            return
        if data.startswith("orf_"):
            context.user_data["or_free"] = data[4:] == "1"
            page = 0
        else:
            page = int(data[4:])
        text, markup = or_render(context.user_data, page)
        await query.edit_message_text(text, reply_markup=markup)
    except Exception as e:
        logging.error(f"Model picker error: {e}")

# ─── GITHUB SYNC ───────────────────────────────────────
async def sync_project(bot, chat_id, message):
    """Commit + push the project folder to its own GitHub repo, if sync is enabled."""
    folder = project_dir()
    if not folder or not github_sync.enabled():
        return
    try:
        r = await asyncio.to_thread(github_sync.sync, folder, message)
    except Exception as e:
        logging.error(f"GitHub sync failed: {e}")
        await bot.send_message(chat_id, f"⚠️ GitHub sync failed: {e}")
        return
    if r["pushed"]:
        note = "created repo and pushed" if r["created"] else ("pushed changes" if r["committed"] else "already up to date")
        await bot.send_message(chat_id, f"⬆️ GitHub: {note}\n{r['url']}")

async def github_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    sub = (context.args[0].lower() if context.args else "")
    if sub in ("on", "off"):
        llm_providers.cfg_update(github_sync=(sub == "on"))
    err = github_sync.check_ready()
    folder = project_dir()
    remote = await asyncio.to_thread(github_sync.remote_url, folder) if folder and os.path.isdir(os.path.join(folder, ".git")) else None
    try:
        who = await asyncio.to_thread(github_sync.owner) if not err else "-"
    except Exception:
        who = "-"
    planned = f"will be created as {who}/{github_sync.repo_name(folder)}" if folder and not err else "none yet"
    lines = [
        f"🐙 GitHub sync: {'ON' if github_sync.enabled() else 'off'}",
        f"Account: {who}",
        f"Project: {folder or 'not set'}",
        f"Repo: {remote or planned}",
    ]
    if err:
        lines.append(f"⚠️ {err}")
    lines.append("")
    lines.append("/github on | off — auto commit + push after every task")
    await update.message.reply_text("\n".join(lines))

# ─── CLAUDE CODE BRIDGE ────────────────────────────────
cc_last_prompt = {}

def _split_message(text, n=3900):
    text = text or "(no output)"
    return [text[i:i + n] for i in range(0, len(text), n)]

async def run_claude_task(bot, chat_id, prompt, permission_mode=None, save_as=None):
    """Run a Claude Code task and report progress/result back to Telegram."""
    status = await bot.send_message(chat_id, "🤖 Claude Code is working...")
    state = {"lines": [], "t": 0.0}

    async def progress(line):
        state["lines"].append(line)
        if time.time() - state["t"] >= 3:
            state["t"] = time.time()
            await status.edit_text("🤖 Claude Code is working...\n" + "\n".join(state["lines"][-6:]))

    cc_last_prompt[chat_id] = prompt
    res = await claude_bridge.run(chat_id, prompt, progress, permission_mode)

    footer = ""
    if res.get("turns") is not None:
        footer = f"{res['turns']} turns" + (f" · ${res['cost']:.2f}" if res.get("cost") else "")
    try:
        await status.edit_text(("✅ Claude Code finished" if res["ok"] else "⚠️ Claude Code stopped") + (f" ({footer})" if footer else ""))
    except Exception:
        pass

    body = res["text"] if res["text"] else f"❌ {res.get('error')}"
    for chunk in _split_message(body):
        await bot.send_message(chat_id, chunk)

    if save_as and res["ok"] and res["text"]:
        try:
            target = os.path.join(project_dir(), save_as)
            with open(target, "w", encoding="utf-8") as f:
                f.write(res["text"])
            await bot.send_message(chat_id, f"💾 Saved to {target}",
                                   reply_markup=plan_buttons(after=save_as))
        except Exception as e:
            await bot.send_message(chat_id, f"⚠️ Couldn't save {save_as}: {e}")

    if res["ok"]:
        await sync_project(bot, chat_id, f"Claude Code: {prompt.strip().splitlines()[0][:70]}")

    if res.get("denials"):
        lines = []
        for d in res["denials"][:5]:
            inp = d.get("tool_input") or {}
            detail = str(inp.get("command") or inp.get("file_path") or "")[:80]
            lines.append(f"• {d.get('tool_name')}: {detail}")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔓 Re-run with full permissions", callback_data="ccbypass")]])
        await bot.send_message(chat_id, "🔒 Claude Code was blocked from:\n" + "\n".join(lines), reply_markup=keyboard)

_cc_tasks = set()

def start_claude_task(bot, chat_id, prompt, permission_mode=None, save_as=None):
    if claude_bridge.is_running(chat_id):
        return False
    task = asyncio.create_task(run_claude_task(bot, chat_id, prompt, permission_mode, save_as))
    _cc_tasks.add(task)  # keep a reference so it isn't garbage-collected mid-run
    task.add_done_callback(_cc_tasks.discard)
    return True

async def claude_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    chat_id = update.effective_chat.id
    args = context.args or []
    sub = args[0].lower() if args else ""
    s = claude_bridge.get_settings()

    if not args:
        found = claude_bridge.find_claude()
        await update.message.reply_text(
            "🤖 Claude Code bridge\n"
            f"CLI: {found or 'NOT FOUND'}\n"
            f"Folder: {s['cwd']}\n"
            f"Permissions: {s['mode']}\n"
            f"Session: {'continuing ' + s['session_id'][:8] if s['session_id'] else 'new'}\n"
            f"Chat mode: {'ON (every message goes to Claude Code)' if s['chat_mode'] else 'off'}\n\n"
            "/claude <task> — run a task\n"
            "/claude on | off — route all messages to Claude Code\n"
            "/claude cd <folder> — set working folder\n"
            "/claude mode <default|acceptEdits|plan|bypassPermissions>\n"
            "/claude new — start a fresh session\n"
            "/claude stop — cancel the running task")
    elif sub == "stop":
        stopped = await claude_bridge.stop(chat_id)
        await update.message.reply_text("🛑 Stopping Claude Code..." if stopped else "Nothing is running.")
    elif sub == "new":
        llm_providers.cfg_update(claude_session_id=None)
        await update.message.reply_text("🆕 Next task starts a fresh Claude Code session.")
    elif sub in ("on", "off"):
        llm_providers.cfg_update(claude_chat_mode=(sub == "on"))
        await update.message.reply_text("💬 Chat mode ON — your messages now go straight to Claude Code. /claude off to return."
                                        if sub == "on" else "💬 Chat mode off.")
    elif sub == "cd":
        path = os.path.abspath(os.path.expandvars(os.path.expanduser(" ".join(args[1:]))))
        if len(args) < 2 or not os.path.isdir(path):
            await update.message.reply_text(f"❌ Not a folder: {path if len(args) > 1 else '(none given)'}")
        else:
            llm_providers.cfg_update(claude_cwd=path, claude_session_id=None)
            await update.message.reply_text(f"📁 Working folder: {path}\n(new session)")
    elif sub == "mode":
        mode = args[1] if len(args) > 1 else ""
        if mode not in claude_bridge.PERMISSION_MODES:
            await update.message.reply_text("Modes: " + ", ".join(claude_bridge.PERMISSION_MODES))
        else:
            llm_providers.cfg_update(claude_permission_mode=mode)
            warn = "\n⚠️ Claude Code can run any command without asking." if mode == "bypassPermissions" else ""
            await update.message.reply_text(f"🔐 Permission mode: {mode}{warn}")
    else:
        if not start_claude_task(context.bot, chat_id, " ".join(args)):
            await update.message.reply_text("⏳ A task is already running. /claude stop to cancel it.")

async def claude_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _cb_authorized(query):
        return
    chat_id = query.message.chat_id
    prompt = cc_last_prompt.get(chat_id)
    if not prompt:
        await query.edit_message_text("Nothing to re-run.")
        return
    await query.edit_message_text("🔓 Re-running with full permissions...")
    if not start_claude_task(context.bot, chat_id, prompt, "bypassPermissions"):
        await context.bot.send_message(chat_id, "⏳ A task is already running.")

# ─── PROJECT + PLAN WORKFLOW ───────────────────────────
PLAN_REVIEW = "plan-review.md"
PLAN_DESIGN = "plan-design.md"
PLAN_PROGRESS = "PROGRESS.md"

def project_dir():
    d = llm_providers.cfg_read().get("project_dir")
    return d if d and os.path.isdir(d) else None

def plan_file():
    """Path of the saved plan in the project folder, or None."""
    d = project_dir()
    name = llm_providers.cfg_read().get("plan_file") or "plan.md"
    path = os.path.join(d, name) if d else None
    return path if path and os.path.exists(path) else None

def plan_buttons(after=None):
    rows = [[InlineKeyboardButton("🧐 Critique", callback_data="plan_review"),
             InlineKeyboardButton("🗺 Design", callback_data="plan_design")],
            [InlineKeyboardButton("🚀 Implement", callback_data="plan_implement")]]
    return InlineKeyboardMarkup(rows)

def plan_prompt(action, extra=""):
    plan = os.path.basename(plan_file())
    ctx = []
    if os.path.exists(os.path.join(project_dir(), PLAN_REVIEW)):
        ctx.append(PLAN_REVIEW)
    if os.path.exists(os.path.join(project_dir(), PLAN_DESIGN)):
        ctx.append(PLAN_DESIGN)
    extra = f"\n\nExtra instructions from the user: {extra}" if extra else ""
    if action == "review":
        body = (f"Read {plan} in this project. Give a constructive critique: gaps and missing requirements, "
                "ambiguities, risks, questionable technical choices, scope or ordering problems, and what is "
                "hard to test. Rank issues by severity, be specific, and for each propose a concrete improvement. "
                "Also say what is already good. Do not write any code. Reply with the review as markdown.")
    elif action == "design":
        body = (f"Read {plan}" + (f" and {', '.join(ctx)}" if ctx else "") + " in this project and inspect any existing code. "
                "Produce a detailed implementation design as markdown: architecture and components, file/folder "
                "structure, data models and interfaces, key decisions with trade-offs, how it will be tested, and an "
                "ordered milestone breakdown as a checklist (- [ ] items). Address the critique if one exists. "
                "Do not write code yet.")
    else:
        body = (f"Implement {plan} in this project" + (f", following {', '.join(ctx)}" if ctx else "") + ". "
                f"Work milestone by milestone, run tests as you go, and keep a checklist of progress in {PLAN_PROGRESS}. "
                "If something in the plan is unclear or conflicts, make the most reasonable choice and note it in "
                f"{PLAN_PROGRESS}. Finish with a short summary of what was built, what is left, and how to run it.")
    return body + extra

def start_plan_action(bot, chat_id, action, extra=""):
    """Returns an error string, or None if the task was started."""
    if not project_dir():
        return "No project folder set. Use /project <folder> first."
    if not plan_file():
        return "No plan saved yet. Send me a plan.md file."
    if not claude_bridge.find_claude():
        return "Claude Code CLI not found on this PC."
    mode = "plan" if action in ("review", "design") else None
    save_as = {"review": PLAN_REVIEW, "design": PLAN_DESIGN}.get(action)
    if not start_claude_task(bot, chat_id, plan_prompt(action, extra), mode, save_as):
        return "A Claude Code task is already running. /claude stop to cancel it."
    return None

async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    arg = " ".join(context.args or []).strip()
    if arg:
        root = os.getenv("PROJECTS_ROOT")
        if root:
            # Server mode: every project is its own folder (and repo) inside the projects root, nowhere else
            root = os.path.realpath(root)
            path = os.path.realpath(os.path.join(root, arg.strip('"')))
            if os.path.dirname(path) != root:
                await update.message.reply_text("❌ Use a plain project name, e.g. /project my-app")
                return
        else:
            path = os.path.abspath(os.path.expandvars(os.path.expanduser(arg.strip('"'))))
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            await update.message.reply_text(f"❌ Can't use that folder: {e}")
            return
        # The project folder is also where Claude Code works; a new folder means a new session
        llm_providers.cfg_update(project_dir=path, claude_cwd=path, claude_session_id=None)
        await update.message.reply_text(f"📁 Project folder set:\n{path}\n\nSend me a plan.md and I'll save it there.")
        return
    d = project_dir()
    pf = plan_file()
    await update.message.reply_text(
        f"📁 Project: {d or 'not set'}\n📝 Plan: {pf or 'none saved'}\n\n"
        "/project <folder> — set (or create) the project folder\n"
        "/plan — plan actions\n/plan show — send me the plan",
        reply_markup=plan_buttons() if pf else None)

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    chat_id = update.effective_chat.id
    args = context.args or []
    sub = args[0].lower() if args else ""
    if sub in ("review", "design", "implement"):
        err = start_plan_action(context.bot, chat_id, sub, " ".join(args[1:]))
        if err:
            await update.message.reply_text(f"❌ {err}")
        return
    pf = plan_file()
    if sub == "show":
        if not pf:
            await update.message.reply_text("No plan saved yet.")
            return
        with open(pf, "r", encoding="utf-8", errors="replace") as f:
            for chunk in _split_message(f.read()):
                await context.bot.send_message(chat_id, chunk)
        return
    await update.message.reply_text(
        f"📝 Plan: {pf or 'none saved - send me a plan.md'}\n📁 Project: {project_dir() or 'not set (/project <folder>)'}\n\n"
        "🧐 Critique — constructive review, saved to plan-review.md\n"
        "🗺 Design — architecture + milestones, saved to plan-design.md\n"
        "🚀 Implement — builds it in the project folder\n\n"
        "Add instructions with e.g. /plan implement only milestone 1",
        reply_markup=plan_buttons() if pf else None)

async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not _cb_authorized(query):
        return
    action = query.data[5:]
    err = start_plan_action(context.bot, query.message.chat_id, action)
    if err:
        await context.bot.send_message(query.message.chat_id, f"❌ {err}")

async def projects_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_authorized(update):
        return
    root = os.getenv("PROJECTS_ROOT")
    if not root or not os.path.isdir(root):
        await update.message.reply_text("No projects root configured. Set /project <folder> directly.")
        return
    cur = project_dir()
    names = sorted(n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n)) and not n.startswith("."))
    lines = [("👉 " if os.path.join(root, n) == cur else "• ") + n for n in names]
    listing = "\n".join(lines) if lines else "(none yet)"
    await update.message.reply_text(f"📂 Projects:\n{listing}\n\n/project <name> — switch or create")

def save_plan_document(filename, data):
    """Save an uploaded markdown plan into the project folder, backing up any previous one."""
    d = project_dir()
    target = os.path.join(d, filename)
    if os.path.exists(target):
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        os.replace(target, os.path.join(d, f"{filename}.{stamp}.bak"))
    with open(target, "wb") as f:
        f.write(data)
    llm_providers.cfg_update(plan_file=filename)
    return target



def register(app):
    """Register all shared handlers on a telegram Application."""
    app.add_handler(CommandHandler("provider", provider_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("setkey", setkey_command))
    app.add_handler(CommandHandler("claude", claude_command))
    app.add_handler(CommandHandler("project", project_command))
    app.add_handler(CommandHandler("projects", projects_command))
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("github", github_command))
    app.add_handler(CallbackQueryHandler(provider_callback, pattern="^(prov_|orm_|orms_|orf_)"))
    app.add_handler(CallbackQueryHandler(claude_callback, pattern="^ccbypass$"))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern="^plan_"))
