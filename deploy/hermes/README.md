# Hermes VcM Deployment Context

This directory contains the versioned identity and project context used by the Coolify deployment.

- `SOUL.md` is mounted into `/opt/data/SOUL.md` and defines Hermes as the Digital Operations Director for the VcM platform.
- `.hermes.md` is mounted into `/opt/data/.hermes.md` and defines the project-specific operating context. The official Docker wrapper starts Hermes from `/opt/data`, so this file is discovered at session startup.

The container data volume at `/opt/data` remains the persistent source of truth for runtime state: config, auth, sessions, memories, skills, profiles, cron, workspace, and logs.

Do not put secrets in these files. Configure secrets through Coolify environment variables or through `hermes setup` inside the running container.
