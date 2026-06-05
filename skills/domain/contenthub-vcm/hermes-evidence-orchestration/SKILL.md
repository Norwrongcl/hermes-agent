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
2. Compare required evidence against received evidence.
3. Request only the missing item, with a short message.
4. Validate file type, accessibility, source, and relationship.
5. Return status: `recibida`, `valida`, `invalida`, or `requiere_reenvio`.
6. Create an audit event for each request, receipt, rejection, or validation.

## Guardrails

- Do not mark evidence as valid only because it exists.
- Do not expose private Drive URLs outside authorized roles.
- If storage destination is undecided, preserve metadata and defer persistence to `hermes-convex-sync`.
