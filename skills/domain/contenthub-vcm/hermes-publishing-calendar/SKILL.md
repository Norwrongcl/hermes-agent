---
name: hermes-publishing-calendar
description: Manage publication scheduling decisions for Hermes and ContentHub. Use when approved content must be queued, scheduled, checked, retried after Buffer or platform errors, or reconciled with the editorial calendar.
---

# Hermes Publishing Calendar

## Overview

Coordinate approved content publication without bypassing CM review. In the current ContentHub implementation, operate through existing `contentProposals` fields only unless a provider-specific publishing tool is explicitly available.

## States

- `pendiente_revision`
- `aprobado`
- `rechazado`
- `programado`
- `publicado`
- `error_publicacion`
- `archivado`

## Workflow

1. Read the target `contentProposals` record from Convex.
2. Confirm the proposal is `aprobada`. If it is `pendiente`, `rechazada`, or missing, do not schedule; ask for approval or correction.
3. Validate channel, copy, hashtags, visual brief or asset readiness, and requested publication date.
4. Check existing `contentProposals` with `status: "programada"` near the requested date when possible.
5. If only internal scheduling is available, update existing fields such as `status: "programada"` and `scheduledAt` with an audit-ready reason.
6. If an external provider tool is configured, queue publication only after internal approval and keep provider failures visible in the response.
7. If publishing fails, keep the proposal in an auditable state and create or request an audit event.

## Tool Use

- Read approved proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"aprobada"})`.
- Read scheduled proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"programada"})`.
- Schedule one approved proposal: `contenthub_vcm_query(operation="update", entity="contentProposals", id="...", patch={"status":"programada","scheduledAt":"..."}, reason="...")`.
- Never patch unknown tables such as `publications` or `publishingQueue` unless the schema tool confirms they exist.

## Guardrails

- Never schedule rejected or unreviewed content.
- Treat "publicar ahora" as privileged and require coordinator/CM confirmation.
- Preserve rollback notes and provider error messages for audit.
- Do not claim external publication succeeded unless a provider tool returned success.
- If no provider is available, say "queda programado internamente en ContentHub" instead of implying publication on Instagram or LinkedIn.
