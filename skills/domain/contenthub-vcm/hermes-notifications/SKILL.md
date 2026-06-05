---
name: hermes-notifications
description: Send or draft Hermes notifications for docentes, coordinators, directors, and CM users. Use when a workflow needs WhatsApp, Telegram, app, or email follow-up about missing fields, evidence, approvals, rejected content, risks, or publication status.
---

# Hermes Notifications

## Overview

Create short, role-aware messages that move VcM work forward while preserving approval gates and privacy.

## Notification Types

- Missing activity field.
- Evidence request or resend.
- Pending validation for coordinator.
- Content proposal ready for CM review.
- Publication scheduled, published, or failed.
- Risk alert for evidence, event, agreement, or indicator.

## Message Rules

- Ask for one action at a time.
- Use formal, close Spanish.
- Include the activity/event name when safe.
- Avoid internal IDs unless speaking to staff.
- Never send sensitive data to an unverified external channel.

## Output

Return channel, recipient role, message body, approval requirement, send window, and audit reason. If delivery tools are not configured, return a draft instead of pretending it was sent.
