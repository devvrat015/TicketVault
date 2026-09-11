from datetime import datetime

from unittest.mock import patch

from app.core.security import hash_password
from app.models.user import User
from app.models.venue import Venue
from app.models.event import Event
from app.models.seat import Seat
from app.models.enums import SeatStatus
from app.models.enums import SeatStatus, UserRole

def test_create_checkout_session_with_mock_stripe(client, db_session):
    # Create organizer
    organizer = User(
    email="stripe-organizer@example.com",
    hashed_password=hash_password("test-password"),
    role=UserRole.ORGANIZER,
    )

    db_session.add(organizer)
    db_session.commit()
    db_session.refresh(organizer)

    # Create venue
    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="Test Address",
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Create event
    event = Event(
        title="Test Event",
        description="Test event for Stripe mocking",
        event_date=datetime(2030, 1, 1),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    # Create held seat
    seat = Seat(
        row_label="A",
        seat_number=1,
        price=500,
        status=SeatStatus.HELD,
        event_id=event.id,
    )

    db_session.add(seat)
    db_session.commit()
    db_session.refresh(seat)

    # Login as organizer
    login_response = client.post(
        "/auth/login",
        data={
            "username": "stripe-organizer@example.com",
            "password": "test-password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    # Mock Stripe checkout session
    mock_session = type(
        "MockStripeSession",
        (),
        {
            "url": "https://checkout.stripe.com/test-session"
        },
    )()

    with patch(
        "app.api.payments.create_checkout_session",
        return_value=mock_session,
    ) as mock_create_checkout, patch(
        "app.api.payments.check_and_store_idempotency",
        return_value=(False, None),
    ), patch(
        "app.api.payments.store_idempotent_result",
        return_value=None,
    ):

        response = client.post(
            f"/payments/checkout/{seat.id}",
            headers={
                "Idempotency-Key": "stripe-test-key-123",
                "Authorization": f"Bearer {access_token}",
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["checkout_url"] == "https://checkout.stripe.com/test-session"

    mock_create_checkout.assert_called_once()