import logging

from app.config import get_settings
from app.db.create_tables import create_tables
from app.digest.builder import build_digest
from app.digest.mailer import send_digest_email
from app.gmail_ingest.run_ingest import run_gmail_ingestion
from app.scrapers.run_all import run_scrapers
from app.seed.seed_sources import seed_sources
from app.util.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    settings = get_settings()

    try:
        create_tables()
        seed_sources()
    except Exception:
        logger.exception("DB init/seed phase failed")

    try:
        inserted = run_scrapers()
        logger.info("Scraping done: %d new offers", inserted)
    except Exception:
        logger.exception("Scraping phase failed")

    if settings.enable_gmail_ingestion:
        try:
            inserted = run_gmail_ingestion()
            logger.info("Gmail ingestion done: %d new offers", inserted)
        except Exception:
            logger.exception("Gmail ingestion phase failed")
    else:
        logger.info("Gmail ingestion disabled (ENABLE_GMAIL_INGESTION=false)")

    digest_id = None
    try:
        digest_id = build_digest()
        logger.info("Digest build done: id=%s", digest_id)
    except Exception:
        logger.exception("Digest build phase failed")

    if digest_id is not None:
        try:
            sent = send_digest_email(digest_id)
            logger.info("Digest email sent: %s", sent)
        except Exception:
            logger.exception("Digest email phase failed")


if __name__ == "__main__":
    main()
