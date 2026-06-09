---
name: hermes-content-proposals
description: Create institutional social content proposals for ContentHub. Use when Hermes must draft Instagram, LinkedIn, web, email, carousel, reel, or campaign copy from approved activity, event, evidence, or coordinator context.
---

# Hermes Content Proposals

## Overview

Generate communication drafts that a CM or coordinator can approve, edit, reject, schedule, or turn into visual/video production.

Hermes must treat content proposals as operational records, not casual copy. Every proposal needs source facts, evidence awareness, channel fit, and an approval path.

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

## Workflow

1. Identify the source: activity, report, evidence, agreement, initiative, or user-provided context.
2. Read the source record from Convex when an ID, name, status, or operational claim is involved.
3. Check evidence readiness. If evidence is missing or only requested, draft only a pending proposal and state the missing evidence.
4. Draft for the requested channel. If no channel is specified, prefer Instagram and LinkedIn variants.
5. Include only verified facts in the copy. Put uncertain details in `missingFields` or a concise follow-up question, not in the post.
6. Prepare `visualBrief` for generated assets. If image generation is requested and configured, route to `hermes-azure-media-generation`; generated assets remain proposals.
7. If the user asks to persist, create `contentProposals` through `hermes-convex-sync` with existing fields only and `status: "pendiente"`.
8. End with the approval gate: who should approve, what is ready, and what is still missing.

## Tool Use

- For pending proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"pendiente"})`.
- For approved proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"aprobada"})`.
- For activity-linked drafts: read `activities` by ID or list/search by title first, then inspect `evidenceFiles` by `activityId`.
- For persistence: `contenthub_vcm_query(operation="create", entity="contentProposals", data={...}, reason="...")`.

## Rules

- Do not publish directly.
- Do not schedule before approval.
- Do not invent attendance, partners, outcomes, or quotes.
- Keep Spanish formal, clear, and institutional.
- For generated images or video, route to `hermes-azure-media-generation` or `hermes-remotion-video-rendering`.
- If the user asks for LinkedIn, optimize for institutional impact and partner value; if Instagram, optimize for concise visual storytelling.
