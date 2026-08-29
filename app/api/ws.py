from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.connection_manager import manager

router = APIRouter()


@router.websocket("/ws/events/{event_id}/seats")
async def seat_map_ws(websocket: WebSocket, event_id: int):
    await manager.connect(event_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(event_id, websocket)

# @router.post("/ws/test-broadcast/{event_id}")
# async def test_broadcast(event_id: int):
#     await manager.broadcast(
#         event_id,
#         {
#             "seat_id": 5,
#             "status": "booked",
#         },
#     )

#     return {"message": "Broadcast sent"}