from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class SeatStatus(str, Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"