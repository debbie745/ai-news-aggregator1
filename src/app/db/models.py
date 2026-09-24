from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Source(Base):
    __tablename__ = "source"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    category: Mapped[str] = mapped_column()
    website_url: Mapped[str] = mapped_column()
    scrape_config: Mapped[dict | None] = mapped_column(JSONB, default=None)
    gmail_sender_pattern: Mapped[str | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    offers: Mapped[list["Offer"]] = relationship(back_populates="source")


class EmailMessage(Base):
    __tablename__ = "email_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(unique=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"))
    sender: Mapped[str] = mapped_column()
    subject: Mapped[str | None] = mapped_column(default=None)
    snippet: Mapped[str | None] = mapped_column(Text, default=None)
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    raw_body_text: Mapped[str | None] = mapped_column(Text, default=None)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source | None"] = relationship()
    offer: Mapped["Offer | None"] = relationship(back_populates="email_message")


class Offer(Base):
    __tablename__ = "offer"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), index=True)
    email_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_message.id"), default=None
    )
    origin: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    url: Mapped[str | None] = mapped_column(default=None)
    snippet: Mapped[str | None] = mapped_column(Text, default=None)
    discount_text: Mapped[str | None] = mapped_column(default=None)
    item_type: Mapped[str | None] = mapped_column(default=None)
    dedupe_key: Mapped[str] = mapped_column(unique=True, index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source"] = relationship(back_populates="offers")
    email_message: Mapped["EmailMessage | None"] = relationship(
        back_populates="offer"
    )
    digest_items: Mapped[list["DigestItem"]] = relationship(back_populates="offer")


class Digest(Base):
    __tablename__ = "digest"

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_date: Mapped[date] = mapped_column(Date, unique=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    items: Mapped[list["DigestItem"]] = relationship(back_populates="digest")


class DigestItem(Base):
    __tablename__ = "digest_item"
    __table_args__ = (UniqueConstraint("digest_id", "offer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digest.id"), index=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offer.id"))
    summary_text: Mapped[str] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    digest: Mapped["Digest"] = relationship(back_populates="items")
    offer: Mapped["Offer"] = relationship(back_populates="digest_items")
