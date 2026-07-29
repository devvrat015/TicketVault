from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BookingStatus




class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False
    )

    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    status: Mapped[BookingStatus] = mapped_column(
    SQLEnum(
        BookingStatus,
        values_callable=lambda obj: [e.value for e in obj],
    ),
    default=BookingStatus.PENDING,
    nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
    seats = relationship("Seat", back_populates="booking")