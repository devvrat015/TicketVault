from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.venue import Venue
    from app.models.seat import Seat
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    event_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id"),
        nullable=False
    )

    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    venue: Mapped["Venue"] = relationship(
        "Venue",
        back_populates="events"
    )

    organizer: Mapped["User"] = relationship(
        "User",
        back_populates="events"
    )

    seats: Mapped[list["Seat"]] = relationship(
        "Seat",
        back_populates="event",
        cascade="all, delete-orphan"
    )