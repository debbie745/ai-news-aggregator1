from app.db.models import Source


def match_source(sender: str, sources: list[Source]) -> Source | None:
    """Matches a message's From header against each Source's
    gmail_sender_pattern via case-insensitive substring match."""
    sender_lower = sender.lower()
    for source in sources:
        pattern = source.gmail_sender_pattern
        if pattern and pattern.lower() in sender_lower:
            return source
    return None
