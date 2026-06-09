"""ContentHub VcM CRUD tool.

Connects Hermes to the ContentHub Convex HTTP API. CRUD writes are document-level
only and are guarded by the Convex endpoints: no drops, cascades or bulk deletes.
"""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

from tools.registry import registry

ENTITY_CATALOG = {
    "users": {
        "fields": ["name", "email", "username", "role", "status", "initials", "createdAt", "updatedAt"],
        "enums": {"role": ["coordinadora", "cm", "director", "docente", "staff"], "status": ["activo", "inactivo"]},
    },
    "channelContacts": {
        "fields": ["userId", "displayName", "channel", "externalId", "status", "lastInteractionAt", "createdAt", "updatedAt"],
        "enums": {"channel": ["whatsapp", "telegram", "email"], "status": ["activo", "inactivo", "bloqueado"]},
    },
    "agreements": {
        "fields": ["name", "partner", "country", "region", "type", "status", "ownerUserId", "startDate", "endDate", "strategicLine", "summary", "createdAt", "updatedAt"],
        "enums": {
            "type": ["internacional", "nacional", "publico", "privado"],
            "status": ["activo", "pendiente", "por_verificar", "cerrado"],
            "strategicLine": ["internacionalizacion", "formacion_continua", "docencia_vinculada", "investigacion_aplicada", "innovacion_emprendimiento", "asistencia_tecnica"],
        },
    },
    "activities": {
        "fields": ["title", "description", "strategicLine", "status", "ownerUserId", "agreementId", "source", "audience", "participantEstimate", "missingEvidenceCount", "riskLevel", "startDate", "endDate", "monthLabel", "color", "createdAt", "updatedAt"],
        "enums": {
            "status": ["planificado", "en_preparacion", "en_ejecucion", "por_aprobar", "cerrado", "en_riesgo"],
            "riskLevel": ["bajo", "medio", "alto"],
            "source": ["manual", "whatsapp_audio", "email", "drive"],
        },
    },
    "activityTasks": {
        "fields": ["activityId", "phase", "text", "done", "responsible", "order", "updatedAt"],
        "enums": {"phase": ["pre", "durante", "post"]},
    },
    "activityReports": {
        "fields": ["activityId", "submittedByUserId", "contactId", "source", "transcript", "extractedSummary", "status", "missingFields", "confidence", "submittedAt", "reviewedAt", "reviewedByUserId", "createdAt", "updatedAt"],
        "enums": {
            "source": ["whatsapp_audio", "whatsapp_text", "telegram", "manual", "email"],
            "status": ["borrador", "pendiente_validacion", "aprobado", "rechazado", "registrado"],
        },
    },
    "evidenceFiles": {
        "fields": ["activityId", "reportId", "uploadedByUserId", "name", "type", "url", "status", "requestedReason", "uploadedAt", "createdAt", "updatedAt"],
        "enums": {"type": ["foto", "pdf", "documento", "planilla", "link"], "status": ["solicitada", "recibida", "validada", "rechazada"]},
    },
    "budgetItems": {
        "fields": ["activityId", "name", "amount", "status", "category", "createdAt"],
        "enums": {"status": ["estimado", "ejecutado"]},
    },
    "contentProposals": {
        "fields": ["authorUserId", "authorName", "authorInitials", "channel", "format", "activityId", "status", "copy", "hashtags", "visualBrief", "rejectionReason", "scheduledAt", "createdAt", "updatedAt"],
        "enums": {
            "channel": ["instagram", "linkedin", "web", "email"],
            "format": ["reel", "post", "story", "carrusel", "nota"],
            "status": ["pendiente", "aprobada", "rechazada", "programada"],
        },
    },
    "initiatives": {
        "fields": ["title", "objective", "strategicLine", "status", "progress", "owner", "nextMilestone", "dueDate", "createdAt", "updatedAt"],
        "enums": {"status": ["activa", "preparacion", "cerrada", "en_riesgo"]},
    },
    "indicators": {
        "fields": ["group", "name", "value", "unit", "target", "trend", "period", "updatedAt"],
        "enums": {"group": ["internacionalizacion", "vcm"], "trend": ["sube", "baja", "estable"]},
    },
    "dashboardItems": {
        "fields": ["kind", "title", "value", "subtitle", "column", "status", "order", "createdAt"],
        "enums": {"kind": ["kpi", "kanban", "attention"]},
    },
    "routePages": {
        "fields": ["slug", "title", "description", "status", "updatedAt"],
        "enums": {"status": ["disponible", "en_construccion"]},
    },
    "notifications": {
        "fields": ["userId", "contactId", "channel", "title", "body", "status", "relatedActivityId", "createdAt", "sentAt"],
        "enums": {"channel": ["app", "email", "whatsapp", "telegram"], "status": ["pendiente", "enviada", "fallida", "leida"]},
    },
    "auditEvents": {
        "fields": ["actorUserId", "agentSessionId", "entityType", "entityId", "action", "summary", "createdAt"],
        "enums": {"entityType": ["activity", "activityReport", "evidenceFile", "contentProposal", "agreement", "user", "system"]},
    },
    "agentSessions": {
        "fields": ["agentName", "purpose", "status", "relatedActivityId", "createdByUserId", "createdAt", "updatedAt"],
        "enums": {"status": ["activa", "cerrada", "fallida"]},
    },
    "agentMessages": {
        "fields": ["sessionId", "role", "content", "createdAt"],
        "enums": {"role": ["user", "assistant", "system", "tool"]},
    },
    "agentToolCalls": {
        "fields": ["sessionId", "toolName", "inputSummary", "outputSummary", "status", "createdAt"],
        "enums": {"status": ["ok", "error"]},
    },
}

