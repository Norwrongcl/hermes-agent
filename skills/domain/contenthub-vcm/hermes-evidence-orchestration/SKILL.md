---
name: hermes-evidence-orchestration
description: Manage evidence requests and intake for Hermes VcM workflows. Use when an activity, event, publication, or accreditation record needs photos, attendance lists, documents, links, audio, video, authorization, validation state, or resend follow-up.
---

# Hermes Evidence Orchestration

## Overview

Coordinate evidence capture without losing provenance. Evidence can be received from WhatsApp, Telegram, Drive links, email, or dashboard uploads.

## Evidence Types

- imagen
- documento
- audio
- video
- enlace
- lista_asistencia
- autorizacion
- encuesta
- otro

## Workflow

1. Identify the linked activity, event, report, or publication.
2. Read the linked `activities`, `activityReports`, `evidenceFiles`, or `contentProposals` records when available.
3. Compare required evidence against received evidence.
4. Request only the missing item, with a short message.
5. Validate file type, accessibility, source, and relationship.
6. Return status: `recibida`, `valida`, `invalida`, or `requiere_reenvio`.
7. Create or update a single evidence record through `hermes-convex-sync` only when the user provides enough data and the action is authorized.
8. Create an audit event for each request, receipt, rejection, or validation when the endpoint/tool supports it.

## Tool Use

- Missing evidence: `contenthub_vcm_list(entity="evidenceFiles", filters={"status":"solicitada"})`.
- Evidence for one activity: `contenthub_vcm_list(entity="evidenceFiles", filters={"activityId":"..."})`.
- Pending reports that may need evidence: `contenthub_vcm_list(entity="activityReports", filters={"status":"pendiente_validacion"})`.
- Do not use free-text search for status-based evidence questions.

## Guardrails

- Do not mark evidence as valid only because it exists.
- Do not expose private Drive URLs outside authorized roles.
- If storage destination is undecided, preserve metadata and defer persistence to `hermes-convex-sync`.
- For CM proposals, missing evidence blocks scheduling and external publication. It does not block drafting a clearly marked pending proposal.
