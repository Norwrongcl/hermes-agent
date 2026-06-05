---
name: hermes-audit-memory
description: Maintain Hermes conversational memory, audit events, tool-call records, and error traces for ContentHub. Use when a workflow needs traceability, session isolation, retries, incident notes, or accreditation-grade action history.
---

# Hermes Audit Memory

## Overview

Keep Hermes useful without making memory a second source of truth. Memory explains context; Convex stores institutional facts.

## What To Store

- Session ID, channel, external user ID, actor role, and linked user when authorized.
- Message summaries and raw message references.
- Tool call name, input summary, output summary, latency, and status.
- State transitions and approval gates.
- Errors, retries, unresolved missing fields, and handoff notes.

## Rules

- Isolate sessions by channel and user.
- Do not share memory across docentes.
- Do not store secrets, API keys, or access tokens.
- Do not treat remembered facts as current; verify in Convex before operational answers.
- Record "why" for every privileged action or denied action.

## Error Handling

On failure, preserve enough context for replay: operation, target entity, non-secret params, user-facing message, provider error code, and next retry recommendation.
