---
name: hermes-publishing-calendar
description: Manage publication scheduling decisions for Hermes and ContentHub. Use when approved content must be queued, scheduled, checked, retried after Buffer or platform errors, or reconciled with the editorial calendar.
---

# Hermes Publishing Calendar

## Overview

Coordinate approved content publication without bypassing CM review. This skill should work from `contentProposals`, `publications`, and `publishingQueue`.

## States

- `pendiente_revision`
- `aprobado`
- `rechazado`
- `programado`
- `publicado`
- `error_publicacion`
- `archivado`

## Workflow

1. Confirm the proposal is approved.
2. Validate channel, asset readiness, copy, hashtags, and publication date.
3. Check for calendar collisions or campaign priority.
4. Queue publication through the approved provider when configured.
5. Record external job IDs and status changes.
6. If publishing fails, keep the item in queue and create an audit event.

## Guardrails

- Never schedule rejected or unreviewed content.
- Treat "publicar ahora" as privileged and require coordinator/CM confirmation.
- Preserve rollback notes and provider error messages for audit.
