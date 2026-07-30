import asyncio
import json

import httpx

BASE_URL = "http://localhost:8000"

PASSWORD = "Password@123"

NUMBER_OF_USERS = 20


async def register_user(client, email):
    payload = {
        "email": email,
        "password": PASSWORD
    }

    await client.post(
        f"{BASE_URL}/auth/register",
        json=payload
    )


async def login_user(client, email):
    data = {
        "username": email,
        "password": PASSWORD
    }

    response = await client.post(
        f"{BASE_URL}/auth/login",
        data=data
    )

    response.raise_for_status()

    return response.json()["access_token"]


async def main():

    tokens = []

    async with httpx.AsyncClient() as client:

        for i in range(1, NUMBER_OF_USERS + 1):

            email = f"user{i}@test.com"

            try:
                await register_user(client, email)
            except Exception:
                # User may already exist
                pass

            token = await login_user(client, email)

            tokens.append(token)

            print(f"✓ {email}")

    with open("tokens.json", "w") as f:
        json.dump(tokens, f, indent=4)

    print(f"\nGenerated {len(tokens)} tokens.")


asyncio.run(main())