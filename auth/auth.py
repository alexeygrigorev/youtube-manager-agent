#!/usr/bin/env python3
"""Shared YouTube Data API auth.

All credentials and runtime state live in the gitignored `.youtube/` folder
at the repo root:

  .youtube/client_secret.json   OAuth client (downloaded from Google Cloud)
  .youtube/token.json           cached user token (created on first run)

The first run opens a browser once for consent; after that the cached token
(with its refresh token) is reused with no browser.
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Full read/write scope: needed for videos.insert/update and playlist edits.
SCOPES = ["https://www.googleapis.com/auth/youtube"]

SECRETS_DIR = Path(__file__).resolve().parents[1] / ".youtube"
DEFAULT_CLIENT_SECRET = SECRETS_DIR / "client_secret.json"
DEFAULT_TOKEN = SECRETS_DIR / "token.json"


def get_service(client_secret: Path | None = None, token: Path | None = None):
    """Return an authorized youtube v3 service.

    Defaults to the credentials in `.youtube/`. Pass explicit paths to override.
    """
    client_secret = Path(client_secret) if client_secret else DEFAULT_CLIENT_SECRET
    token = Path(token) if token else DEFAULT_TOKEN

    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secret.exists():
                raise SystemExit(
                    f"Missing {client_secret}. Download an OAuth *Desktop app* "
                    f"client from Google Cloud Console and save it there "
                    f"(see README -> 'Google Cloud setup')."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
            creds = flow.run_local_server(port=0)
        token.parent.mkdir(parents=True, exist_ok=True)
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)
