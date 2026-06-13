"""Google Forms submission helper for ContentHub Hermes.

This avoids browser automation for simple Google Forms. It can inspect a public
form page enough to discover entry IDs and submit values directly to the
formResponse endpoint. Authenticated, file-upload, CAPTCHA, and dynamically
validated forms still require a human/browser workflow.
"""

from __future__ import annotations

import html
import json
import re
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from tools.registry import registry, tool_error, tool_result


GOOGLE_FORMS_SCHEMA = {
    "name": "contenthub_google_form",
    "description": (
        "Inspecciona o responde formularios de Google Forms sin navegador. "
        "Usar para formularios publicos simples cuando Hermes debe enviar "
        "datos estructurados VcM. No usar para formularios que requieren login, "
        "carga de archivos, CAPTCHA o validacion humana."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["inspect", "submit"],
                "description": "inspect descubre campos entry.*; submit envia una respuesta.",
            },
            "formUrl": {
                "type": "string",
                "description": "URL de Google Form viewform, prefilled link o formResponse.",
            },
            "responses": {
                "type": "object",
                "description": (
                    "Mapa de respuestas para submit. Preferir keys entry.<id>. "
                    "Tambien acepta labels exactos si inspect puede asociarlos."
                ),
            },
            "dryRun": {
                "type": "boolean",
                "description": "Si true, no envia; devuelve URL/payload normalizado.",
            },
        },
        "required": ["operation", "formUrl"],
    },
}


def _normalize_form_url(url: str, *, submit: bool = False) -> str:
    parsed = urlparse(url.strip())
    path = parsed.path
    if "/forms/d/e/" not in path and "/forms/d/" not in path:
        raise ValueError("Expected a Google Forms URL containing /forms/d/ or /forms/d/e/.")

    if submit:
        if path.endswith("/viewform"):
            path = path[: -len("/viewform")] + "/formResponse"
        elif not path.endswith("/formResponse"):
            path = path.rstrip("/") + "/formResponse"
    else:
        if path.endswith("/formResponse"):
            path = path[: -len("/formResponse")] + "/viewform"
        elif not path.endswith("/viewform"):
            path = path.rstrip("/") + "/viewform"

    return urlunparse((parsed.scheme or "https", parsed.netloc, path, "", parsed.query, ""))


def _extract_title(text: str) -> str | None:
    match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    title = html.unescape(re.sub(r"\s+", " ", match.group(1)).strip())
    return title.replace(" - Google Forms", "").strip() or title


def _extract_entry_ids(text: str) -> list[str]:
    return sorted(set(re.findall(r"entry\.(\d+)", text)))


def _extract_prefilled_values(url: str) -> dict[str, list[str]]:
    query = parse_qs(urlparse(url).query)
    return {
        key: value
        for key, value in query.items()
        if key.startswith("entry.") and value
    }


def _extract_label_map(text: str) -> dict[str, str]:
    # Google embeds FB_PUBLIC_LOAD_DATA_ with each question block. This regex is
    # intentionally conservative: it catches common public form pages while
    # avoiding a brittle full parser for Google's internal data array.
    labels: dict[str, str] = {}
    for match in re.finditer(r'\["([^"]{1,200})",\s*null,\s*\[\[\s*(\d{4,})', text):
        label = html.unescape(match.group(1)).strip()
        entry = f"entry.{match.group(2)}"
        if label and entry not in labels:
            labels[label] = entry
    return labels


def _inspect_form(form_url: str) -> dict[str, Any]:
    view_url = _normalize_form_url(form_url, submit=False)
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.get(view_url)
        response.raise_for_status()
    text = response.text
    entry_ids = _extract_entry_ids(text)
    label_map = _extract_label_map(text)
    return {
        "title": _extract_title(text),
        "viewUrl": str(response.url),
        "submitUrl": _normalize_form_url(str(response.url), submit=True),
        "entries": [f"entry.{entry_id}" for entry_id in entry_ids],
        "labels": label_map,
        "prefilledValues": _extract_prefilled_values(form_url),
        "limitations": [
            "No browser is used.",
            "Login, CAPTCHA, file upload, and complex client-side validation are not supported.",
        ],
    }


def _resolve_responses(responses: dict[str, Any], labels: dict[str, str]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in (responses or {}).items():
        target = key if str(key).startswith("entry.") else labels.get(str(key), str(key))
        if not str(target).startswith("entry."):
            raise ValueError(f"Response key {key!r} is not an entry.* field and no label match was found.")
        resolved[target] = value
    return resolved


def _submit_form(form_url: str, responses: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    form = _inspect_form(form_url)
    submit_url = form["submitUrl"]
    resolved = _resolve_responses(responses, form["labels"])
    if not resolved:
        raise ValueError("submit requires responses.")

    payload: list[tuple[str, str]] = []
    for key, value in resolved.items():
        if isinstance(value, list):
            for item in value:
                payload.append((key, str(item)))
        else:
            payload.append((key, str(value)))

    if dry_run:
        return {
            "submitUrl": submit_url,
            "payload": payload,
            "encodedPayload": urlencode(payload),
            "dryRun": True,
        }

    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "Hermes ContentHub VcM",
    }
    with httpx.Client(timeout=20.0, follow_redirects=False) as client:
        response = client.post(submit_url, data=payload, headers=headers)

    # Google Forms commonly returns 200 with a confirmation page or 302.
    ok = response.status_code in {200, 302}
    return {
        "submitted": ok,
        "statusCode": response.status_code,
        "submitUrl": submit_url,
        "entriesSubmitted": sorted(resolved),
    }


def contenthub_google_form(args: dict[str, Any], **kw) -> str:
    operation = args.get("operation")
    form_url = str(args.get("formUrl") or "").strip()
    if not form_url:
        return tool_error("formUrl is required.", error_type="invalid_arguments", source="google_forms")

    try:
        if operation == "inspect":
            return tool_result(source="google_forms", data=_inspect_form(form_url))
        if operation == "submit":
            result = _submit_form(
                form_url,
                args.get("responses") or {},
                bool(args.get("dryRun")),
            )
            return tool_result(source="google_forms", data=result)
        return tool_error(f"Unsupported operation: {operation}", error_type="invalid_operation", source="google_forms")
    except Exception as exc:
        return tool_error(str(exc), error_type=type(exc).__name__, source="google_forms")


registry.register(
    name="contenthub_google_form",
    toolset="contenthub_forms",
    schema=GOOGLE_FORMS_SCHEMA,
    handler=contenthub_google_form,
    description=GOOGLE_FORMS_SCHEMA["description"],
    emoji="",
    max_result_size_chars=60_000,
)