ENTITY_NAMES = list(ENTITY_CATALOG)
ENTITY_CATALOG_TEXT = "; ".join(
    f"{entity}({', '.join(spec['fields'])})"
    for entity, spec in ENTITY_CATALOG.items()
)


CONTENTHUB_VCM_SCHEMA = {
    "name": "contenthub_vcm_query",
    "description": (
        "Consulta y modifica datos operativos reales de ContentHub VcM desde Convex. "
        "Convex es la fuente de verdad: usar antes de responder sobre convenios, "
        "actividades, evidencias, reportes, propuestas de contenido, indicadores, "
        "notificaciones o auditoria. Para listas por estado/tipo/canal/fecha, "
        "preferir operation=list o la tool contenthub_vcm_list; para overview, schema, "
        "get/create/update/delete usar esta tool. CRUD es documental y auditado: "
        "sin drops, sin cascades, sin truncates, sin borrados masivos."
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
                    "schema",
                    "search",
                    "list",
                    "get",
                    "create",
                    "update",
                    "delete",
                ],
                "description": (
                    "Consulta operativa a ejecutar. Usa list para preguntas como 'convenios activos', "
                    "'todos los convenios', 'evidencias faltantes', 'propuestas pendientes' o "
                    "'actividades por region'. Usa search solo para texto libre; usa schema si dudas "
                    "sobre entidades/campos; usa overview para resumen ejecutivo."
                ),
            },
            "entity": {
                "type": "string",
                "enum": ENTITY_NAMES,
                "description": f"Tabla/entidad para search, list, get, create, update o delete. Catalogo: {ENTITY_CATALOG_TEXT}",
            },
            "query": {
                "type": "string",
                "description": (
                    "Texto de busqueda o filtro natural. Ej: activo, vigente, todos. "
                    "Para estados conocidos conviene usar filters; no concluyas cero resultados "
                    "solo por buscar una palabra si existe un campo status."
                ),
            },
            "filters": {
                "type": "object",
                "description": (
                    "Filtros flexibles para operation=list. Puede usar exacto {\"status\":\"activo\"}, "
                    "listas {\"status\":[\"activo\",\"pendiente\"]}, o operadores "
                    "{\"participantEstimate\":{\"$gte\":20}}, {\"name\":{\"$contains\":\"PUCV\"}}, "
                    "{\"status\":{\"$ne\":\"cerrado\"}}."
                ),
            },
            "id": {
                "type": "string",
                "description": "ID Convex del documento para get, update o delete.",
            },
            "data": {
                "type": "object",
                "description": (
                    "Documento para create. Usar solo campos existentes de la entidad. "
                    "Para propuestas CM usar contentProposals con channel, format, copy, hashtags, "
                    "visualBrief, activityId si existe y status normalmente pendiente."
                ),
            },
            "patch": {
                "type": "object",
                "description": (
                    "Campos a modificar para update. No modificar _id ni _creationTime. "
                    "Para programacion CM, solo usar campos existentes como status y scheduledAt, "
                    "y no programar propuestas no aprobadas."
                ),
            },
            "mode": {
                "type": "string",
                "enum": ["soft", "hard"],
                "description": "Modo de delete. Preferir soft.",
            },
            "confirm": {
                "type": "string",
                "description": "Para hard delete debe ser PERMANENT_DELETE_ONE.",
            },
            "reason": {
                "type": "string",
                "description": (
                    "Motivo obligatorio para operaciones de escritura. Debe ser audit-ready, "
                    "por ejemplo 'CM solicito crear propuesta LinkedIn desde actividad X'."
                ),
            },
            "limit": {
                "type": "integer",
                "description": "Maximo de resultados para operation=list/search, por defecto 100.",
            },
            "sortBy": {
                "type": "string",
                "description": "Atributo por el cual ordenar despues de consultar Convex.",
            },
            "sortDirection": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Direccion de ordenamiento.",
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Atributos a devolver. Omitir para devolver el documento completo.",
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
    "schema": "/hermes/schema",
}

