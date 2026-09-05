from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ticketvault",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.imports = (
    "app.tasks.test_tasks",
    "app.tasks.email_tasks",
)