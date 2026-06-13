"""ContentHub Drive evidence storage tool.

Uploads and organizes VcM evidence files in a Google Drive folder shared with
Hermes' service account. Convex remains the source of truth; this tool only
returns Drive IDs, URLs, and folder metadata for the ContentHub tool to audit.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from tools.registry import registry, tool_error, tool_result


DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


CONTENTHUB_DRIVE_SCHEMA = {
    "name": "contenthub_drive_evidence",
    "description": (
        "Crea carpetas y sube evidencias VcM a Google Drive usando la cuenta "
        "de servicio de Hermes. Usar cuando Hermes recibe fotos, PDF, videos, "
        "audios o documentos por WhatsApp/Telegram/email/dashboard y necesita "
        "dejarlos en la carpeta institucional correcta. Luego registrar los "
        "driveFileId, driveFolderId, webViewLink y estado en Convex con "
        "contenthub_vcm_query/contenthub_vcm_list."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": [
                    "ensure_folder",
                    "ensure_activity_folders",
                    "upload_file",
                    "get_file",
                    "list_children",
                ],
                "description": (
                    "Operacion Drive. ensure_activity_folders crea una ruta "
                    "estandar para actividad VcM. upload_file sube un archivo "
                    "local ya descargado desde WhatsApp u otro canal."
                ),
            },
            "path": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Segmentos de carpeta bajo CONTENTHUB_DRIVE_ROOT_FOLDER_ID. "
                    "Ej: ['2026', '2026-1', 'Actividades', 'ACT-2026-00034 - Taller']."
                ),
            },
            "activityCode": {
                "type": "string",
                "description": "Codigo institucional de actividad, por ejemplo ACT-2026-00034.",
            },
            "activityTitle": {
                "type": "string",
                "description": "Titulo de actividad para nombrar carpeta.",
            },
            "year": {
                "type": "string",
                "description": "Ano de trazabilidad, por ejemplo 2026.",
            },
            "period": {
                "type": "string",
                "description": "Periodo academico o carpeta secundaria, por ejemplo 2026-1.",
            },
            "subfolder": {
                "type": "string",
                "enum": [
                    "01_Originales_WhatsApp",
                    "02_Evidencias_Validadas",
                    "03_Audios_Transcripciones",
                    "04_Reportes",
                    "Pendientes_Clasificacion",
                ],
                "description": "Subcarpeta estandar dentro de una actividad.",
            },
            "parentFolderId": {
                "type": "string",
                "description": "Folder ID padre opcional. Si se omite, usa CONTENTHUB_DRIVE_ROOT_FOLDER_ID.",
            },
            "folderName": {
                "type": "string",
                "description": "Nombre de carpeta para ensure_folder.",
            },
            "localPath": {
                "type": "string",
                "description": "Ruta local del archivo temporal a subir.",
            },
            "fileName": {
                "type": "string",
                "description": "Nombre final en Drive. Si se omite, usa el nombre local.",
            },
            "mimeType": {
                "type": "string",
                "description": "MIME type opcional. Si se omite, se infiere por extension.",
            },
            "description": {
                "type": "string",
                "description": "Descripcion/metadata visible del archivo en Drive.",
            },
            "fileId": {
                "type": "string",
                "description": "Drive file ID para get_file.",
            },
        },
        "required": ["operation"],
    },
}


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def check_contenthub_drive_requirements() -> bool:
    return bool(
        _env("CONTENTHUB_DRIVE_ROOT_FOLDER_ID")
        and (
            _env("GOOGLE_SERVICE_ACCOUNT_JSON")
            or _env("GOOGLE_SERVICE_ACCOUNT_JSON_B64")
            or _env("GOOGLE_SERVICE_ACCOUNT_FILE")
        )
    )


def _service_account_info() -> dict[str, Any]:
    raw_json = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
    raw_b64 = _env("GOOGLE_SERVICE_ACCOUNT_JSON_B64")
    file_path = _env("GOOGLE_SERVICE_ACCOUNT_FILE")

    if raw_json:
        return json.loads(raw_json)
    if raw_b64:
        return json.loads(base64.b64decode(raw_b64).decode("utf-8"))
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    raise RuntimeError(
        "Missing GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SERVICE_ACCOUNT_JSON_B64, or GOOGLE_SERVICE_ACCOUNT_FILE."
    )


def _drive_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Google Drive dependencies are missing. Install hermes-agent[google] "
            "or add google-api-python-client and google-auth."
        ) from exc

    credentials = service_account.Credentials.from_service_account_info(
        _service_account_info(),
        scopes=DRIVE_SCOPES,
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _folder_query(name: str, parent_id: str) -> str:
    safe_name = name.replace("\\", "\\\\").replace("'", "\\'")
    return (
        "mimeType = 'application/vnd.google-apps.folder' "
        f"and name = '{safe_name}' "
        f"and '{parent_id}' in parents "
        "and trashed = false"
    )


def _ensure_folder(service, name: str, parent_id: str) -> dict[str, Any]:
    response = service.files().list(
        q=_folder_query(name, parent_id),
        spaces="drive",
        fields="files(id, name, webViewLink)",
        pageSize=10,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
    ).execute()
    files = response.get("files", [])
    if files:
        return {**files[0], "created": False}

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(
        body=metadata,
        fields="id, name, webViewLink",
        supportsAllDrives=True,
    ).execute()
    return {**folder, "created": True}


def _ensure_path(service, path: list[str], parent_id: str) -> dict[str, Any]:
    current_parent = parent_id
    created_any = False
    folders = []

    for raw_segment in path:
        segment = " ".join(str(raw_segment or "").strip().split())
        if not segment:
            continue
        folder = _ensure_folder(service, segment, current_parent)
        folders.append(folder)
        created_any = created_any or bool(folder.get("created"))
        current_parent = folder["id"]

    return {
        "folderId": current_parent,
        "folders": folders,
        "created": created_any,
    }


def _activity_base_path(args: dict[str, Any]) -> list[str]:
    year = str(args.get("year") or "").strip()
    period = str(args.get("period") or "").strip()
    code = str(args.get("activityCode") or "").strip()
    title = str(args.get("activityTitle") or "").strip()

    if not year or not code or not title:
        raise ValueError("ensure_activity_folders requires year, activityCode, and activityTitle.")

    activity_folder = f"{code} - {title}"
    path = [year]
    if period:
        path.append(period)
    path.extend(["Actividades", activity_folder])
    return path


def _upload_file(
    service,
    *,
    local_path: str,
    parent_id: str,
    file_name: str | None,
    mime_type: str | None,
    description: str | None,
) -> dict[str, Any]:
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise RuntimeError("google-api-python-client is required for Drive uploads.") from exc

    path = Path(local_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {local_path}")

    final_name = file_name or path.name
    guessed_mime = mime_type or mimetypes.guess_type(final_name)[0] or "application/octet-stream"
    metadata: dict[str, Any] = {
        "name": final_name,
        "parents": [parent_id],
    }
    if description:
        metadata["description"] = description

    media = MediaFileUpload(str(path), mimetype=guessed_mime, resumable=True)
    return service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, mimeType, size, md5Checksum, webViewLink, webContentLink, parents",
        supportsAllDrives=True,
    ).execute()


def contenthub_drive_evidence(args: dict[str, Any], **kw) -> str:
    operation = args.get("operation")
    root_id = args.get("parentFolderId") or _env("CONTENTHUB_DRIVE_ROOT_FOLDER_ID")

    if not root_id:
        return tool_error(
            "Missing CONTENTHUB_DRIVE_ROOT_FOLDER_ID or parentFolderId.",
            error_type="configuration_missing",
            source="contenthub_drive",
        )

    try:
        service = _drive_service()

        if operation == "ensure_folder":
            folder_name = args.get("folderName")
            if not folder_name:
                return tool_error("ensure_folder requires folderName.", error_type="invalid_arguments")
            folder = _ensure_folder(service, str(folder_name), root_id)
            return tool_result(source="contenthub_drive", data=folder)

        if operation == "ensure_activity_folders":
            base_path = _activity_base_path(args)
            subfolder = args.get("subfolder")
            final_path = base_path + ([subfolder] if subfolder else [])
            result = _ensure_path(service, final_path, root_id)
            return tool_result(source="contenthub_drive", data={**result, "path": final_path})

        if operation == "upload_file":
            upload_parent = root_id
            path = args.get("path")
            if isinstance(path, list) and path:
                upload_parent = _ensure_path(service, path, root_id)["folderId"]
            elif args.get("folderName"):
                upload_parent = _ensure_folder(service, str(args["folderName"]), root_id)["id"]

            file_result = _upload_file(
                service,
                local_path=str(args.get("localPath") or ""),
                parent_id=upload_parent,
                file_name=args.get("fileName"),
                mime_type=args.get("mimeType"),
                description=args.get("description"),
            )
            return tool_result(
                source="contenthub_drive",
                data={**file_result, "driveFolderId": upload_parent},
            )

        if operation == "get_file":
            file_id = args.get("fileId")
            if not file_id:
                return tool_error("get_file requires fileId.", error_type="invalid_arguments")
            file_result = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, md5Checksum, webViewLink, webContentLink, parents, trashed",
                supportsAllDrives=True,
            ).execute()
            return tool_result(source="contenthub_drive", data=file_result)

        if operation == "list_children":
            response = service.files().list(
                q=f"'{root_id}' in parents and trashed = false",
                spaces="drive",
                fields="files(id, name, mimeType, webViewLink, parents)",
                pageSize=100,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            ).execute()
            return tool_result(source="contenthub_drive", data=response.get("files", []))

        return tool_error(f"Unsupported operation: {operation}", error_type="invalid_operation")
    except Exception as exc:
        details = str(exc)
        if "Service Accounts do not have storage quota" in details:
            return tool_error(
                "Google Drive rejected the upload because service accounts do not have storage quota. "
                "Use a Google Workspace Shared Drive as CONTENTHUB_DRIVE_ROOT_FOLDER_ID, or configure "
                "OAuth/domain-wide delegation for a real Workspace user.",
                error_type="service_account_storage_quota",
                source="contenthub_drive",
            )
        return tool_error(
            details,
            error_type=type(exc).__name__,
            source="contenthub_drive",
        )


registry.register(
    name="contenthub_drive_evidence",
    toolset="contenthub_drive",
    schema=CONTENTHUB_DRIVE_SCHEMA,
    handler=contenthub_drive_evidence,
    check_fn=check_contenthub_drive_requirements,
    requires_env=[
        "CONTENTHUB_DRIVE_ROOT_FOLDER_ID",
        "GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_SERVICE_ACCOUNT_JSON_B64 or GOOGLE_SERVICE_ACCOUNT_FILE",
    ],
    description=CONTENTHUB_DRIVE_SCHEMA["description"],
    emoji="",
    max_result_size_chars=80_000,
)
