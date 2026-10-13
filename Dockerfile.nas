FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv python3-pip git curl ca-certificates \
    && mkdir -p -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @anthropic-ai/claude-code && npm cache clean --force

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY nas/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app
COPY nas_bot.py agent_core.py claude_bridge.py llm_providers.py github_sync.py /app/
COPY nas/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# TrueNAS runs apps as uid/gid 568 ("apps"). Claude Code refuses bypassPermissions as root, so never run as root.
# The base image's "node" user already owns uid 1000, so make a dedicated one.
RUN groupadd -g 568 apps && useradd -u 568 -g 568 -m -d /data/home -s /bin/sh apps \
    && mkdir -p /data /projects && chown -R 568:568 /data /projects
USER 568:568

ENV HOME=/data/home \
    DATA_DIR=/data \
    PROJECTS_ROOT=/projects \
    GITHUB_SYNC=1 \
    PYTHONUNBUFFERED=1
VOLUME ["/data", "/projects"]
ENTRYPOINT ["/app/entrypoint.sh"]
