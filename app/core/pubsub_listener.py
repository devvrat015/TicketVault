import asyncio
import json

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.connection_manager import manager


async def listen_for_events():
    while True:
        pubsub = None

        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )

            pubsub = client.pubsub()

            await pubsub.psubscribe("event:*:updates")

            print("📡 Redis Pub/Sub listener started...")

            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    channel = message["channel"]

                    event_id = int(
                        channel.split(":")[1]
                    )

                    data = json.loads(message["data"])

                    print(
                        f"📨 Received from {channel}: {data}"
                    )

                    await manager.broadcast(
                        event_id,
                        data,
                    )

        except asyncio.CancelledError:
            raise

        except Exception as e:
            print(
                f"❌ Redis Pub/Sub listener error: {e}"
            )

            await asyncio.sleep(2)

        finally:
            if pubsub:
                await pubsub.aclose()

            if "client" in locals():
                await client.aclose()