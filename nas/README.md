# AI Assistant on TrueNAS (headless project agent)

A container that runs the Telegram project agent on your NAS:

```
Telegram  ->  /project <name>  ->  send plan.md  ->  Critique / Design / Implement (Claude Code)  ->  private GitHub repo per project
```

It has no PC-control skills (screenshots, mouse, WhatsApp). Those need a desktop and stay in the Windows bot.

## What you need

| Item | How to get it |
|---|---|
| Telegram bot token | `@BotFather` -> `/newbot` (a separate bot from your Windows one, since two programs can't poll the same bot) |
| Your Telegram user id | message `@userinfobot` |
| Claude subscription token | on any machine with Claude Code installed: `claude setup-token`, copy the token |
| GitHub token | github.com -> Settings -> Developer settings -> Personal access tokens. Classic token with the **repo** scope (or a fine-grained token with Administration + Contents read/write on all repos, which is needed to create repos) |
| Optional chat model key | NVIDIA, Groq or OpenRouter. Only used for plain chat and `/model`; Claude Code doesn't need it |

## Install

1. **Datasets.** In TrueNAS create `apps/ai-assistant/data` and `apps/ai-assistant/projects` and give the user/group `apps` (568) modify access to both (Datasets -> Permissions -> ACL, or set owner `apps`).
2. **Image.** The `Build NAS image` GitHub Action publishes `ghcr.io/starmarine06/aiassistant-nas:latest` on every push that touches the NAS files. The first time, open github.com -> your profile -> Packages -> `aiassistant-nas` -> Package settings and make it **public** (or add GHCR credentials in TrueNAS under Apps -> Settings).
3. **App.** Apps -> Discover Apps -> Custom App -> Install via YAML. Paste `nas/docker-compose.yml`, fill in the `<...>` values and your pool path, and deploy.
4. Message the bot `/start`.

To update: redeploy the app so it pulls the newest `latest` image.

## Using it

- `/project my-app`: creates `/projects/my-app` and switches to it. Each project folder becomes its own **private** GitHub repo (`<you>/my-app`), created on first sync.
- Send a `plan.md`: saved in the project folder (the old one is backed up as `plan.md.<time>.bak`) with **Critique / Design / Implement** buttons.
  - Critique -> `plan-review.md`, Design -> `plan-design.md` (both read-only, in Claude Code's plan mode)
  - Implement -> builds the project, tracks progress in `PROGRESS.md`
- After every successful task the project is committed and pushed. `/github` shows the repo and status; `/github off` pauses syncing.
- Any message you send goes to Claude Code in the current project (chat mode). `/claude off` switches to plain LLM chat; `/claude stop` cancels a running task.
- `/projects` lists projects. `/provider` and `/model` choose the chat LLM.

## Notes and safety

- **Permissions.** Nobody is at the NAS to approve prompts, so Claude Code runs with `bypassPermissions` by default. The container is the sandbox: it can only touch `/projects` and `/data`, but it does have internet access and your GitHub token. Set `CLAUDE_PERMISSION_MODE=acceptEdits` for a stricter setup (shell commands will then be blocked and reported with a one-tap "Re-run with full permissions" button).
- **Set `AUTHORIZED_CHAT_ID`.** Otherwise the first person to message the bot becomes its owner.
- **Secrets.** A default `.gitignore` is added to new repos (`.env`, `*.key`, `*.pem`, `node_modules/`, ...). Existing `.gitignore` files are left alone. Review what Claude Code writes before trusting it with real secrets.
- **Persistence.** `/data` holds the bot config, the Claude Code session history and git settings. `/projects` holds your code. Back both up.
- Repos that already exist on GitHub under the same name are reused (the folder is pointed at them). If the histories differ, the push is rejected and the bot tells you.
