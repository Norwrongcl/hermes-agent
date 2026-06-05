---
name: hermes-activity-extraction
description: Extract structured VcM activity reports from docente messages or transcripts. Use when Hermes must turn conversational text into activity fields, missing fields, confidence scores, and a validation summary before saving to Convex.
---

# Hermes Activity Extraction

## Overview

Turn natural language reports into an auditable `activityReport` draft. This skill prepares data and asks for missing details; it does not approve the activity.

## Required Fields

- Academic unit.
- Teacher identity and RUT when available.
- VcM line: internacionalizacion, formacion continua, docencia vinculada, investigacion aplicada, innovacion_emprendimiento, asistencia_tecnica.
- Activity type and title.
- Date or date range.
- Place, modality, and external organization.
- Description, participants, beneficiaries, and evidence available.

## Output Contract

```json
{
  "status": "borrador|pendiente_validacion",
  "fields": {},
  "missingFields": [],
  "confidence": 0.0,
  "reviewSummary": "Resumen breve para coordinacion",
  "questionsForUser": ["Una pregunta puntual"],
  "evidenceHints": ["foto", "lista_asistencia"]
}
```

## Rules

- Ask one missing-field question at a time.
- Confirm the summary with the docente before any write.
- Mark low-confidence fields for human review.
- Keep original transcript and extracted JSON linked for accreditation traceability.
