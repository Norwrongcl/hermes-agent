---
name: hermes-convex-sync
description: Read and write live ContentHub Convex data through protected Hermes endpoints. Use when Hermes needs VcM CRUD, table schema context, pending reports, missing evidence, search, audit logs, or coordinator-approved persistence.
---

# Hermes Convex Sync

## Overview

Use Convex as the source of truth. Hermes can perform document-level CRUD through protected HTTP endpoints. Do not invent records from memory when a live read is possible.

## Preferred Tools

- Use `contenthub_vcm_list` for list questions such as "convenios activos", "listar todos los convenios", "evidencias solicitadas", "reportes pendientes".
- Use `contenthub_vcm_query` for overview, schema, get/create/update/delete, or compatibility with older operation-based calls.
- `contenthub_vcm_list` accepts flexible filters: exact values, arrays, `$contains`, `$in`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, plus `sortBy`, `sortDirection`, `fields`, and `limit`.

## Current Read Endpoints

Base site URL: `https://careful-monitor-525.convex.site`

- `GET /hermes/overview`
- `GET /hermes/pending-reports`
- `GET /hermes/missing-evidence`
- `GET /hermes/recent-audit`
- `POST /hermes/search`
- `GET /hermes/schema`
- `POST /hermes/crud/list`
- `POST /hermes/crud/get`

Every request requires `Authorization: Bearer <CONTENTHUB_CONVEX_API_KEY>`.

## CRUD Endpoints

- `POST /hermes/crud/create`
- `POST /hermes/crud/update`
- `POST /hermes/crud/delete`

All write requests must include `reason`. Include `actorUserId` or `agentSessionId` when available.

Examples:

```json
{
  "table": "agreements",
  "filters": { "status": "activo" },
  "limit": 50
}
```

```json
{
  "table": "agreements",
  "id": "record_id",
  "patch": { "status": "cerrado" },
  "reason": "Coordinadora solicito cerrar convenio desde Telegram"
}
```

```json
{
  "table": "evidenceFiles",
  "id": "record_id",
  "mode": "soft",
  "reason": "Evidencia duplicada marcada por coordinadora"
}
```

## Read Rules

- Prefer live Convex data over memory when answering operational questions.
- Prefer `contenthub_vcm_list` over `contenthub_vcm_query(operation="overview")` when the user asks for records by status or wants all records.
- For status, type, role, channel, line, and date filters, use `/hermes/crud/list` with exact `filters`; do not use text search.
- Include record names, status, and timestamps when available.
- Use `/hermes/schema` when unsure about table names, searchable fields, or soft-delete behavior.
- If an endpoint fails, say the system cannot verify live data and log the error.
- Never put API keys in prompts, messages, screenshots, or audit summaries.

## Table Names

- `users`: name, email, username, role, status, initials, createdAt, updatedAt.
- `channelContacts`: userId, displayName, channel, externalId, status, lastInteractionAt, createdAt, updatedAt.
- `agreements`: name, partner, country, region, type, status, ownerUserId, startDate, endDate, strategicLine, summary, createdAt, updatedAt.
- `activities`: title, description, strategicLine, status, ownerUserId, agreementId, source, audience, participantEstimate, missingEvidenceCount, riskLevel, startDate, endDate, monthLabel, color, createdAt, updatedAt.
- `activityTasks`: activityId, phase, text, done, responsible, order, updatedAt.
- `activityReports`: activityId, submittedByUserId, contactId, source, transcript, extractedSummary, status, missingFields, confidence, submittedAt, reviewedAt, reviewedByUserId, createdAt, updatedAt.
- `evidenceFiles`: activityId, reportId, uploadedByUserId, name, type, url, status, requestedReason, uploadedAt, createdAt, updatedAt.
- `budgetItems`: activityId, name, amount, status, category, createdAt.
- `contentProposals`: authorUserId, authorName, authorInitials, channel, format, activityId, status, copy, hashtags, visualBrief, rejectionReason, scheduledAt, createdAt, updatedAt.
- `initiatives`: title, objective, strategicLine, status, progress, owner, nextMilestone, dueDate, createdAt, updatedAt.
- `indicators`: group, name, value, unit, target, trend, period, updatedAt.
- `dashboardItems`: kind, title, value, subtitle, column, status, order, createdAt.
- `routePages`: slug, title, description, status, updatedAt.
- `notifications`: userId, contactId, channel, title, body, status, relatedActivityId, createdAt, sentAt.
- `auditEvents`: actorUserId, agentSessionId, entityType, entityId, action, summary, createdAt.
- `agentSessions`: agentName, purpose, status, relatedActivityId, createdByUserId, createdAt, updatedAt.
- `agentMessages`: sessionId, role, content, createdAt.
- `agentToolCalls`: sessionId, toolName, inputSummary, outputSummary, status, createdAt.

