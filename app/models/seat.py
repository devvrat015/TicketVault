from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.event import Event
from app.models.enums import SeatStatus
from app.core.database import Base


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(primary_key=True)

    row_label: Mapped[str] = mapped_column(
        String(5),
        nullable=False
    )

    seat_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    price: Mapped[int] = mapped_column(
        Integer,
        default=500
    )

    status: Mapped[SeatStatus] = mapped_column(
        SQLEnum(
            SeatStatus,
            values_callable=lambda enum: [e.value for e in enum],
            name="seatstatus",
        ),
        default=SeatStatus.AVAILABLE,
        nullable=False,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id"),
        nullable=False
    )

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="seats"
    )