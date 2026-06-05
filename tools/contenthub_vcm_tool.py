"""ContentHub VcM read-only tool.

Connects Hermes to the ContentHub Convex HTTP API. This tool is intentionally
read-only until the VcM approval/audit workflows are wired end to end.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from tools.registry import registry


CONTENTHUB_VCM_SCHEMA = {
    "name": "contenthub_vcm_query",
    "description": (
        "Consulta datos operativos reales de ContentHub VcM desde Convex. "
        "Usar para revisar actividades en riesgo, reportes pendientes, "
        "evidencias faltantes, auditoria reciente y busquedas institucionales. "
        "No escribe datos."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "overview",
                    "pending_reports",
                    "missing_evidence",
                    "recent_audit",
                    "search",
                ],
                "description": "Consulta operativa a ejecutar.",
            },
            "entity": {
                "type": "string",
                "enum": [
                    "activities",
                    "agreements",
                    "contentProposals",
                    "initiatives",
                    "activityReports",
                    "agentMessages",
                ],
                "description": "Entidad para operation=search.",
            },
            "query": {
                "type": "string",
                "description": "Texto de busqueda para operation=search.",
            },
        },
        "required": ["operation"],
    },
}


_GET_PATHS = {
    "overview": "/hermes/overview",
    "pending_reports": "/hermes/pending-reports",
    "missing_evidence": "/hermes/missing-evidence",
    "recent_audit": "/hermes/recent-audit",
}


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def check_contenthub_vcm_requirements() -> bool:
    return bool(_env("CONTENTHUB_CONVEX_SITE_URL") and _env("CONTENTHUB_CONVEX_API_KEY"))


def _json_response(data: Any) -> str:
    return json.dumps(
        {
            "source": "contenthub_convex",
            "data": data,
        },
        ensure_ascii=False,
        default=str,
    )


def _tool_error(message: str, *, error_type: str = "contenthub_vcm_error") -> str:
    return json.dumps(
        {
            "error": message,
            "error_type": error_type,
            "source": "contenthub_convex",
        },
        ensure_ascii=False,
    )


def contenthub_vcm_query(operation: str, entity: str | None = None, query: str | None = None) -> str:
    base_url = _env("CONTENTHUB_CONVEX_SITE_URL").rstrip("/")
    api_key = _env("CONTENTHUB_CONVEX_API_KEY")

    if not base_url or not api_key:
        return _tool_error(
            "Missing CONTENTHUB_CONVEX_SITE_URL or CONTENTHUB_CONVEX_API_KEY.",
            error_type="configuration_missing",
        )

    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            if operation in _GET_PATHS:
                response = client.get(f"{base_url}{_GET_PATHS[operation]}", headers=headers)
            elif operation == "search":
                if not entity:
                    return _tool_error("operation=search requires entity.", error_type="invalid_arguments")
                if not query or len(query.strip()) < 2:
                    return _tool_error("operation=search requires a query with at least 2 characters.", error_type="invalid_arguments")
                response = client.post(
                    f"{base_url}/hermes/search",
                    headers={**headers, "content-type": "application/json"},
                    json={"entity": entity, "query": query.strip()},
                )
            else:
                return _tool_error(f"Unsupported operation: {operation}", error_type="invalid_operation")

            response.raise_for_status()
            return _json_response(response.json())
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:800] if exc.response is not None else ""
        return _tool_error(
            f"ContentHub returned HTTP {exc.response.status_code}: {body}",
            error_type="http_status_error",
        )
    except Exception as exc:
        return _tool_error(str(exc), error_type=type(exc).__name__)


def _handle_contenthub_vcm_query(args, **kw):
    return contenthub_vcm_query(
        operation=args.get("operation", ""),
        entity=args.get("entity"),
        query=args.get("query"),
    )


registry.register(
    name="contenthub_vcm_query",
    toolset="contenthub_vcm",
    schema=CONTENTHUB_VCM_SCHEMA,
    handler=_handle_contenthub_vcm_query,
    check_fn=check_contenthub_vcm_requirements,
    requires_env=["CONTENTHUB_CONVEX_SITE_URL", "CONTENTHUB_CONVEX_API_KEY"],
    description=CONTENTHUB_VCM_SCHEMA["description"],
    emoji="",
    max_result_size_chars=100_000,
)
