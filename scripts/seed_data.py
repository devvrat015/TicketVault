from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.venue import Venue
from app.models.event import Event
from app.models.seat import Seat
from app.models.enums import UserRole, SeatStatus


fake = Faker()

# Configuration
NUM_ORGANIZERS = 5
NUM_VENUES = 30
NUM_EVENTS = 10_000
SEATS_PER_EVENT = 10

CITIES = [
    "Mumbai",
    "Pune",
    "Nashik",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
]


def create_organizers(db: Session):
    organizers = []

    for i in range(NUM_ORGANIZERS):
        organizer = User(
            email=f"seed_organizer_{i}@ticketvault.test",
            hashed_password="seeded-test-password",
            role=UserRole.ORGANIZER,
            is_active=True,
        )

        db.add(organizer)
        organizers.append(organizer)

    db.flush()

    return organizers


def create_venues(db: Session):
    venues = []

    for i in range(NUM_VENUES):
        venue = Venue(
            name=fake.company() + " Arena",
            city=CITIES[i % len(CITIES)],
            address=fake.address(),
        )

        db.add(venue)
        venues.append(venue)

    db.flush()

    return venues


def create_events(db: Session, organizers, venues):
    event_count = 0

    start_date = datetime.utcnow() + timedelta(days=1)

    batch_size = 500

    for batch_start in range(0, NUM_EVENTS, batch_size):

        events_batch = []

        batch_end = min(
            batch_start + batch_size,
            NUM_EVENTS
        )

        for i in range(batch_start, batch_end):

            event_date = start_date + timedelta(
                days=fake.random_int(min=0, max=365),
                hours=fake.random_int(min=0, max=23),
                minutes=fake.random_int(min=0, max=59),
            )

            event = Event(
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=300),
                event_date=event_date,
                venue_id=venues[i % len(venues)].id,
                organizer_id=organizers[i % len(organizers)].id,
            )

            db.add(event)
            events_batch.append(event)

        db.flush()

        # Create seats for every event
        for event in events_batch:

            for seat_number in range(1, SEATS_PER_EVENT + 1):

                seat = Seat(
                    row_label=fake.random_element(
                        elements=("A", "B", "C", "D", "E")
                    ),
                    seat_number=seat_number,
                    price=fake.random_int(
                        min=300,
                        max=2000
                    ),
                    status=SeatStatus.AVAILABLE,
                    event_id=event.id,
                )

                db.add(seat)

        db.commit()

        event_count += len(events_batch)

        print(
            f"Created {event_count}/{NUM_EVENTS} events"
        )


def main():
    db = SessionLocal()

    try:
        print("Starting seed...")

        print("Creating organizers...")
        organizers = create_organizers(db)

        print("Creating venues...")
        venues = create_venues(db)

        db.commit()

        print("Creating events and seats...")
        create_events(db, organizers, venues)

        print()
        print("Seed completed successfully!")
        print(f"Events: {NUM_EVENTS}")
        print(f"Venues: {NUM_VENUES}")
        print(f"Organizers: {NUM_ORGANIZERS}")
        print(f"Seats: {NUM_EVENTS * SEATS_PER_EVENT}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()