CONTENTHUB_VCM_LIST_SCHEMA = {
    "name": "contenthub_vcm_list",
    "description": (
        "Lista registros reales de una tabla ContentHub VcM desde Convex con filtros flexibles. "
        "Preferir para preguntas por entidad/estado/tipo/canal/fecha: 'convenios activos', "
        "'listar todos los convenios', 'evidencias faltantes', 'reportes pendientes', "
        "'propuestas de contenido pendientes', 'actividades en riesgo'. Evita responder "
        "cero resultados por una busqueda textual pobre: inspecciona la entidad y campos plausibles."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entity": {
                "type": "string",
                "enum": ENTITY_NAMES,
                "description": f"Tabla a listar. Catalogo de entidades y atributos: {ENTITY_CATALOG_TEXT}",
            },
            "filters": {
                "type": "object",
                "description": (
                    "Filtros libres sobre atributos de la entidad. Soporta exacto, array/in, "
                    "$contains, $in, $ne, $gt, $gte, $lt, $lte. Ej: {\"status\":\"activo\"}, "
                    "{\"region\":{\"$contains\":\"Valparaiso\"}}, {\"startDate\":{\"$gte\":\"2026-01-01\"}}."
                ),
            },
            "query": {
                "type": "string",
                "description": "Filtro natural o busqueda textual. Ej: activo, vigente, todos.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximo de resultados, por defecto 100.",
            },
            "sortBy": {
                "type": "string",
                "description": "Atributo por el cual ordenar despues de consultar Convex. Ej: startDate, updatedAt, name.",
            },
            "sortDirection": {
                "type": "string",
                "enum": ["asc", "desc"],
                "description": "Direccion de ordenamiento.",
            },
            "fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Atributos a devolver. Omitir para devolver el documento completo.",
            },
        },
        "required": ["entity"],
    },
}


_CRUD_PATHS = {
    "list": "/hermes/crud/list",
    "get": "/hermes/crud/get",
    "create": "/hermes/crud/create",
    "update": "/hermes/crud/update",
    "delete": "/hermes/crud/delete",
}


_STATUS_ALIASES = {
    "activo": "activo",
    "activos": "activo",
    "activa": "activo",
    "activas": "activo",
    "active": "activo",
    "vigente": "activo",
    "vigentes": "activo",
    "pendiente": "pendiente",
    "pendientes": "pendiente",
    "por verificar": "por_verificar",
    "por_verificar": "por_verificar",
    "verificar": "por_verificar",
    "cerrado": "cerrado",
    "cerrados": "cerrado",
    "cerrada": "cerrado",
    "cerradas": "cerrado",
}


