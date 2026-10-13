"""Commit and push a project folder to its own private GitHub repo (via git + the gh CLI)."""
import os, re, sys, shutil, logging, subprocess

import llm_providers as cfgstore

DEFAULT_GITIGNORE = """# secrets
.env
.env.*
*.pem
*.key
credentials.json
token.json

# dependencies / build output
node_modules/
__pycache__/
*.pyc
.venv/
venv/
dist/
build/
.DS_Store
"""

_owner_cache = None


def enabled():
    cfg = cfgstore.cfg_read()
    if "github_sync" in cfg:
        return bool(cfg["github_sync"])
    return os.getenv("GITHUB_SYNC", "").lower() in ("1", "true", "yes")


def _run(args, cwd=None, check=True):
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=180, **kwargs)
    if check and r.returncode != 0:
        detail = (r.stderr or r.stdout).strip()[-300:]
        raise RuntimeError(f"{' '.join(args[:3])} failed: {detail}")
    return r


def check_ready():
    """Return an error string if git/gh aren't usable, else None."""
    if not shutil.which("git"):
        return "git is not installed."
    if not shutil.which("gh"):
        return "GitHub CLI (gh) is not installed."
    if _run(["gh", "auth", "status"], check=False).returncode != 0:
        return "GitHub CLI isn't signed in (set GH_TOKEN, or run `gh auth login`)."
    return None


def owner():
    global _owner_cache
    if os.getenv("GITHUB_OWNER"):
        return os.environ["GITHUB_OWNER"]
    if not _owner_cache:
        _owner_cache = _run(["gh", "api", "user", "-q", ".login"]).stdout.strip()
    return _owner_cache


def repo_name(folder):
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(os.path.normpath(folder))).strip("-.")
    return name or "project"


def remote_url(folder):
    r = _run(["git", "remote", "get-url", "origin"], cwd=folder, check=False)
    return r.stdout.strip() if r.returncode == 0 else None


def _ensure_identity(folder):
    if _run(["git", "config", "user.name"], cwd=folder, check=False).stdout.strip():
        return
    login = owner()
    name = os.getenv("GIT_USER_NAME") or login
    email = os.getenv("GIT_USER_EMAIL")
    if not email:
        uid = _run(["gh", "api", "user", "-q", ".id"]).stdout.strip()
        email = f"{uid}+{login}@users.noreply.github.com"
    _run(["git", "config", "user.name", name], cwd=folder)
    _run(["git", "config", "user.email", email], cwd=folder)


def sync(folder, message):
    """Init the repo if needed, create the GitHub repo if needed, commit and push.

    Returns {"url", "created", "committed", "pushed"}; raises RuntimeError with a readable message on failure.
    """
    err = check_ready()
    if err:
        raise RuntimeError(err)

    if not os.path.isdir(os.path.join(folder, ".git")):
        _run(["git", "init", "-b", "main"], cwd=folder)
    gitignore = os.path.join(folder, ".gitignore")
    if not os.path.exists(gitignore):
        with open(gitignore, "w", encoding="utf-8") as f:
            f.write(DEFAULT_GITIGNORE)
    _ensure_identity(folder)

    created = False
    url = remote_url(folder)
    if not url:
        full = f"{owner()}/{repo_name(folder)}"
        if _run(["gh", "repo", "view", full], check=False).returncode != 0:
            _run(["gh", "repo", "create", full, "--private", "--description", "Created by AI Assistant"])
            created = True
        url = f"https://github.com/{full}.git"
        _run(["git", "remote", "add", "origin", url], cwd=folder)

    _run(["git", "add", "-A"], cwd=folder)
    committed = False
    if _run(["git", "status", "--porcelain"], cwd=folder).stdout.strip():
        _run(["git", "commit", "-m", message[:200]], cwd=folder)
        committed = True

    pushed = False
    if _run(["git", "rev-parse", "HEAD"], cwd=folder, check=False).returncode == 0:
        _run(["git", "push", "-u", "origin", "HEAD"], cwd=folder)
        pushed = True

    web = re.sub(r"\.git$", "", url)
    logging.info(f"GitHub sync {folder}: created={created} committed={committed} pushed={pushed}")
    return {"url": web, "created": created, "committed": committed, "pushed": pushed}
