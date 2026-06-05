---
name: hermes-azure-media-generation
description: Use Azure AI APIs for Hermes media and content production research or implementation. Use when ContentHub needs image generation, video generation with Sora, text-to-speech, avatar video, transcription, translation, content safety, or video indexing in CM workflows.
---

# Hermes Azure Media Generation

## Overview

Use Azure as a governed API layer for content creation and moderation. Prefer it when the project needs enterprise controls, Azure billing, regional deployment, or Microsoft Foundry model management.

## Candidate Azure APIs

- Azure OpenAI image generation: `gpt-image-1`, `gpt-image-1-mini`, `gpt-image-1.5`, and `gpt-image-2` where available.
- Azure OpenAI video generation: Sora and Sora 2 preview for text-to-video, image-to-video, and remix jobs.
- Azure Speech: text-to-speech audio, neural voices, and text-to-speech avatar video.
- Azure AI Video Indexer: upload/index media and extract insights from video/audio.
- Azure AI Content Safety: moderate generated and user-provided text/image/multimodal content.
- Azure AI Translator: translate or localize publication drafts when needed.

## Recommended Uses In ContentHub

- Generate visual concepts for posts after CM approval.
- Generate short Sora clips only for generic institutional scenes, not real people or copyrighted IP.
- Generate voiceover or avatar explainers for event recaps and training content.
- Moderate copy and visuals before they enter approval.
- Index raw event video to produce summaries, chapters, transcripts, and clip ideas.

## Guardrails

- Treat Sora as preview and quota-limited.
- Avoid real-person face generation unless Azure terms, consent, and account access explicitly allow it.
- Run Content Safety checks before storing or proposing generated assets.
- Store prompts, model deployment, asset URL, reviewer, and approval state in Convex.

## Source Links

- https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/dall-e
- https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/video-generation
- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech
- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/text-to-speech-avatar/what-is-text-to-speech-avatar
- https://learn.microsoft.com/en-us/azure/azure-video-indexer/
- https://learn.microsoft.com/en-us/azure/ai-services/content-safety/
