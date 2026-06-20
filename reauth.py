#!/usr/bin/env python3
"""Check, refresh, or re-create the cached YouTube OAuth token.

  python reauth.py            # check token; auto-refresh if expired, re-consent if dead
  python reauth.py --check    # check only; never opens a browser or deletes anything
  python reauth.py --force    # discard the cached token and re-consent from scratch

Apps left in OAuth "Testing" mode get refresh tokens that Google expires after
7 days, so a weekly `invalid_grant` is normal — just run this to re-auth. (Publish
the consent screen to Production to stop the 7-day expiry.)
"""
import argparse
import sys
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

from auth import DEFAULT_CLIENT_SECRET, DEFAULT_TOKEN, SCOPES


def _safe_print(s: str) -> None:
    """Print, tolerating consoles (e.g. Windows cp1252) that can't encode emoji."""
    enc = sys.stdout.encoding or "utf-8"
    print(s.encode(enc, errors="replace").decode(enc, errors="replace"))


def _whoami(creds) -> None:
    """Print the channel the credentials belong to (1 quota unit)."""
    yt = build("youtube", "v3", credentials=creds)
    r = yt.channels().list(part="snippet", mine=True).execute()
    items = r.get("items", [])
    if items:
        sn = items[0]["snippet"]
        _safe_print(f"authorized as: {sn['title']}  (channel {items[0]['id']})")


def _consent(client_secret: Path, token: Path) -> Credentials:
    if not client_secret.exists():
        raise SystemExit(
            f"Missing {client_secret}. Download an OAuth *Desktop app* client "
            f"from Google Cloud Console and save it there (see README)."
        )
    print("opening browser for consent...")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
    creds = flow.run_local_server(port=0)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(creds.to_json(), encoding="utf-8")
    print(f"wrote fresh token -> {token}")
    return creds


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="report status only; never open a browser or delete the token")
    ap.add_argument("--force", action="store_true",
                    help="discard the cached token and re-consent from scratch")
    ap.add_argument("--client-secret", type=Path, default=DEFAULT_CLIENT_SECRET)
    ap.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    args = ap.parse_args()

    token: Path = args.token

    if args.force:
        if args.check:
            ap.error("--force and --check are mutually exclusive")
        if token.exists():
            token.unlink()
            print(f"removed cached token: {token}")
        _consent(args.client_secret, token)
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
        _whoami(creds)
        return 0

    if not token.exists():
        print(f"no cached token at {token}")
        if args.check:
            print("status: NO TOKEN (run without --check to authorize)")
            return 1
        _consent(args.client_secret, token)
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
        _whoami(creds)
        return 0

    creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    print(f"token:        {token}")
    print(f"valid:        {creds.valid}")
    print(f"expired:      {creds.expired}")
    print(f"expiry (UTC): {creds.expiry}")
    print(f"has refresh:  {bool(creds.refresh_token)}")
    print(f"scopes:       {creds.scopes}")

    if creds.valid:
        print("status: VALID")
        _whoami(creds)
        return 0

    if creds.expired and creds.refresh_token:
        print("expired -- attempting silent refresh...")
        try:
            creds.refresh(Request())
        except RefreshError as e:
            print(f"refresh FAILED: {e}")
            if args.check:
                print("status: DEAD (refresh token revoked/expired) -- "
                      "run without --check or with --force to re-consent")
                return 1
            print("falling back to browser consent...")
            token.unlink(missing_ok=True)
            creds = _consent(args.client_secret, token)
            _whoami(creds)
            return 0
        token.write_text(creds.to_json(), encoding="utf-8")
        print(f"refreshed OK; new expiry (UTC): {creds.expiry}")
        print(f"updated token -> {token}")
        _whoami(creds)
        return 0

    # invalid and not refreshable
    print("status: INVALID and no refresh token")
    if args.check:
        return 1
    token.unlink(missing_ok=True)
    creds = _consent(args.client_secret, token)
    _whoami(creds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
