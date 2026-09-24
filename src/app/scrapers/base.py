from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.db.models import Source


@dataclass
class OfferDraft:
    title: str
    url: str | None = None
    snippet: str | None = None
    discount_text: str | None = None
    item_type: str | None = None


class BaseScraper(ABC):
    def __init__(self, source: Source):
        self.source = source

    @abstractmethod
    def fetch(self) -> str:
        """Return the raw HTML for the source's listing page."""

    @abstractmethod
    def parse(self, html: str) -> list[OfferDraft]:
        """Parse raw HTML into a list of offer drafts."""

    def run(self) -> list[OfferDraft]:
        return self.parse(self.fetch())
