import json


async def check_and_store_idempotency(
    redis_client,
    key: str,
    ttl: int = 86400
):
    """
    Returns:
        (is_duplicate, stored_result)
    """

    redis_key = f"idempotency:{key}"

    # Atomic SET NX
    was_set = await redis_client.set(
        redis_key,
        "processing",
        nx=True,
        ex=ttl
    )

    if not was_set:
        existing = await redis_client.get(redis_key)

        if existing == "processing":
            return True, None

        return True, json.loads(existing)

    return False, None


async def store_idempotent_result(
    redis_client,
    key: str,
    result: dict,
    ttl: int = 86400
):
    redis_key = f"idempotency:{key}"

    await redis_client.set(
        redis_key,
        json.dumps(result),
        ex=ttl
    )