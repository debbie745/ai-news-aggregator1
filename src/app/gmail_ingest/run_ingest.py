import logging
import os
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import get_settings
from app.db.models import EmailMessage, Offer, Source
from app.db.session import session_scope
from app.gmail_ingest.auth import get_gmail_service
from app.gmail_ingest.client import get_message, list_recent_messages
from app.gmail_ingest.matcher import match_source
from app.gmail_ingest.parser import parse_message
from app.scrapers.dedupe import compute_dedupe_key

logger = logging.getLogger(__name__)


def run_gmail_ingestion() -> int:
    """Ingests recent promo emails into EmailMessage/Offer rows.

    Returns the number of new offers created. Skips (logs and returns 0)
    if Gmail credentials aren't configured yet.
    """
    settings = get_settings()

    if not os.path.exists(settings.gmail_credentials_path):
        logger.info(
            "Gmail ingestion skipped: no credentials at %s",
            settings.gmail_credentials_path,
        )
        return 0

    service = get_gmail_service()
    messages = list_recent_messages(service)

    inserted_offers = 0

    with session_scope() as session:
        sources = list(session.scalars(select(Source).where(Source.is_active.is_(True))).all())

        for ref in messages:
            message_id = ref["id"]
            existing = session.scalar(
                select(EmailMessage).where(EmailMessage.gmail_message_id == message_id)
            )
            if existing is not None:
                continue

            full_message = get_message(service, message_id)
            parsed = parse_message(full_message)

            matched_source = match_source(parsed.sender, sources)

            email_row = EmailMessage(
                gmail_message_id=parsed.gmail_message_id,
                source_id=matched_source.id if matched_source else None,
                sender=parsed.sender,
                subject=parsed.subject,
                snippet=parsed.snippet,
                received_at=parsed.received_at,
                raw_body_text=parsed.raw_body_text,
            )
            session.add(email_row)
            session.flush()  # populate email_row.id

            if matched_source is not None and parsed.subject:
                dedupe_key = compute_dedupe_key(matched_source.id, None, parsed.subject)
                offer_exists = session.scalar(
                    select(Offer).where(Offer.dedupe_key == dedupe_key)
                )
                if offer_exists is None:
                    session.add(
                        Offer(
                            source_id=matched_source.id,
                            email_message_id=email_row.id,
                            origin="email",
                            title=parsed.subject,
                            snippet=parsed.snippet or parsed.raw_body_text,
                            dedupe_key=dedupe_key,
                        )
                    )
                    inserted_offers += 1

            email_row.processed_at = datetime.now(UTC)

    return inserted_offers


if __name__ == "__main__":
    from app.util.logging import setup_logging

    setup_logging()
    count = run_gmail_ingestion()
    print(f"Inserted {count} new offers from email.")
