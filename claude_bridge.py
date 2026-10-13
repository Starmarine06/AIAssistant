"""Bridge to the Claude Code CLI installed on this machine (headless `claude -p`)."""
import os, sys, json, shutil, asyncio, logging, subprocess

import llm_providers as cfgstore

PERMISSION_MODES = ["default", "acceptEdits", "plan", "bypassPermissions"]
DEFAULT_MODE = "acceptEdits"
TIMEOUT_SECONDS = 30 * 60

_running = {}  # uid -> asyncio subprocess


def find_claude():
    path = shutil.which("claude")
    if path:
        return path
    candidates = [
        os.path.expanduser("~/.local/bin/claude.exe"),
        os.path.expanduser("~/.local/bin/claude"),
        os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd"),
        "/usr/local/bin/claude",
    ]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def get_settings():
    cfg = cfgstore.cfg_read()
    cwd = cfg.get("claude_cwd") or os.path.expanduser("~")
    if not os.path.isdir(cwd):
        cwd = os.path.expanduser("~")
    mode = cfg.get("claude_permission_mode")
    return {
        "cwd": cwd,
        "mode": mode if mode in PERMISSION_MODES else DEFAULT_MODE,
        "session_id": cfg.get("claude_session_id"),
        "chat_mode": bool(cfg.get("claude_chat_mode")),
    }


def is_running(uid):
    proc = _running.get(uid)
    return proc is not None and proc.returncode is None


async def stop(uid):
    proc = _running.get(uid)
    if proc is None or proc.returncode is not None:
        return False
    if sys.platform == "win32":
        # claude.exe may spawn children; kill the whole tree
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        proc.kill()
    return True


def _summarize_tool(block):
    name = block.get("name", "tool")
    inp = block.get("input") or {}
    detail = (inp.get("command") or inp.get("file_path") or inp.get("pattern")
              or inp.get("path") or inp.get("url") or inp.get("description") or "")
    detail = str(detail).replace("\n", " ")[:80]
    return f"🔧 {name}: {detail}" if detail else f"🔧 {name}"


async def run(uid, prompt, on_progress=None, permission_mode=None, resume=True):
    """Run one Claude Code task. Returns a dict: ok, text, session_id, cost, turns, denials, error."""
    exe = find_claude()
    if not exe:
        return {"ok": False, "error": "Claude Code CLI not found. Install it and make sure `claude` is on PATH."}
    if is_running(uid):
        return {"ok": False, "error": "A Claude Code task is already running. Use /claude stop to cancel it."}

    s = get_settings()
    mode = permission_mode or s["mode"]
    cmd = [exe, "-p", "--output-format", "stream-json", "--verbose", "--permission-mode", mode]
    if resume and s["session_id"]:
        cmd += ["--resume", s["session_id"]]

    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=s["cwd"],
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        limit=32 * 1024 * 1024, **kwargs,
    )
    _running[uid] = proc
    logging.info(f"Claude Code started (pid {proc.pid}, mode {mode}, cwd {s['cwd']})")

    result = {"ok": False, "text": "", "session_id": None, "cost": None, "turns": None, "denials": [], "error": None}
    stderr_task = asyncio.create_task(proc.stderr.read())

    async def pump():
        proc.stdin.write(prompt.encode("utf-8"))
        await proc.stdin.drain()
        proc.stdin.close()
        async for raw in proc.stdout:
            try:
                ev = json.loads(raw.decode("utf-8", "replace"))
            except json.JSONDecodeError:
                continue
            kind = ev.get("type")
            if kind == "system" and ev.get("session_id"):
                result["session_id"] = ev["session_id"]
            elif kind == "assistant" and on_progress:
                for block in (ev.get("message") or {}).get("content") or []:
                    if block.get("type") == "tool_use":
                        try:
                            await on_progress(_summarize_tool(block))
                        except Exception as e:
                            logging.warning(f"Progress callback failed: {e}")
            elif kind == "result":
                result["text"] = ev.get("result") or ""
                result["session_id"] = ev.get("session_id") or result["session_id"]
                result["cost"] = ev.get("total_cost_usd")
                result["turns"] = ev.get("num_turns")
                result["denials"] = ev.get("permission_denials") or []
                result["ok"] = not ev.get("is_error")
                if not result["ok"] and not result["text"]:
                    result["error"] = ev.get("subtype") or "Claude Code reported an error"

    try:
        await asyncio.wait_for(pump(), timeout=TIMEOUT_SECONDS)
        await proc.wait()
    except asyncio.TimeoutError:
        await stop(uid)
        result.update(ok=False, error=f"Timed out after {TIMEOUT_SECONDS // 60} minutes.")
    except Exception as e:
        logging.exception("Claude Code bridge error")
        await stop(uid)
        result.update(ok=False, error=str(e))
    finally:
        _running.pop(uid, None)

    err = (await stderr_task).decode("utf-8", "replace").strip()
    if not result["ok"] and not result["text"] and not result["error"]:
        result["error"] = err[-800:] or ("Stopped." if proc.returncode else "No output from Claude Code.")

    if result["session_id"]:
        cfgstore.cfg_update(claude_session_id=result["session_id"])
    return result
