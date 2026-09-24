import json
import logging

from openai import OpenAI
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

MODEL = "openai/gpt-oss-120b"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class DigestItemSummary(BaseModel):
    offer_id: int
    summary_text: str


class DigestSummaries(BaseModel):
    items: list[DigestItemSummary]


def summarize_offers(system_prompt: str, offers: list[dict]) -> list[DigestItemSummary]:
    """Summarizes offers into digest snippets via Groq (Llama 3.3 70B).

    Each offer dict should have: id, source_name, category, title,
    discount_text, snippet. Returns [] if the model call fails or returns
    something unparseable -- callers should treat that as "no LLM summaries
    this run" rather than crash the pipeline.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL)

    offers_text = json.dumps(offers, indent=2, default=str)
    user_prompt = (
        f"Offers discovered in the last 24 hours:\n\n{offers_text}\n\n"
        "Respond with JSON only, no prose: an object shaped as "
        '{"items": [{"offer_id": <int>, "summary_text": "<string>"}, ...]}.'
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        data = json.loads(raw)
        return DigestSummaries.model_validate(data).items
    except Exception:
        logger.exception("LLM digest summarization failed")
        return []
