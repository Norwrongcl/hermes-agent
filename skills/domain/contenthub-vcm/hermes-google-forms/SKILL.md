---
name: hermes-google-forms
description: Use when Hermes must inspect or submit a Google Form for ContentHub VcM without browser automation, especially legacy institutional forms such as Presencias en la Sociedad.
---

# Hermes Google Forms

## Purpose

Submit simple public Google Forms from structured VcM data without using a
browser. This is for backend-safe form submission in Coolify, where a headless
browser may not be installed or reliable.

## Tool

Use `contenthub_google_form`.

Supported operations:

- `inspect`: read the public form page, discover `entry.<id>` fields, title,
  submit URL, prefilled values, and best-effort labels.
- `submit`: send a response to the Google Forms `formResponse` endpoint.

## Workflow

1. Confirm the target form URL.
2. Call `contenthub_google_form(operation="inspect", formUrl="...")`.
3. Map extracted ContentHub fields to `entry.<id>` values.
4. If the mapping is uncertain, ask the user for the missing mapping instead of
   guessing.
5. Prefer a dry run first:
   `contenthub_google_form(operation="submit", formUrl="...", responses={...}, dryRun=true)`.
6. Submit only after the values are complete and the user or coordinator has
   approved the action.
7. Register or update the related record in Convex with `contenthub_vcm_query`
   when the form submission represents a VcM report, evidence step, or audit
   event.

## Guardrails

- Do not use browser tools for Google Forms unless a human explicitly requests
  visual/browser interaction and the browser toolset is configured.
- Do not submit forms that require Google login, CAPTCHA, file upload, or
  interactive validation. Ask the user to handle those manually or provide a
  backend/API alternative.
- Do not invent `entry.<id>` mappings. If labels are not discovered reliably,
  ask for a prefilled link or a field map.
- Do not submit duplicate institutional reports unless the user confirms that a
  duplicate submission is intended.
- Never expose OAuth secrets, client secrets, refresh tokens, or form internals
  to WhatsApp users.

## Good Inputs

Public form URL:

```text
https://docs.google.com/forms/d/e/<form-id>/viewform
```

Prefilled link:

```text
https://docs.google.com/forms/d/e/<form-id>/viewform?usp=pp_url&entry.123=...
```

Explicit field map:

```json
{
  "entry.123456": "Escuela de Ingenieria Civil Informatica",
  "entry.789012": "2026-06-13",
  "entry.345678": "Charla de innovacion con empresa asociada"
}
```

## Failure Handling

- If `inspect` finds no entries, explain that the form may require login or use
  unsupported dynamic rendering.
- If `submit` returns a non-200/302 status, report that the form rejected the
  submission and preserve the payload for review.
- If the form asks for file upload, use the Drive evidence workflow first and
  submit the Drive link only if the form accepts links.
