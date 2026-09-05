import smtplib
from email.message import EmailMessage

from app.celery_app import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.event import Event
from app.models.user import User
from app.services.pdf_service import generate_ticket_pdf


@celery_app.task(bind=True, max_retries=3)
def send_ticket_email(self, booking_id: int):
    db = SessionLocal()

    try:
        # Get booking
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .first()
        )

        if not booking:
            raise ValueError("Booking not found")

        # Get seat through booking_id
        seat = (
            db.query(Seat)
            .filter(Seat.booking_id == booking.id)
            .first()
        )

        if not seat:
            raise ValueError("Seat not found")

        # Get event
        event = (
            db.query(Event)
            .filter(Event.id == booking.event_id)
            .first()
        )

        if not event:
            raise ValueError("Event not found")

        # Get user
        user = (
            db.query(User)
            .filter(User.id == booking.user_id)
            .first()
        )

        if not user:
            raise ValueError("User not found")

        # Generate PDF
        pdf_bytes = generate_ticket_pdf(
            booking=booking,
            seat=seat,
            event=event,
        )

        # Create email
        msg = EmailMessage()

        msg["Subject"] = f"Your TicketVault ticket - {event.title}"
        msg["From"] = "tickets@ticketvault.dev"
        msg["To"] = user.email

        msg.set_content(
            f"""
Hello,

Your booking for {event.title} has been confirmed.

Booking ID: {booking.id}
Seat: {seat.row_label}{seat.seat_number}
Amount Paid: INR {booking.total_amount}

Your TicketVault ticket is attached to this email.

Thank you for using TicketVault!
"""
        )

        # Attach PDF
        msg.add_attachment(
            pdf_bytes,
            maintype="application",
            subtype="pdf",
            filename=f"ticket_{booking.id}.pdf",
        )

        # Send email
        with smtplib.SMTP(
            settings.SMTP_HOST,
            settings.SMTP_PORT,
        ) as server:

            server.starttls()

            server.login(
                settings.SMTP_USER,
                settings.SMTP_PASSWORD,
            )

            server.send_message(msg)

        print(
            f"📧 Ticket email sent successfully for booking {booking.id}"
        )

        return {
            "status": "success",
            "booking_id": booking.id,
        }

    except Exception as exc:
        print(
            f"❌ Failed to send ticket email for booking "
            f"{booking_id}: {exc}"
        )

        raise self.retry(
            exc=exc,
            countdown=10,
        )

    finally:
        db.close()