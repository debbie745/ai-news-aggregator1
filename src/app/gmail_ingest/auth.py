import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from app.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service() -> Resource:
    settings = get_settings()
    creds = _load_or_refresh_credentials(
        settings.gmail_credentials_path, settings.gmail_token_path
    )
    return build("gmail", "v1", credentials=creds)


def _load_or_refresh_credentials(credentials_path: str, token_path: str) -> Credentials:
    creds: Credentials | None = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # One-time interactive step: opens a browser for the user to sign in
        # and grant read-only Gmail access. Cannot run non-interactively.
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)

    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    return creds
