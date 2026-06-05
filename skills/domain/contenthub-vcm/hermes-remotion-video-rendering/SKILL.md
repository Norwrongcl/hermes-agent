---
name: hermes-remotion-video-rendering
description: Render programmatic videos for ContentHub using Remotion and React. Use when Hermes has approved copy, images, charts, event metadata, subtitles, or voiceover and must assemble repeatable reels, recaps, explainers, lower thirds, or social clips.
---

# Hermes Remotion Video Rendering

## Overview

Use Remotion for deterministic video assembly, not generative imagination. It is best when ContentHub already has facts, brand templates, screenshots, photos, captions, audio, or generated assets.

## Best Fit

- Recap videos from event photos, dates, partner names, and metrics.
- Social reels with institutional title cards, subtitles, and music/voiceover.
- Indicator clips generated from Convex data.
- Personalized campaign variants from the same template.
- Preview inside the dashboard with `@remotion/player`, then server render.

## Workflow

1. Receive an approved content proposal and asset manifest.
2. Select a React composition template for post, reel, story, or recap.
3. Inject structured props: title, dates, images, captions, metrics, sponsor/partner names, CTA, and duration.
4. Preview in app if available.
5. Render MP4 locally, in a worker, or with Remotion Lambda when cloud rendering is configured.
6. Store render artifact, props, composition version, and approval status in Convex.

## When To Use Azure Instead

- Need text-to-video or image-to-video generation.
- Need avatar video from script.
- Need AI video indexing, moderation, or transcription.

## Source Links

- https://www.remotion.dev/docs/
- https://www.remotion.dev/docs/player
- https://www.remotion.dev/docs/lambda
