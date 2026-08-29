from fastapi import FastAPI
from app.core.config import Settings
import asyncio

from app.api.auth import router as auth_router
from app.api.organizer import router as organizer_router
from app.api.venues import router as venues_router
from app.api.events import router as events_router
from app.api.bookings import router as bookings_router
from app.api.ws import router as ws_router
from app.services.hold_expiration import listen_for_expired_holds


async def lifespan(app: FastAPI):
    task = asyncio.create_task(listen_for_expired_holds())

    yield

    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(organizer_router)
app.include_router(venues_router)
app.include_router(events_router)
app.include_router(bookings_router)
app.include_router(ws_router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": Settings.APP_NAME
    }


