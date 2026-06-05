---
name: hermes-audio-transcription
description: Transcribe and normalize audio sent to Hermes by docentes or coordinators. Use for WhatsApp or Telegram voice notes before extracting activities, events, evidence requests, notes, or content briefs.
---

# Hermes Audio Transcription

## Overview

Convert voice notes into reliable Spanish text with metadata Hermes can audit. This skill prepares audio for extraction; it must not write final records by itself.

## Workflow

1. Verify sender identity and session from the router.
2. Store or reference the raw audio without exposing secrets in logs.
3. Transcribe with the configured speech provider.
4. Normalize punctuation, dates, names, institutions, and Chilean Spanish terms only when confidence is high.
5. Return transcript, confidence, detected language, duration, and quality notes.
6. Send the transcript to `hermes-activity-extraction`, `hermes-content-proposals`, or `hermes-vcm-reporting` depending on intent.

## Output

```json
{
  "transcript": "Texto transcrito...",
  "language": "es-CL",
  "confidence": 0.0,
  "durationSeconds": 0,
  "qualityFlags": ["background_noise", "partial_audio"],
  "requiresConfirmation": true
}
```

## Guardrails

- Do not invent missing names, dates, institutions, or numbers.
- If confidence is low, ask the user to repeat the unclear fragment.
- Preserve the raw transcript separately from normalized fields.
- Keep audio provider, model, latency, and errors in agent audit logs.
