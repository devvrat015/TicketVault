import time

from app.celery_app import celery_app


@celery_app.task
def add_numbers_slowly(a: int, b: int) -> int:
    time.sleep(5)
    return a + b