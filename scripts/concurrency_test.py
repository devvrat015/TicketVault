import asyncio
import json

import httpx

BASE_URL = "http://localhost:8000"

EVENT_ID = 1

SEAT_ID = 9


with open("tokens.json") as f:
    TOKENS = json.load(f)


async def try_book(client, token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = await client.post(
        f"{BASE_URL}/bookings/{EVENT_ID}/book-seat/{SEAT_ID}",
        headers=headers
    )

    try:
        body = response.json()
    except Exception:
        body = response.text

    return response.status_code, body


async def main():

    async with httpx.AsyncClient(timeout=30.0) as client:

        results = await asyncio.gather(
            *[try_book(client, token) for token in TOKENS]
        )

    successes = [r for r in results if r[0] == 200]

    print("=" * 60)

    print(f"Successful bookings : {len(successes)}")

    print("=" * 60)

    for index, result in enumerate(results, start=1):
        print(f"{index:02d}. {result}")



asyncio.run(main())