_LIST_ALL_TERMS = {
    "",
    "todo",
    "todos",
    "todas",
    "all",
    "list",
    "lista",
    "listar",
    "listar todo",
    "listar todos",
    "listar todas",
    "lista todo",
    "lista todos",
    "lista todas",
    "convenio",
    "convenios",
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


def _natural_filters(entity: str | None, query: str | None) -> dict[str, Any] | None:
    if not entity or "status" not in ENTITY_CATALOG.get(entity, {}).get("fields", []):
        return None

    normalized = " ".join((query or "").strip().lower().replace("_", " ").split())
    if normalized in _STATUS_ALIASES:
        return {"status": _STATUS_ALIASES[normalized]}

    if normalized.startswith("status:"):
        status = normalized.split(":", 1)[1].strip().replace(" ", "_")
        return {"status": _STATUS_ALIASES.get(status, status)}

    return None


def _is_list_all_query(query: str | None) -> bool:
    normalized = " ".join((query or "").strip().lower().split())
    return normalized in _LIST_ALL_TERMS


def _post_json(client: httpx.Client, base_url: str, headers: dict[str, str], path: str, payload: dict[str, Any]) -> httpx.Response:
    return client.post(
        f"{base_url}{path}",
        headers={**headers, "content-type": "application/json"},
        json=payload,
    )


def _is_operator_filter(value: Any) -> bool:
    return isinstance(value, dict) and any(str(key).startswith("$") for key in value)


def _server_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    if not filters:
        return {}

    # Convex endpoint supports exact equality and arrays. Keep richer operators
    # for client-side post-filtering after fetching a broader result set.
    return {
        field: expected
        for field, expected in filters.items()
        if not _is_operator_filter(expected)
    }


def _to_comparable(value: Any) -> Any:
    if isinstance(value, str):
        return value.lower()
    return value


def _matches_filter(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        for operator, operand in expected.items():
            if operator == "$contains":
                if isinstance(actual, list):
                    if not any(str(operand).lower() in str(item).lower() for item in actual):
                        return False
                elif str(operand).lower() not in str(actual or "").lower():
                    return False
            elif operator == "$in":
                if actual not in (operand or []):
                    return False
            elif operator == "$ne":
                if actual == operand:
                    return False
            elif operator == "$gt":
                if not (actual is not None and actual > operand):
                    return False
            elif operator == "$gte":
                if not (actual is not None and actual >= operand):
                    return False
            elif operator == "$lt":
                if not (actual is not None and actual < operand):
                    return False
            elif operator == "$lte":
                if not (actual is not None and actual <= operand):
                    return False
            else:
                return False
        return True

    if isinstance(expected, list):
        return actual in expected

    return actual == expected


def _postprocess_records(
    data: Any,
    *,
    filters: dict[str, Any] | None,
    sort_by: str | None,
    sort_direction: str | None,
    fields: list[str] | None,
    limit: int | None,
) -> Any:
    if not isinstance(data, list):
        return data

    records = [
        record for record in data
        if isinstance(record, dict)
        and all(_matches_filter(record.get(field), expected) for field, expected in (filters or {}).items())
    ]

    if sort_by:
        reverse = sort_direction == "desc"
        records = sorted(records, key=lambda record: _to_comparable(record.get(sort_by)), reverse=reverse)

    if fields:
        always = ["_id", "_creationTime"]
        selected = [field for field in always + fields if field]
        records = [
            {field: record.get(field) for field in selected if field in record}
            for record in records
        ]

    if limit:
        records = records[: max(1, min(int(limit), 200))]

    return records


def contenthub_vcm_query(
    operation: str,
    entity: str | None = None,
    query: str | None = None,
    filters: dict[str, Any] | None = None,
    id: str | None = None,
    data: dict[str, Any] | None = None,
    patch: dict[str, Any] | None = None,
    mode: str | None = None,
    confirm: str | None = None,
    reason: str | None = None,
    limit: int | None = None,
    sortBy: str | None = None,
    sortDirection: str | None = None,
    fields: list[str] | None = None,
) -> str:
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
            elif operation in _CRUD_PATHS:
                if not entity:
                    return _tool_error(f"operation={operation} requires entity.", error_type="invalid_arguments")

                payload: dict[str, Any] = {"table": entity}
                if operation == "list":
                    effective_filters = filters or _natural_filters(entity, query) or {}
                    payload["filters"] = _server_filters(effective_filters)
                    if query and not payload["filters"] and not _is_list_all_query(query):
                        payload["search"] = query.strip()
                    payload["limit"] = 200
                elif operation == "get":
                    if not id:
                        return _tool_error("operation=get requires id.", error_type="invalid_arguments")
                    payload["id"] = id
                elif operation == "create":
                    if not data:
                        return _tool_error("operation=create requires data.", error_type="invalid_arguments")
                    payload["data"] = data
                    payload["reason"] = reason or "Hermes create requested from conversation"
                elif operation == "update":
                    if not id or not patch:
                        return _tool_error("operation=update requires id and patch.", error_type="invalid_arguments")
                    payload["id"] = id
                    payload["patch"] = patch
                    payload["reason"] = reason or "Hermes update requested from conversation"
                elif operation == "delete":
                    if not id:
                        return _tool_error("operation=delete requires id.", error_type="invalid_arguments")
                    payload["id"] = id
                    payload["mode"] = mode or "soft"
                    if confirm:
                        payload["confirm"] = confirm
                    payload["reason"] = reason or "Hermes delete requested from conversation"

                response = _post_json(client, base_url, headers, _CRUD_PATHS[operation], payload)
            elif operation == "search":
                if not entity:
                    return _tool_error("operation=search requires entity.", error_type="invalid_arguments")
                natural_filters = filters or _natural_filters(entity, query)
                if natural_filters or _is_list_all_query(query):
                    effective_filters = natural_filters or {}
                    response = _post_json(
                        client,
                        base_url,
                        headers,
                        "/hermes/crud/list",
                        {"table": entity, "filters": _server_filters(effective_filters), "limit": 200},
                    )
                else:
                    if not query or len(query.strip()) < 2:
                        return _tool_error("operation=search requires a query with at least 2 characters.", error_type="invalid_arguments")
                    response = _post_json(
                        client,
                        base_url,
                        headers,
                        "/hermes/search",
                        {"entity": entity, "query": query.strip()},
                    )
            else:
                return _tool_error(f"Unsupported operation: {operation}", error_type="invalid_operation")

            response.raise_for_status()
            data = response.json()
            if operation in {"list", "search"}:
                data = _postprocess_records(
                    data,
                    filters=filters or _natural_filters(entity, query) or {},
                    sort_by=sortBy,
                    sort_direction=sortDirection,
                    fields=fields,
                    limit=limit or 100,
                )
            return _json_response(data)
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
        filters=args.get("filters"),
        id=args.get("id"),
        data=args.get("data"),
        patch=args.get("patch"),
        mode=args.get("mode"),
        confirm=args.get("confirm"),
        reason=args.get("reason"),
        limit=args.get("limit"),
        sortBy=args.get("sortBy"),
        sortDirection=args.get("sortDirection"),
        fields=args.get("fields"),
    )


def _handle_contenthub_vcm_list(args, **kw):
    return contenthub_vcm_query(
        operation="list",
        entity=args.get("entity"),
        query=args.get("query"),
        filters=args.get("filters"),
        limit=args.get("limit"),
        sortBy=args.get("sortBy"),
        sortDirection=args.get("sortDirection"),
        fields=args.get("fields"),
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

registry.register(
    name="contenthub_vcm_list",
    toolset="contenthub_vcm",
    schema=CONTENTHUB_VCM_LIST_SCHEMA,
    handler=_handle_contenthub_vcm_list,
    check_fn=check_contenthub_vcm_requirements,
    requires_env=["CONTENTHUB_CONVEX_SITE_URL", "CONTENTHUB_CONVEX_API_KEY"],
    description=CONTENTHUB_VCM_LIST_SCHEMA["description"],
    emoji="",
    max_result_size_chars=100_000,
)
