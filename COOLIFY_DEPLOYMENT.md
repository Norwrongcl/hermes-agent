# Hermes Agent on Coolify

This repo already contains an official production Dockerfile and published
image. For Coolify, prefer `docker-compose.coolify.yml`: it uses
`nousresearch/hermes-agent:latest`, keeps the official `/init` entrypoint, and
mounts persistent storage at `/opt/data`.

## Persistent Data

The `/opt/data` volume must persist across restarts and redeploys. It contains:

- `.env` and `auth.json`
- `config.yaml`
- `SOUL.md`
- `state.db`
- `sessions/`
- `memories/`
- `skills/`
- `profiles/`
- `cron/`
- `home/`
- `logs/`

Never run two Hermes gateway containers against the same volume at the same
time.

## Coolify Settings

- Build/deploy type: Docker Compose
- Compose file: `docker-compose.coolify.yml`
- Service: `hermes`
- Internal API port: `8642`
- Dashboard port: `9119`
- Persistent volume: `hermes-data:/opt/data`
- Start command: leave default from compose, `gateway run`
- Entrypoint: do not override
- Healthcheck: `curl -fsS http://127.0.0.1:8642/health`
- Minimum resources: 1 CPU, 1 GB RAM, 500 MB persistent disk
- Recommended resources: 2 CPU, 2-4 GB RAM, 2+ GB persistent disk
- Shared memory: `1gb` if browser/Playwright tools are used

## Required Environment Variables

At minimum:

```env
API_SERVER_ENABLED=true
API_SERVER_HOST=0.0.0.0
API_SERVER_PORT=8642
API_SERVER_KEY=<openssl-rand-hex-32>
```

The dashboard is disabled by default in the Coolify compose. To expose it, set
`HERMES_DASHBOARD=1` and either configure
`HERMES_DASHBOARD_OAUTH_CLIENT_ID` or put your own authentication in front and
set `HERMES_DASHBOARD_INSECURE=1`.

Then configure either Nous Portal interactively or at least one model provider
key, for example:

```env
OPENROUTER_API_KEY=<key>
```

For a Telegram bot:

```env
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALLOWED_USERS=<comma-separated-user-ids>
```

Do not set `GATEWAY_ALLOW_ALL_USERS=true` on an internet-facing VPS unless you
fully understand that Hermes can run tools and terminal commands.

## First Boot

After the first deployment, open a shell in the Coolify container and run one of:

```bash
hermes setup --portal
```

or:

```bash
hermes setup
```

The setup writes configuration into `/opt/data`, so it survives container
replacement, host reboot, and image upgrades.

## Upgrade

Redeploy in Coolify or pull the latest image. The image is stateless; data stays
on `hermes-data`.
