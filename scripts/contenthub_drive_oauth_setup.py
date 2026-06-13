r"""Generate Google Drive OAuth env values for ContentHub Hermes.

Usage:
    python scripts/contenthub_drive_oauth_setup.py C:\path\oauth-client.json

The script opens a local browser consent flow and prints the Coolify variables
needed by tools/contenthub_drive_evidence_tool.py. Do not commit the output.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/drive"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/contenthub_drive_oauth_setup.py <oauth-client-json>")
        return 2

    client_path = Path(sys.argv[1]).expanduser().resolve()
    if not client_path.exists():
        print(f"OAuth client JSON not found: {client_path}")
        return 2

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "Missing google-auth-oauthlib. Install hermes-agent[google] or run:\n"
            "python -m pip install google-auth-oauthlib==1.3.1"
        )
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), scopes=SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent")
    if not credentials.refresh_token:
        print("Google did not return a refresh_token. Re-run with a fresh consent grant.")
        return 1

    client_b64 = base64.b64encode(client_path.read_bytes()).decode("ascii")
    print("Paste these values into Coolify as secrets/env vars:")
    print()
    print(f"GOOGLE_OAUTH_CLIENT_JSON_B64={client_b64}")
    print(f"GOOGLE_OAUTH_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("Also set CONTENTHUB_DRIVE_ROOT_FOLDER_ID to the Drive folder ID.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
