def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "secret123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data

def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "secret123"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "login@example.com",
            "password": "secret123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]

def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "secret123"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "wrongpass@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_protected_route_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401

def test_protected_route_with_token(client):
    register_response = client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "me@example.com",
            "password": "secret123"
        }
    )

    token = login_response.json()["access_token"]

def test_user_cannot_create_event(client):
    client.post(
        "/auth/register",
        json={
            "email": "normaluser@example.com",
            "password": "secret123"
        }
    )

    login_response = client.post(
        "/auth/login",
        data={
            "username": "normaluser@example.com",
            "password": "secret123"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Unauthorized Event",
            "description": "Should not be created",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": 1
        }
    )

    assert response.status_code == 403

from app.models.user import User
from app.models.enums import UserRole
from app.models.venue import Venue

def test_organizer_can_create_event(client, db_session):
    client.post(
        "/auth/register",
        json={
            "email": "organizer@example.com",
            "password": "secret123"
        }
    )

    user = db_session.query(User).filter(
        User.email == "organizer@example.com"
    ).first()

    user.role = UserRole.ORGANIZER
    db_session.commit()

    venue = Venue(
    name="Test Venue",
    address="Test Address",
    city="Mumbai",
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "organizer@example.com",
            "password": "secret123"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Organizer Event",
            "description": "Created by organizer",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert response.status_code == 201


def test_admin_can_create_event(client, db_session):
    client.post(
        "/auth/register",
        json={
            "email": "admin@example.com",
            "password": "secret123"
        }
    )

    user = db_session.query(User).filter(
        User.email == "admin@example.com"
    ).first()

    user.role = UserRole.ADMIN
    db_session.commit()

    venue = Venue(
        name="Admin Test Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    login_response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "secret123"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Admin Event",
            "description": "Created by admin",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert response.status_code == 201


def test_organizer_cannot_update_another_organizers_event(client, db_session):
    # Create organizer 1
    client.post(
        "/auth/register",
        json={
            "email": "organizer1@example.com",
            "password": "secret123"
        }
    )

    organizer1 = db_session.query(User).filter(
        User.email == "organizer1@example.com"
    ).first()

    organizer1.role = UserRole.ORGANIZER
    db_session.commit()

    venue = Venue(
        name="Ownership Test Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Login organizer 1
    login_response = client.post(
        "/auth/login",
        data={
            "username": "organizer1@example.com",
            "password": "secret123"
        }
    )

    token1 = login_response.json()["access_token"]

    # Organizer 1 creates an event
    event_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "title": "Organizer 1 Event",
            "description": "Owned by organizer 1",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert event_response.status_code == 201

    event = event_response.json()

    # Create organizer 2
    client.post(
        "/auth/register",
        json={
            "email": "organizer2@example.com",
            "password": "secret123"
        }
    )

    organizer2 = db_session.query(User).filter(
        User.email == "organizer2@example.com"
    ).first()

    organizer2.role = UserRole.ORGANIZER
    db_session.commit()

    # Login organizer 2
    login_response = client.post(
        "/auth/login",
        data={
            "username": "organizer2@example.com",
            "password": "secret123"
        }
    )

    token2 = login_response.json()["access_token"]

    # Organizer 2 tries to update organizer 1's event
    response = client.put(
        f"/events/{event['id']}",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "title": "Hacked Event",
            "description": "Should not be allowed",
            "event_date": "2027-01-02T18:00:00",
            "venue_id": venue.id,
            "version": event["version"]
        }
    )

    assert response.status_code == 403


def test_organizer_cannot_delete_another_organizers_event(client, db_session):
    # Create organizer 1
    client.post(
        "/auth/register",
        json={
            "email": "deleteowner1@example.com",
            "password": "secret123"
        }
    )

    organizer1 = db_session.query(User).filter(
        User.email == "deleteowner1@example.com"
    ).first()

    organizer1.role = UserRole.ORGANIZER
    db_session.commit()

    venue = Venue(
        name="Delete Ownership Venue",
        address="Test Address",
        city="Mumbai"
    )

    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)

    # Login organizer 1
    login_response = client.post(
        "/auth/login",
        data={
            "username": "deleteowner1@example.com",
            "password": "secret123"
        }
    )

    token1 = login_response.json()["access_token"]

    # Organizer 1 creates an event
    event_response = client.post(
        "/events/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "title": "Event To Protect",
            "description": "Owned by organizer 1",
            "event_date": "2027-01-01T18:00:00",
            "venue_id": venue.id
        }
    )

    assert event_response.status_code == 201

    event = event_response.json()

    # Create organizer 2
    client.post(
        "/auth/register",
        json={
            "email": "deleteowner2@example.com",
            "password": "secret123"
        }
    )

    organizer2 = db_session.query(User).filter(
        User.email == "deleteowner2@example.com"
    ).first()

    organizer2.role = UserRole.ORGANIZER
    db_session.commit()

    # Login organizer 2
    login_response = client.post(
        "/auth/login",
        data={
            "username": "deleteowner2@example.com",
            "password": "secret123"
        }
    )

    token2 = login_response.json()["access_token"]

    # Organizer 2 tries to delete organizer 1's event
    response = client.delete(
        f"/events/{event['id']}",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 403