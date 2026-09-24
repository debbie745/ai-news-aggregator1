import hashlib


def compute_dedupe_key(source_id: int, url: str | None, title: str) -> str:
    normalized_url = (url or "").strip().lower()
    normalized_title = title.strip().lower()
    raw = f"{source_id}|{normalized_url}|{normalized_title}"
    return hashlib.sha256(raw.encode()).hexdigest()
