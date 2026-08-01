"""
Custom exceptions for the application's business logic.

These exceptions are raised by the service layer and translated
into appropriate HTTP responses by the API layer.
"""


class SeatNotFoundError(Exception):
    """Raised when the requested seat does not exist."""
    pass


class SeatNotAvailableError(Exception):
    """Raised when a seat cannot be booked because it is not available."""
    pass

class EventNotFoundError(Exception):
    pass


class SeatEventMismatchError(Exception):
    pass