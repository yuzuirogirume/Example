#!/usr/bin/env python3
"""One-time helper to create token.json from OAuth client credentials.

1. Create a Google Cloud project and enable the Google Calendar API.
2. Create an OAuth 2.0 Client ID of type "Desktop app".
3. Download the JSON and save it as ./client_secret.json (or set
   GCAL_OAUTH_CLIENT_FILE).
4. Run: python init_oauth.py
   A browser window opens; sign in with the Gmail account whose calendar
   you want to write to and grant the calendar.events scope.
5. token.json is written next to client_secret.json.
"""
from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main() -> None:
    client_file = Path(os.environ.get("GCAL_OAUTH_CLIENT_FILE", "client_secret.json"))
    token_file = Path(os.environ.get("GCAL_TOKEN_FILE", "token.json"))
    if not client_file.exists():
        raise SystemExit(f"OAuth client file not found: {client_file}")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
    creds = flow.run_local_server(port=0)
    token_file.write_text(creds.to_json())
    print(f"Saved credentials to {token_file}")


if __name__ == "__main__":
    main()
