from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, event_id: int, websocket: WebSocket):
        await websocket.accept()

        self.active_connections.setdefault(event_id, []).append(websocket)

        print(
            f"🔌 WebSocket connected: event={event_id}, "
            f"connections={len(self.active_connections[event_id])}"
        )

    def disconnect(self, event_id: int, websocket: WebSocket):
        if event_id in self.active_connections:

            self.active_connections[event_id].remove(websocket)

            if not self.active_connections[event_id]:
                del self.active_connections[event_id]

        print(
            f"🔌 WebSocket disconnected: event={event_id}"
        )

    async def broadcast(self, event_id: int, message: dict):

        connections = self.active_connections.get(event_id, [])

        print(
            f"📡 Broadcasting to event={event_id}, "
            f"connections={len(connections)}, "
            f"message={message}"
        )

        for connection in connections:
            await connection.send_json(message)


manager = ConnectionManager()