`authCredentials` is protected. Do not read or write it through Hermes.

## Common Enum Values

- `agreements.status`: `activo`, `pendiente`, `por_verificar`, `cerrado`
- `activities.status`: `planificado`, `en_preparacion`, `en_ejecucion`, `por_aprobar`, `cerrado`, `en_riesgo`
- `activityReports.status`: `borrador`, `pendiente_validacion`, `aprobado`, `rechazado`, `registrado`
- `evidenceFiles.status`: `solicitada`, `recibida`, `validada`, `rechazada`
- `contentProposals.status`: `pendiente`, `aprobada`, `rechazada`, `programada`
- `initiatives.status`: `activa`, `preparacion`, `cerrada`, `en_riesgo`
- `users.status`: `activo`, `inactivo`
- `channelContacts.status`: `activo`, `inactivo`, `bloqueado`
- `notifications.status`: `pendiente`, `enviada`, `fallida`, `leida`
- `agentSessions.status`: `activa`, `cerrada`, `fallida`

## Write Rules

- Never perform schema changes, table drops, truncates, bulk deletes, cascade deletes, or destructive multi-record operations.
- Create/update/delete only one document per tool call.
- Prefer soft delete when the table has a status field. `/hermes/crud/delete` with `mode: "soft"` maps records to a closed, inactive, rejected, or read state.
- Hard delete is single-record only and requires `confirm: "PERMANENT_DELETE_ONE"`.
- Do not patch `_id` or `_creationTime`.
- After every write, summarize the table, id, changed fields, and audit reason.
- For ambiguous user requests, first list matching records and ask which specific record to mutate.

## Query Examples

- "Convenios activos" -> `contenthub_vcm_list` with `entity: "agreements"`, `filters: { "status": "activo" }`.
- "Convenios por verificar" -> `/hermes/crud/list` with `table: "agreements"`, `filters: { "status": "por_verificar" }`.
- "Evidencias faltantes" -> `/hermes/crud/list` with `table: "evidenceFiles"`, `filters: { "status": "solicitada" }`.
- "Reportes pendientes" -> `/hermes/crud/list` with `table: "activityReports"`, `filters: { "status": "pendiente_validacion" }`.
- "Propuestas de CM pendientes" -> `/hermes/crud/list` with `table: "contentProposals"`, `filters: { "status": "pendiente" }`.
- "Buscar por palabra libre" -> `/hermes/crud/list` with `search` only when the user is searching text such as name, partner, summary, title, copy, transcript, or body.
- "Convenios en Valparaiso no cerrados" -> `contenthub_vcm_list` with `entity: "agreements"`, `filters: { "region": { "$contains": "Valparaiso" }, "status": { "$ne": "cerrado" } }`.
- "Actividades de alto riesgo desde 2026" -> `contenthub_vcm_list` with `entity: "activities"`, `filters: { "riskLevel": "alto", "startDate": { "$gte": "2026-01-01" } }`, `sortBy: "startDate"`.
- "Solo nombres y estados" -> add `fields: ["name", "status"]` or the equivalent entity fields.
