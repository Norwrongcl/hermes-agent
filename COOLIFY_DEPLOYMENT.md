# Hermes Agent on Coolify

This repo already contains an official production Dockerfile and published
image. For Coolify, prefer `docker-compose.coolify.yml`: it uses
`nousresearch/hermes-agent:latest`, keeps the official `/init` entrypoint, and
mounts persistent storage at `/opt/data`.

This deployment repairs the existing Coolify application:

- Application UUID: `howwk4ocgcggg4gg0g448sco`
- Repository: `Norwrongcl/hermes-agent`
- Branch: `main`
- Compose file: `/docker-compose.coolify.yml`
- Project: `Taller Ing SW`

## Persistent Data

The `/opt/data` volume must persist across restarts and redeploys. It contains:

- `.env` and `auth.json`
- `config.yaml`
- `SOUL.md`
- `.hermes.md`
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
- App/exposed port in Coolify: `8642` (not `3000`)
- Dashboard port: disabled in v1
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

## VcM Identity And Context

The Coolify compose bind-mounts versioned context files under `/seed`, then
copies them into the persistent volume before the Hermes gateway starts:

```yaml
hermes:
  command: ["sh", "-lc", "cp /seed/SOUL.md /opt/data/SOUL.md && cp /seed/.hermes.md /opt/data/.hermes.md && exec hermes gateway run"]
  volumes:
    - hermes-data:/opt/data
    - ./deploy/hermes/SOUL.md:/seed/SOUL.md:ro
    - ./deploy/hermes/.hermes.md:/seed/.hermes.md:ro
```

`SOUL.md` makes Hermes act as the Digital Operations Director for the VcM
platform. `.hermes.md` gives Hermes the project operating context: this is a
VcM operations platform with specialized agents, not a chatbot, Wiki-RAG, or
document search system.

Do not bind-mount `SOUL.md` directly over `/opt/data/SOUL.md`. The official
Hermes Docker startup script seeds and chowns files under `/opt/data`; direct
file bind mounts can make that hook treat the path incorrectly or fail on a
read-only file.

Do not store secrets in these files.

## Repair Existing Coolify App

If Coolify detected the app as port `3000`, change it manually in the panel:

- App/exposed port: `8642`
- Remove any `3000` port setting
- Healthcheck path: `/health`
- Healthcheck port: `8642`
- Healthcheck scheme: `http`
- Expected status: `200`

Keep FQDN empty for the initial private API deployment unless you are ready to
put authentication and network policy in front of the endpoint.

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
