import logging
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage as MimeEmailMessage

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Digest, DigestItem
from app.db.session import session_scope

logger = logging.getLogger(__name__)


def render_digest_text(digest: Digest, items: list[DigestItem]) -> str:
    lines = [f"Daily Offers Digest — {digest.digest_date}", ""]

    if not items:
        lines.append("No new offers in the last 24 hours.")
    else:
        for item in items:
            lines.append(f"- {item.summary_text}")
            if item.link:
                lines.append(f"  {item.link}")
            lines.append("")

    return "\n".join(lines)


def send_digest_email(digest_id: int) -> bool:
    """Renders and sends the digest by id. Returns True if it was sent.

    Skips (logs and returns False) if SMTP credentials aren't configured.
    """
    settings = get_settings()

    with session_scope() as session:
        digest = session.get(Digest, digest_id)
        if digest is None:
            logger.error("No digest with id=%s", digest_id)
            return False

        items = list(
            session.scalars(
                select(DigestItem).where(DigestItem.digest_id == digest_id)
            ).all()
        )
        body = render_digest_text(digest, items)
        digest_date = digest.digest_date

        if not settings.smtp_username or not settings.smtp_password:
            logger.info("Digest built but not sent (SMTP not configured)")
            return False

        if not settings.digest_recipient_email:
            logger.info("Digest built but not sent (no DIGEST_RECIPIENT_EMAIL set)")
            return False

        message = MimeEmailMessage()
        message["From"] = settings.effective_sender_email
        message["To"] = settings.digest_recipient_email
        message["Subject"] = f"Daily Offers Digest - {digest_date}"
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)

        digest.sent_at = datetime.now(UTC)
        logger.info("Sent digest %s to %s", digest_id, settings.digest_recipient_email)
        return True


if __name__ == "__main__":
    import sys

    from app.util.logging import setup_logging

    setup_logging()
    target_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if target_id is None:
        print("Usage: python -m app.digest.mailer <digest_id>")
        raise SystemExit(1)
    sent = send_digest_email(target_id)
    print(f"Sent: {sent}")
