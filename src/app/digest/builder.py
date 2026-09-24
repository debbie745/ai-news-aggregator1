import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Digest, DigestItem, Offer
from app.db.session import session_scope
from app.llm.groq_client import summarize_offers

logger = logging.getLogger(__name__)


def build_digest() -> int:
    """Builds (or reuses) today's digest from the last 24h of offers.

    Returns the Digest id. If a digest for today already exists, it's
    reused as-is (not rebuilt) rather than duplicated.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    window_start = now - timedelta(hours=24)
    today = now.date()

    with session_scope() as session:
        existing = session.scalar(select(Digest).where(Digest.digest_date == today))
        if existing is not None:
            logger.info("Digest for %s already exists (id=%s), reusing it", today, existing.id)
            return existing.id

        offers = list(
            session.scalars(
                select(Offer).where(Offer.discovered_at.between(window_start, now))
            ).all()
        )

        digest = Digest(digest_date=today, window_start=window_start, window_end=now)
        session.add(digest)
        session.flush()  # populate digest.id

        summaries = []
        if offers and settings.groq_api_key:
            system_prompt = _load_system_prompt(settings.system_prompt_path)
            payload = [
                {
                    "id": offer.id,
                    "source_name": offer.source.name,
                    "category": offer.source.category,
                    "title": offer.title,
                    "discount_text": offer.discount_text,
                    "snippet": offer.snippet,
                }
                for offer in offers
            ]
            summaries = summarize_offers(system_prompt, payload)

        offers_by_id = {offer.id: offer for offer in offers}

        if summaries:
            for summary in summaries:
                offer = offers_by_id.get(summary.offer_id)
                if offer is None:
                    continue
                session.add(
                    DigestItem(
                        digest_id=digest.id,
                        offer_id=offer.id,
                        summary_text=summary.summary_text,
                        link=offer.url,
                    )
                )
        else:
            # No LLM key, or the LLM call produced nothing usable -- fall
            # back to a trivial deterministic summary per offer so the
            # digest still has content.
            for offer in offers:
                summary_text = offer.title
                if offer.discount_text:
                    summary_text += f" — {offer.discount_text}"
                session.add(
                    DigestItem(
                        digest_id=digest.id,
                        offer_id=offer.id,
                        summary_text=summary_text,
                        link=offer.url,
                    )
                )

        logger.info(
            "Built digest %s for %s with %d offers", digest.id, today, len(offers)
        )
        return digest.id


def _load_system_prompt(path: str) -> str:
    with open(path) as f:
        return f.read()


if __name__ == "__main__":
    from app.util.logging import setup_logging

    setup_logging()
    digest_id = build_digest()
    print(f"Digest id: {digest_id}")
