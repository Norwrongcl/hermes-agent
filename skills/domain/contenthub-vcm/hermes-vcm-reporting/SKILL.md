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
2. Separate facts from recommendations.
3. Surface highest-risk items first.
4. Include missing data and confidence caveats.
5. Recommend next action and responsible role.
6. Log report generation inputs and output summary.

## Output Shape

Keep answers concise for chat. For formal exports, return structured sections: resumen, riesgos, evidencias faltantes, acciones, indicadores, fuentes.
