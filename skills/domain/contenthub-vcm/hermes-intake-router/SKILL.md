---
name: hermes-intake-router
description: Route incoming WhatsApp, Telegram, email, or web messages for Hermes in ContentHub. Use when Hermes receives a new user interaction and must classify intent, channel, identity, session state, next required skill, and whether a human approval gate is needed.
---

# Hermes Intake Router

## Purpose

Classify each inbound message before Hermes performs work. Keep routing explicit so WhatsApp docente flows, Telegram coordinadora flows, read-only dashboard questions, and content requests do not mix state.

## Routing Contract

Return a structured decision:

```json
{
  "channel": "whatsapp|telegram|email|web",
  "actorRole": "docente|coordinadora|director|cm|desconocido",
  "intent": "reportar_actividad|subir_evidencia|consultar_estado|crear_contenido|programar_publicacion|generar_reporte|otro",
  "sessionState": "new|active|waiting_for_field|waiting_for_approval|completed|failed",
  "nextSkill": "skill-folder-name",
  "requiresHumanApproval": true,
  "reason": "short audit-ready explanation"
}
```

## Rules

- Validate channel identity before routing any privileged action.
- Treat unregistered WhatsApp numbers as `desconocido`; do not create records.
- Route audio first to `hermes-audio-transcription`.
- Route activity descriptions to `hermes-activity-extraction`.
- Route missing files, links, photos, attendance lists, or authorizations to `hermes-evidence-orchestration`.
- Route requests about live status, pending validation, missing evidence, indicators, or audit to `hermes-convex-sync` or `hermes-vcm-reporting`.
- Route copy, hashtags, carousel, reel, or post drafts to `hermes-content-proposals`.
- Route scheduling or publication status to `hermes-publishing-calendar`.
- Never publish, persist critical data, or notify external parties without the target skill approval gate.
