---
name: hermes-content-proposals
description: Create institutional social content proposals for ContentHub. Use when Hermes must draft Instagram, LinkedIn, web, email, carousel, reel, or campaign copy from approved activity, event, evidence, or coordinator context.
---

# Hermes Content Proposals

## Overview

Generate communication drafts that a CM or coordinator can approve, edit, reject, schedule, or turn into visual/video production.

## Inputs

- Source activity/event/report IDs when available.
- Approved or pending facts from Convex.
- Channel, format, audience, publication objective, and deadline.
- Brand constraints from institutional tone.
- Evidence assets or visual notes.

## Output

```json
{
  "channel": "instagram|linkedin|web|email",
  "format": "post|reel|story|carrusel|comunicado|video",
  "copy": "Texto principal",
  "hashtags": [],
  "visualBrief": "Indicaciones de imagen o video",
  "sourceFacts": [],
  "state": "pendiente_revision",
  "approvalNeededBy": "cm|coordinadora"
}
```

## Rules

- Do not publish directly.
- Do not invent attendance, partners, outcomes, or quotes.
- Keep Spanish formal, clear, and institutional.
- For generated images or video, route to `hermes-azure-media-generation` or `hermes-remotion-video-rendering`.
