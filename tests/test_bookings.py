import threading


from app.models.user import User
from app.models.enums import UserRole
from app.models.venue import Venue
from app.models.seat import Seat



def test_user_can_book_available_seat(client, db_session):
    # Create organizer
    client.post(
        "/auth/register",
        json={
            "email": "bookingorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer = db_session.query(User).filter(
        User.email == "bookingorganizer@example.com"
    ).first()

    organizer.role = UserRole.ORGANIZER
    db_session.commit()

    # Create venue
    venue = Venue(
        name="Booking Test Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Login organizer
    login_response = client.post(
        "/auth/login",
        data={
            "username": "bookingorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer_token = login_response.json()["access_token"]

    # Create event
    event_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json={
            "title": "Booking Test Event",
            "description": "Event for booking test",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert event_response.status_code == 201

    event = event_response.json()

    # Get one of the generated seats
    seat = db_session.query(Seat).filter(
        Seat.event_id == event["id"]
    ).first()

    # Create normal user
    client.post(
        "/auth/register",
        json={
            "email": "bookinguser@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "bookinguser@example.com",
            "password": "secret123"
        }
    )

    user_token = login_response.json()["access_token"]

    # Book the available seat
    response = client.post(
        f"/bookings/{event['id']}/book-seat/{seat.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] > 0
    assert data["event_id"] == event["id"]
    assert data["total_amount"] == "500.00"
    assert data["status"] == "confirmed"


# Prevent double booking test
def test_prevent_double_booking(client, db_session):
    # Create organizer
    client.post(
        "/auth/register",
        json={
            "email": "concurrencyorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer = db_session.query(User).filter(
        User.email == "concurrencyorganizer@example.com"
    ).first()

    organizer.role = UserRole.ORGANIZER
    db_session.commit()

    # Create venue
    venue = Venue(
        name="Concurrency Test Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Login organizer
    login_response = client.post(
        "/auth/login",
        data={
            "username": "concurrencyorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer_token = login_response.json()["access_token"]

    # Create event
    event_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json={
            "title": "Concurrency Test Event",
            "description": "Event for double booking test",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert event_response.status_code == 201

    event = event_response.json()

    # Get one available seat
    seat = db_session.query(Seat).filter(
        Seat.event_id == event["id"]
    ).first()

    # Create first user
    client.post(
        "/auth/register",
        json={
            "email": "bookinguser1@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "bookinguser1@example.com",
            "password": "secret123"
        }
    )

    token1 = login_response.json()["access_token"]

    # Create second user
    client.post(
        "/auth/register",
        json={
            "email": "bookinguser2@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "bookinguser2@example.com",
            "password": "secret123"
        }
    )

    token2 = login_response.json()["access_token"]

    # First user books the seat
    response1 = client.post(
        f"/bookings/{event['id']}/book-seat/{seat.id}",
        headers={"Authorization": f"Bearer {token1}"}
    )

    # Second user tries to book the same seat
    response2 = client.post(
        f"/bookings/{event['id']}/book-seat/{seat.id}",
        headers={"Authorization": f"Bearer {token2}"}
    )

    # Exactly one booking should succeed
    assert response1.status_code == 200
    assert response2.status_code == 400

    assert response2.json()["detail"] == "Seat not available"




# Actual concurrent booking test
def test_concurrent_booking_same_seat(client, concurrency_client, db_session):
    # Create organizer
    client.post(
        "/auth/register",
        json={
            "email": "concurrentorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer = db_session.query(User).filter(
        User.email == "concurrentorganizer@example.com"
    ).first()

    organizer.role = UserRole.ORGANIZER
    db_session.commit()

    # Create venue
    venue = Venue(
        name="Concurrent Booking Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Login organizer
    login_response = client.post(
        "/auth/login",
        data={
            "username": "concurrentorganizer@example.com",
            "password": "secret123"
        }
    )

    organizer_token = login_response.json()["access_token"]

    # Create event
    event_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {organizer_token}"},
        json={
            "title": "Concurrent Booking Event",
            "description": "Event for concurrency test",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert event_response.status_code == 201

    event = event_response.json()

    # Get one available seat
    seat = db_session.query(Seat).filter(
        Seat.event_id == event["id"]
    ).first()

    # Create first user
    client.post(
        "/auth/register",
        json={
            "email": "concurrentuser1@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "concurrentuser1@example.com",
            "password": "secret123"
        }
    )

    token1 = login_response.json()["access_token"]

    # Create second user
    client.post(
        "/auth/register",
        json={
            "email": "concurrentuser2@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "concurrentuser2@example.com",
            "password": "secret123"
        }
    )

    token2 = login_response.json()["access_token"]

    # Store both responses
    responses = []

    # Function executed by each thread
    def book_seat(token):
        response = concurrency_client.post(
            f"/bookings/{event['id']}/book-seat/{seat.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        responses.append(response)

    # Create two simultaneous booking requests
    thread1 = threading.Thread(target=book_seat, args=(token1,))
    thread2 = threading.Thread(target=book_seat, args=(token2,))

    # Start both requests
    thread1.start()
    thread2.start()

    # Wait for both requests to finish
    thread1.join()
    thread2.join()

    # Exactly one request should succeed

    status_codes = sorted(response.status_code for response in responses)

    assert status_codes == [200, 400]

from datetime import datetime
def test_hold_seat_success(db_session):
    from app.models.event import Event
    from app.models.seat import Seat
    from app.models.venue import Venue
    from app.models.enums import SeatStatus
    from app.services.hold_service import hold_seat
    from unittest.mock import Mock
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password
    
    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
    email="hold-test-organizer@example.com",
    hashed_password=hash_password("password123"),
    role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Test Event",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 15, 18, 0),
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    seat = Seat(
        event_id=event.id,
        row_label="A",
        seat_number=1,
        price=500,
        status=SeatStatus.AVAILABLE,
    )
    db_session.add(seat)
    db_session.commit()

    mock_redis = Mock()

    result = hold_seat(
        db=db_session,
        redis_client=mock_redis,
        user_id=1,
        event_id=event.id,
        seat_id=seat.id,
    )

    assert result["seat_id"] == seat.id
    assert result["user_id"] == 1
    assert result["status"] == SeatStatus.HELD
    assert result["expires_in"] == 300

    db_session.refresh(seat)
    assert seat.status == SeatStatus.HELD

    mock_redis.setex.assert_called_once_with(
        f"seat_hold:{seat.id}",
        300,
        "1",
    )


def test_hold_seat_event_not_found(db_session):
    from app.services.hold_service import hold_seat
    from app.core.exceptions import EventNotFoundError
    from unittest.mock import Mock
    import pytest

    with pytest.raises(EventNotFoundError):
        hold_seat(
            db=db_session,
            redis_client=Mock(),
            user_id=1,
            event_id=99999,
            seat_id=99999,
        )


def test_hold_seat_not_found(db_session):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password
    from app.services.hold_service import hold_seat
    from app.core.exceptions import SeatNotFoundError
    from unittest.mock import Mock
    from datetime import datetime
    import pytest

    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="seat-not-found@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Test Event",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 15, 18, 0),
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    with pytest.raises(SeatNotFoundError):
        hold_seat(
            db=db_session,
            redis_client=Mock(),
            user_id=1,
            event_id=event.id,
            seat_id=99999,
        )


def test_hold_seat_event_mismatch(db_session):
    from app.models.event import Event
    from app.models.seat import Seat
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import SeatStatus, UserRole
    from app.core.security import hash_password
    from app.services.hold_service import hold_seat
    from app.core.exceptions import SeatEventMismatchError
    from unittest.mock import Mock
    from datetime import datetime
    import pytest

    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="mismatch-test@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event1 = Event(
        title="Event One",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 15, 18, 0),
        organizer_id=organizer.id,
    )

    event2 = Event(
        title="Event Two",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 16, 18, 0),
        organizer_id=organizer.id,
    )

    db_session.add_all([event1, event2])
    db_session.commit()

    seat = Seat(
        event_id=event1.id,
        row_label="A",
        seat_number=1,
        price=500,
        status=SeatStatus.AVAILABLE,
    )
    db_session.add(seat)
    db_session.commit()

    with pytest.raises(SeatEventMismatchError):
        hold_seat(
            db=db_session,
            redis_client=Mock(),
            user_id=1,
            event_id=event2.id,
            seat_id=seat.id,
        )


def test_hold_seat_not_available(db_session):
    from app.models.event import Event
    from app.models.seat import Seat
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import SeatStatus, UserRole
    from app.core.security import hash_password
    from app.services.hold_service import hold_seat
    from app.core.exceptions import SeatNotAvailableError
    from unittest.mock import Mock
    from datetime import datetime
    import pytest

    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="unavailable-test@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Test Event",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 15, 18, 0),
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    seat = Seat(
        event_id=event.id,
        row_label="A",
        seat_number=1,
        price=500,
        status=SeatStatus.HELD,
    )
    db_session.add(seat)
    db_session.commit()

    with pytest.raises(SeatNotAvailableError):
        hold_seat(
            db=db_session,
            redis_client=Mock(),
            user_id=1,
            event_id=event.id,
            seat_id=seat.id,
        )


def test_hold_seat_redis_failure_rolls_back(db_session):
    from app.models.event import Event
    from app.models.seat import Seat
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import SeatStatus, UserRole
    from app.core.security import hash_password
    from app.services.hold_service import hold_seat
    from unittest.mock import Mock
    from datetime import datetime
    import pytest

    venue = Venue(
        name="Test Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="redis-failure@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Test Event",
        venue_id=venue.id,
        description="testing event",
        event_date=datetime(2027, 1, 15, 18, 0),
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    seat = Seat(
        event_id=event.id,
        row_label="A",
        seat_number=1,
        price=500,
        status=SeatStatus.AVAILABLE,
    )
    db_session.add(seat)
    db_session.commit()

    redis_mock = Mock()
    redis_mock.setex.side_effect = Exception("Redis failure")

    with pytest.raises(Exception, match="Redis failure"):
        hold_seat(
            db=db_session,
            redis_client=redis_mock,
            user_id=1,
            event_id=event.id,
            seat_id=seat.id,
        )

    db_session.refresh(seat)

    assert seat.status == SeatStatus.AVAILABLE