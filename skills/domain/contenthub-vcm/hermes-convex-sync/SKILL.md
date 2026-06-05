---
name: hermes-convex-sync
description: Read from and write to ContentHub Convex through approved Hermes endpoints and mutations. Use when Hermes needs live VcM data, pending reports, missing evidence, search, audit logs, or future human-approved persistence.
---

# Hermes Convex Sync

## Overview

Use Convex as the source of truth. Current documented endpoints are read-only; any write operation must use explicit future mutations with coordinator approval and audit.

## Current Read Endpoints

Base site URL: `https://careful-monitor-525.convex.site`

- `GET /hermes/overview`
- `GET /hermes/pending-reports`
- `GET /hermes/missing-evidence`
- `GET /hermes/recent-audit`
- `POST /hermes/search`

Every request requires `Authorization: Bearer <CONTENTHUB_CONVEX_API_KEY>`.

## Read Rules

- Prefer live Convex data over memory when answering operational questions.
- Include record names, status, and timestamps when available.
- If an endpoint fails, say the system cannot verify live data and log the error.
- Never put API keys in prompts, messages, screenshots, or audit summaries.

## Future Write Gate

Before writes exist, return a draft payload and require human confirmation. A valid write must include actor, session, source channel, target table, status transition, and audit reason.
