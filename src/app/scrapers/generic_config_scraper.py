import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper, OfferDraft

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; ai-news-aggregator1/0.1; "
    "+https://github.com/) personal-use offer scraper"
)


class GenericConfigScraper(BaseScraper):
    """Scrapes a listing page using CSS selectors from Source.scrape_config.

    Expected scrape_config keys: list_selector, title_selector, url_selector,
    discount_selector (optional), base_url (optional, for resolving relative
    links). If a site exposes data on the list item itself (e.g. a custom
    element with data-* attributes) rather than nested markup, url_attr /
    discount_attr can name an attribute on the list item to read instead of
    using url_selector / discount_selector.
    """

    def fetch(self) -> str:
        response = requests.get(
            self.source.website_url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
        return response.text

    def parse(self, html: str) -> list[OfferDraft]:
        config = self.source.scrape_config or {}
        list_selector = config.get("list_selector")
        if not list_selector:
            logger.warning(
                "source %s has no scrape_config.list_selector, skipping",
                self.source.name,
            )
            return []

        base_url = config.get("base_url") or self.source.website_url
        soup = BeautifulSoup(html, "html.parser")

        drafts: list[OfferDraft] = []
        for item in soup.select(list_selector):
            try:
                draft = self._parse_item(item, config, base_url)
            except Exception:
                logger.exception(
                    "failed to parse listing item for source %s", self.source.name
                )
                continue
            if draft is not None:
                drafts.append(draft)
        return drafts

    def _parse_item(self, item, config: dict, base_url: str) -> OfferDraft | None:
        title_el = item.select_one(config.get("title_selector", ""))
        if title_el is None:
            return None
        title = _extract_text(title_el)
        if not title:
            return None

        url = None
        if config.get("url_attr") and item.get(config["url_attr"]):
            url = urljoin(base_url, item[config["url_attr"]])
        else:
            url_el = item.select_one(config.get("url_selector", ""))
            if url_el is not None and url_el.get("href"):
                url = urljoin(base_url, url_el["href"])

        discount_text = None
        if config.get("discount_attr") and item.get(config["discount_attr"]):
            discount_text = _format_discount_attr_value(item[config["discount_attr"]])
        elif config.get("discount_selector"):
            discount_el = item.select_one(config["discount_selector"])
            if discount_el is not None:
                discount_text = _extract_text(discount_el)

        return OfferDraft(title=title, url=url, discount_text=discount_text)


def _format_discount_attr_value(value: str) -> str:
    """Sites often expose a raw data-*-price attribute (e.g. "18.0") with no
    discount semantics at all -- there's no original/compare-at price on the
    page to compute a real percentage from. Left as a bare number, an LLM
    reading a field named discount_text tends to hallucinate "18% off".
    Formatting it as a price ("$18.0") makes clear it's just the listed
    price, not a discount amount, without inventing data we don't have."""
    stripped = value.strip()
    if stripped.replace(".", "", 1).isdigit():
        return f"${stripped} (listed price, not a discount amount)"
    return stripped


def _extract_text(el) -> str:
    """Like el.get_text(strip=True), but also covers text sitting inside a
    <template> tag (e.g. Vue SSR markup) -- BeautifulSoup's get_text() skips
    that by design since browsers don't render <template> content either,
    but for scraping purposes the text is still the data we want."""
    text = el.get_text(strip=True)
    if text:
        return text
    return "".join(str(c) for c in el.contents).strip()
