import logging

from sqlalchemy import select

from app.db.models import Offer, Source
from app.db.session import session_scope
from app.scrapers.dedupe import compute_dedupe_key
from app.scrapers.generic_config_scraper import GenericConfigScraper

logger = logging.getLogger(__name__)


def run_scrapers() -> int:
    """Scrape all active sources and insert new offers. Returns count inserted."""
    inserted = 0

    with session_scope() as session:
        source_ids = list(
            session.scalars(select(Source.id).where(Source.is_active.is_(True))).all()
        )

    for source_id in source_ids:
        try:
            with session_scope() as session:
                source = session.get(Source, source_id)
                drafts = GenericConfigScraper(source).run()

                for draft in drafts:
                    dedupe_key = compute_dedupe_key(source.id, draft.url, draft.title)
                    existing = session.scalar(
                        select(Offer).where(Offer.dedupe_key == dedupe_key)
                    )
                    if existing is not None:
                        continue

                    session.add(
                        Offer(
                            source_id=source.id,
                            origin="scrape",
                            title=draft.title,
                            url=draft.url,
                            snippet=draft.snippet,
                            discount_text=draft.discount_text,
                            item_type=draft.item_type,
                            dedupe_key=dedupe_key,
                        )
                    )
                    inserted += 1
        except Exception:
            logger.exception("scrape failed for source_id %s", source_id)

    return inserted


if __name__ == "__main__":
    from app.util.logging import setup_logging

    setup_logging()
    count = run_scrapers()
    print(f"Inserted {count} new offers.")
