from googleapiclient.discovery import Resource


def list_recent_messages(
    service: Resource, query: str = "newer_than:2d", max_results: int = 100
) -> list[dict]:
    """Returns a list of {"id": ..., "threadId": ...} dicts (no body)."""
    messages: list[dict] = []
    request = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    )
    while request is not None:
        response = request.execute()
        messages.extend(response.get("messages", []))
        request = service.users().messages().list_next(request, response)
    return messages


def get_message(service: Resource, message_id: str) -> dict:
    """Returns the full Gmail message resource (format=full)."""
    return service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
