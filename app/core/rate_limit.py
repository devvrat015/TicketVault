from fastapi import Request, HTTPException
from fastapi import Depends

from app.api.deps import get_current_active_user
from app.models.user import User
from app.core.redis_client import redis_client


def rate_limiter(max_requests: int, window_seconds: int):
    def dependency(request: Request):
        client_id = request.client.host

        key = f"ratelimit:{client_id}:{request.url.path}"

        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, window_seconds)

        if count > max_requests:
            ttl = redis_client.ttl(key)

            raise HTTPException(
                status_code=429,
                detail="Too many requests, please try again later.",
                headers={"Retry-After": str(ttl)},
            )

    return dependency


def rate_limiter_by_user(max_requests: int, window_seconds: int):
    def dependency(
        current_user: User = Depends(get_current_active_user)
    ):
        key = f"ratelimit:user:{current_user.id}:{max_requests}:{window_seconds}"

        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, window_seconds)

        if count > max_requests:
            ttl = redis_client.ttl(key)

            raise HTTPException(
                status_code=429,
                detail="Too many requests, please try again later.",
                headers={"Retry-After": str(ttl)},
            )

        return current_user

    return dependency