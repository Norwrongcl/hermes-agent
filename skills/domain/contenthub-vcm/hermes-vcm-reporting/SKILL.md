---
name: hermes-vcm-reporting
description: Generate VcM operational summaries, accreditation evidence summaries, indicator explanations, and risk reports from Convex data. Use when Hermes is asked for current status, weekly briefs, missing evidence, pending validations, or management reporting.
---

# Hermes VcM Reporting

## Overview

Answer management questions from live data, not memory. Reports must help coordinators prioritize validation, evidence closure, publications, and accreditation traceability.

## Report Types

- Daily or weekly operational brief.
- Pending activity validation.
- Missing evidence by line, event, or responsible user.
- Publication pipeline and CM workload.
- Indicator snapshot with trend and caveats.
- Accreditation-ready evidence summary.

## Workflow

1. Use `hermes-convex-sync` for live data.
2. Select the smallest useful live reads: overview for executive state, list filters for entity-specific questions.
3. Separate facts from recommendations.
4. Surface highest-risk items first.
5. Include missing data and confidence caveats.
6. Recommend next action and responsible role.
7. Log report generation inputs and output summary when the available tool supports it.

## Query Playbook

- Current operational snapshot: `contenthub_vcm_query(operation="overview")`.
- Active agreements: `contenthub_vcm_list(entity="agreements", filters={"status":"activo"})`.
- Agreements to verify: `contenthub_vcm_list(entity="agreements", filters={"status":"por_verificar"})`.
- Missing evidence: `contenthub_vcm_list(entity="evidenceFiles", filters={"status":"solicitada"})`.
- Pending reports: `contenthub_vcm_list(entity="activityReports", filters={"status":"pendiente_validacion"})`.
- Pending CM proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"pendiente"})`.
- Scheduled CM proposals: `contenthub_vcm_list(entity="contentProposals", filters={"status":"programada"})`.
- Risk activities: `contenthub_vcm_list(entity="activities", filters={"status":"en_riesgo"})` or `filters={"riskLevel":"alto"}` depending on the user wording.

## Output Shape

Keep answers concise for chat. For formal exports, return structured sections: resumen, riesgos, evidencias faltantes, acciones, indicadores, fuentes.

If a filtered query returns zero records, include the exact filter used and, when useful, one nearby context list such as all agreements or all proposals by status. This prevents false negatives from wording like "vigente" vs `activo`.
