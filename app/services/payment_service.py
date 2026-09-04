import stripe

from app.core.config import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    seat,
    user,
    idempotency_key: str
):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],

        line_items=[
            {
                "price_data": {
                    "currency": "inr",
                    "product_data": {
                        "name": f"Seat {seat.row_label}{seat.seat_number}"
                    },
                    "unit_amount": seat.price * 100,
                },
                "quantity": 1,
            }
        ],

        mode="payment",

        success_url=(
            settings.STRIPE_SUCCESS_URL
            + "?session_id={CHECKOUT_SESSION_ID}"
        ),

        cancel_url=settings.STRIPE_CANCEL_URL,

        metadata={
            "seat_id": str(seat.id),
            "user_id": str(user.id),
        },

        idempotency_key=idempotency_key,
    )

    return session