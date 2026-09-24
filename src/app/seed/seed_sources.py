from sqlalchemy import select

from app.db.models import Source
from app.db.session import session_scope
from app.seed.sources_seed import SOURCES


def seed_sources() -> None:
    with session_scope() as session:
        for entry in SOURCES:
            existing = session.scalar(select(Source).where(Source.name == entry["name"]))
            if existing is None:
                session.add(Source(**entry))
                print(f"created: {entry['name']}")
                continue

            for key, value in entry.items():
                setattr(existing, key, value)
            print(f"updated: {entry['name']}")


if __name__ == "__main__":
    seed_sources()
