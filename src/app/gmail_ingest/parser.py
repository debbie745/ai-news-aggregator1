import base64
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime


@dataclass
class ParsedEmail:
    gmail_message_id: str
    sender: str
    subject: str | None
    snippet: str | None
    received_at: datetime | None
    raw_body_text: str | None


def parse_message(message: dict) -> ParsedEmail:
    payload = message.get("payload", {})
    headers = {
        h["name"].lower(): h["value"] for h in payload.get("headers", [])
    }

    received_at = None
    date_header = headers.get("date")
    if date_header:
        try:
            received_at = parsedate_to_datetime(date_header)
        except (TypeError, ValueError):
            received_at = None

    return ParsedEmail(
        gmail_message_id=message["id"],
        sender=headers.get("from", ""),
        subject=headers.get("subject"),
        snippet=message.get("snippet"),
        received_at=received_at,
        raw_body_text=_extract_plain_text(payload),
    )


def _extract_plain_text(payload: dict) -> str | None:
    if payload.get("mimeType") == "text/plain":
        return _decode_body(payload.get("body", {}))

    for part in payload.get("parts", []) or []:
        text = _extract_plain_text(part)
        if text:
            return text

    return None


def _decode_body(body: dict) -> str | None:
    data = body.get("data")
    if not data:
        return None
    try:
        return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")
    except Exception:
        return None
