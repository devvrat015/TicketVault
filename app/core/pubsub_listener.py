import json

from app.core.redis_client import async_redis_client
from app.core.connection_manager import manager


async def listen_for_events():
    pubsub = async_redis_client.pubsub()

    await pubsub.psubscribe("event:*:updates")

    print("📡 Redis Pub/Sub listener started...")

    try:
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

    finally:
        await pubsub.close()