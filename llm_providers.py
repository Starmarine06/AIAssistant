"""LLM provider layer: NVIDIA, Groq and OpenRouter (all OpenAI-compatible)."""
import os, json, time, logging, requests

PROVIDERS = {
    "nvidia": {
        "label": "NVIDIA",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "default_model": "meta/llama-3.3-70b-instruct",
        "vision_model": "meta/llama-3.2-90b-vision-instruct",
        "env": "NVIDIA_API_KEY",
    },
    "groq": {
        "label": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "default_model": "llama-3.3-70b-versatile",
        "vision_model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "env": "GROQ_API_KEY",
    },
    "openrouter": {
        "label": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "vision_model": None,  # uses the selected model
        "env": "OPENROUTER_API_KEY",
    },
}

_config_dir = None
_models_cache = {"ts": 0, "models": []}


def init(config_dir):
    global _config_dir
    _config_dir = config_dir


def _config_path():
    return os.path.join(_config_dir, "config.json")


def cfg_read():
    try:
        with open(_config_path(), "r") as f:
            return json.load(f)
    except Exception:
        return {}


def cfg_update(**kv):
    data = cfg_read()
    data.update(kv)
    with open(_config_path(), "w") as f:
        json.dump(data, f, indent=4)


def _legacy_provider(key):
    """Old configs stored any provider's key in nvidia_api_key; sniff by prefix."""
    if key and key.startswith("gsk_"):
        return "groq"
    if key and key.startswith("sk-or-"):
        return "openrouter"
    return "nvidia"


def get_key(provider, cfg=None):
    cfg = cfg if cfg is not None else cfg_read()
    key = cfg.get(f"{provider}_api_key") or os.getenv(PROVIDERS[provider]["env"])
    legacy = cfg.get("nvidia_api_key")
    if not key and legacy and _legacy_provider(legacy) == provider:
        key = legacy
    return key or None


def configured_providers(cfg=None):
    cfg = cfg if cfg is not None else cfg_read()
    return [p for p in PROVIDERS if get_key(p, cfg)]


def has_any_key():
    return bool(configured_providers())


def get_active(cfg=None):
    """Return (provider, key). Falls back to the first provider that has a key."""
    cfg = cfg if cfg is not None else cfg_read()
    wanted = cfg.get("provider")
    if wanted in PROVIDERS and get_key(wanted, cfg):
        return wanted, get_key(wanted, cfg)
    legacy = cfg.get("nvidia_api_key")
    if legacy and not wanted:
        p = _legacy_provider(legacy)
        return p, get_key(p, cfg)
    for p in PROVIDERS:
        if get_key(p, cfg):
            return p, get_key(p, cfg)
    return None, None


def get_model(provider, cfg=None):
    cfg = cfg if cfg is not None else cfg_read()
    if provider == "openrouter":
        return cfg.get("openrouter_model") or PROVIDERS[provider]["default_model"]
    return PROVIDERS[provider]["default_model"]


def describe_active():
    provider, key = get_active()
    if not provider:
        return "No provider configured"
    return f"{PROVIDERS[provider]['label']} · {get_model(provider)}"


def _headers(provider, key):
    h = {"Authorization": f"Bearer {key}", "Accept": "text/event-stream"}
    if provider == "openrouter":
        h["HTTP-Referer"] = "https://github.com/Starmarine06/AIAssistant"
        h["X-Title"] = "AI Assistant"
    return h


def chat_completion(messages, vision=False, temperature=0.7, max_tokens=1024):
    """Stream a chat completion from the active provider and return the full text."""
    cfg = cfg_read()
    provider, key = get_active(cfg)
    if not provider:
        raise RuntimeError("No LLM API key configured. Add one in Settings.")
    info = PROVIDERS[provider]
    model = get_model(provider, cfg)
    if vision and info["vision_model"]:
        model = info["vision_model"]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }
    resp = requests.post(info["url"], headers=_headers(provider, key), json=payload, stream=True, timeout=30)
    resp.raise_for_status()

    full = ""
    for line in resp.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if decoded.startswith("data: "):
            decoded = decoded[6:]
        if decoded == "[DONE]":
            break
        try:
            delta = json.loads(decoded)["choices"][0]["delta"]
            full += delta.get("content") or ""
        except (json.JSONDecodeError, KeyError, IndexError):
            continue  # SSE comments / keep-alives
    return full.strip()


def list_openrouter_models(force=False):
    """Return [{'id','name','free','ctx'}] sorted by id; cached for 10 minutes."""
    if not force and _models_cache["models"] and time.time() - _models_cache["ts"] < 600:
        return _models_cache["models"]
    headers = {}
    key = get_key("openrouter")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    r = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=20)
    r.raise_for_status()
    models = []
    for m in r.json().get("data", []):
        pricing = m.get("pricing") or {}
        free = str(pricing.get("prompt")) in ("0", "0.0") and str(pricing.get("completion")) in ("0", "0.0")
        models.append({
            "id": m["id"],
            "name": m.get("name") or m["id"],
            "free": free,
            "ctx": m.get("context_length") or 0,
        })
    models.sort(key=lambda m: m["id"])
    _models_cache.update(ts=time.time(), models=models)
    logging.info(f"Fetched {len(models)} OpenRouter models")
    return models
