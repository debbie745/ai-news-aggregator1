from app.db.base import Base
from app.db.models import Digest, DigestItem, EmailMessage, Offer, Source  # noqa: F401
from app.db.session import get_engine


def create_tables() -> None:
    Base.metadata.create_all(get_engine())


if __name__ == "__main__":
    create_tables()
    print("Tables created.")
