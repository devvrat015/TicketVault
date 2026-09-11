from datetime import datetime, timedelta

from sqlalchemy import text


def test_create_event_success(client, db_session):
    from app.models.user import User
    from app.models.venue import Venue
    from app.models.seat import Seat
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
        email="event-organizer@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "event-organizer@example.com",
            "password": "password123",
        },
    )
    access_token = response.json()["access_token"]

    response = client.post(
        "/events/",
        json={
            "title": "Test Concert",
            "description": "A test event",
            "event_date": "2027-01-15T18:00:00",
            "venue_id": venue.id,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Test Concert"
    assert data["description"] == "A test event"
    assert data["venue"]["id"] == venue.id

    seats = (
        db_session.query(Seat)
        .filter_by(event_id=data["id"])
        .all()
    )

    assert len(seats) == 50


def test_create_event_venue_not_found(client, db_session):
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    organizer = User(
        email="event-organizer-404@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "event-organizer-404@example.com",
            "password": "password123",
        },
    )
    access_token = response.json()["access_token"]

    response = client.post(
        "/events/",
        json={
            "title": "Test Concert",
            "description": "A test event",
            "event_date": "2027-01-15T18:00:00",
            "venue_id": 99999,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Venue not found"


def test_get_all_events_pagination_and_cache(
    client,
    db_session,
    monkeypatch,
):
    from app.api import events
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Pagination Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="pagination@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    for i in range(3):
        event = Event(
            title=f"Event {i + 1}",
            description="Pagination test",
            event_date=datetime(2027, 1, 15, 18, 0)
            + timedelta(days=i),
            venue_id=venue.id,
            organizer_id=organizer.id,
        )
        db_session.add(event)

    db_session.commit()

    response = client.get("/events/?page=2&limit=2")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Event 3"
    assert data[0]["venue"]["id"] == venue.id

    cached_events = [
        {
            "id": 1,
            "title": "Cached Event",
            "description": "Cached event description",
            "event_date": "2027-01-15T18:00:00",
            "venue": {
                "id": 1,
                "name": "Cached Venue",
                "city": "Mumbai",
                "address": "123 Test Street",
            },
            "version": 1,
        }
    ]

    monkeypatch.setattr(
        events,
        "get_cache",
        lambda key: cached_events,
    )

    response = client.get("/events/")

    assert response.status_code == 200
    assert response.json() == cached_events


def test_get_event_success_not_found_and_cache(
    client,
    db_session,
    monkeypatch,
):
    from app.api import events
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Get Event Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="get-event@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Get Event Test",
        description="Testing single event retrieval",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    response = client.get(f"/events/{event.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == event.id
    assert data["title"] == "Get Event Test"
    assert data["venue"]["id"] == venue.id

    response = client.get("/events/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"

    cached_event = {
        "id": 1,
        "title": "Cached Event",
        "description": "Cached event description",
        "event_date": "2027-01-15T18:00:00",
        "venue": {
            "id": 1,
            "name": "Cached Venue",
            "city": "Mumbai",
            "address": "123 Test Street",
        },
        "version": 1,
    }

    monkeypatch.setattr(
        events,
        "get_cache",
        lambda key: cached_event,
    )

    response = client.get("/events/1")

    assert response.status_code == 200
    assert response.json() == cached_event


def test_search_events_basic_and_city_filter(
    client,
    db_session,
):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Search Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="search-basic@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Search Test Event",
        description="Testing search",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    response = client.get("/events/search")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Search Test Event"

    response = client.get("/events/search?city=mumbai")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Search Test Event"


def test_search_events_by_query(client, db_session):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Search Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="search-query@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Python Conference",
        description="Backend and Python development event",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    db_session.execute(
        text(
            """
            UPDATE events
            SET search_vector =
                to_tsvector(
                    'english',
                    coalesce(title, '') || ' ' || coalesce(description, '')
                )
            WHERE id = :event_id
            """
        ),
        {"event_id": event.id},
    )
    db_session.commit()

    response = client.get("/events/search?q=Python")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Python Conference"


def test_search_events_combined_filters_and_pagination(
    client,
    db_session,
):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    mumbai_venue = Venue(
        name="Mumbai Venue",
        city="Mumbai",
        address="123 Mumbai Street",
    )
    pune_venue = Venue(
        name="Pune Venue",
        city="Pune",
        address="123 Pune Street",
    )

    db_session.add_all([mumbai_venue, pune_venue])
    db_session.commit()

    organizer = User(
        email="search-combined@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    matching_event = Event(
        title="Python Mumbai Conference",
        description="Python backend conference",
        event_date=datetime(2027, 2, 15, 18, 0),
        venue_id=mumbai_venue.id,
        organizer_id=organizer.id,
    )

    wrong_city = Event(
        title="Python Pune Conference",
        description="Python backend conference",
        event_date=datetime(2027, 2, 15, 18, 0),
        venue_id=pune_venue.id,
        organizer_id=organizer.id,
    )

    wrong_date = Event(
        title="Python Mumbai Old Conference",
        description="Python backend conference",
        event_date=datetime(2027, 4, 15, 18, 0),
        venue_id=mumbai_venue.id,
        organizer_id=organizer.id,
    )

    pagination_event = Event(
        title="Python Mumbai Second Conference",
        description="Python backend conference",
        event_date=datetime(2027, 2, 20, 18, 0),
        venue_id=mumbai_venue.id,
        organizer_id=organizer.id,
    )

    db_session.add_all(
        [
            matching_event,
            wrong_city,
            wrong_date,
            pagination_event,
        ]
    )
    db_session.commit()

    db_session.execute(
        text(
            """
            UPDATE events
            SET search_vector =
                to_tsvector(
                    'english',
                    coalesce(title, '') || ' ' || coalesce(description, '')
                )
            """
        )
    )
    db_session.commit()

    response = client.get(
        "/events/search"
        "?q=Python"
        "&city=mumbai"
        "&date_from=2027-02-01"
        "&date_to=2027-02-28"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Python Mumbai Conference"

    response = client.get(
        "/events/search"
        "?q=Python"
        "&city=mumbai"
        "&date_from=2027-02-01"
        "&date_to=2027-02-28"
        "&page=2"
        "&page_size=1"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert data["page"] == 2
    assert data["page_size"] == 1
    assert data["total_pages"] == 2
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == (
        "Python Mumbai Second Conference"
    )


def test_update_event_success_and_admin_success(
    client,
    db_session,
):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Update Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="update-event@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )

    admin = User(
        email="admin-update@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ADMIN,
    )

    db_session.add_all([organizer, admin])
    db_session.commit()

    event = Event(
        title="Original Event",
        description="Original description",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "update-event@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]

    response = client.put(
        f"/events/{event.id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Updated Event",
            "description": "Updated description",
            "event_date": "2027-02-15T18:00:00",
            "venue_id": venue.id,
            "version": 0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated Event"
    assert data["description"] == "Updated description"
    assert data["version"] == 1

    login_response = client.post(
        "/auth/login",
        data={
            "username": "admin-update@example.com",
            "password": "password123",
        },
    )
    admin_token = login_response.json()["access_token"]

    response = client.put(
        f"/events/{event.id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "title": "Admin Updated Event",
            "description": "Updated by admin",
            "event_date": "2027-03-15T18:00:00",
            "venue_id": venue.id,
            "version": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Admin Updated Event"
    assert data["description"] == "Updated by admin"
    assert data["version"] == 2


def test_update_event_conflict_and_forbidden(
    client,
    db_session,
):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Ownership Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    owner = User(
        email="event-owner@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )

    other_organizer = User(
        email="other-organizer@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )

    db_session.add_all([owner, other_organizer])
    db_session.commit()

    event = Event(
        title="Owner's Event",
        description="Ownership test",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=owner.id,
    )
    db_session.add(event)
    db_session.commit()

    owner_login = client.post(
        "/auth/login",
        data={
            "username": "event-owner@example.com",
            "password": "password123",
        },
    )
    owner_token = owner_login.json()["access_token"]

    response = client.put(
        f"/events/{event.id}",
        headers={
            "Authorization": f"Bearer {owner_token}"
        },
        json={
            "title": "Updated Event",
            "description": "Updated description",
            "event_date": "2027-02-15T18:00:00",
            "venue_id": venue.id,
            "version": 999,
        },
    )

    assert response.status_code == 409
    assert "modified by someone else" in response.json()["detail"]

    other_login = client.post(
        "/auth/login",
        data={
            "username": "other-organizer@example.com",
            "password": "password123",
        },
    )
    other_token = other_login.json()["access_token"]

    response = client.put(
        f"/events/{event.id}",
        headers={
            "Authorization": f"Bearer {other_token}"
        },
        json={
            "title": "Unauthorized Update",
            "description": "Should not update",
            "event_date": "2027-02-15T18:00:00",
            "venue_id": venue.id,
            "version": 0,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You can only update your own events"
    )


def test_delete_event_success(client, db_session):
    from app.models.event import Event
    from app.models.venue import Venue
    from app.models.user import User
    from app.models.enums import UserRole
    from app.core.security import hash_password

    venue = Venue(
        name="Delete Venue",
        city="Mumbai",
        address="123 Test Street",
    )
    db_session.add(venue)
    db_session.commit()

    organizer = User(
        email="delete-event@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.ORGANIZER,
    )
    db_session.add(organizer)
    db_session.commit()

    event = Event(
        title="Event To Delete",
        description="Delete test",
        event_date=datetime(2027, 1, 15, 18, 0),
        venue_id=venue.id,
        organizer_id=organizer.id,
    )
    db_session.add(event)
    db_session.commit()

    event_id = event.id

    login_response = client.post(
        "/auth/login",
        data={
            "username": "delete-event@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]

    response = client.delete(
        f"/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204

    deleted_event = (
        db_session.query(Event)
        .filter(Event.id == event_id)
        .first()
    )

    assert deleted_event is None