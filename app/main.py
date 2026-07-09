from fastapi import FastAPI
from app.core.config import Settings

settings = Settings()

app = FastAPI()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }