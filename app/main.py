from fastapi import FastAPI
from app.core.config import Settings
from app.api.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": Settings.APP_NAME
    }