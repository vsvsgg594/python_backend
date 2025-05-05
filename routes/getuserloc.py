from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List


router=APIRouter()
# List to keep track of connected clients
connected_clients: List[WebSocket] = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            # Receive message from the client
            data = await websocket.receive_text()
            print(f"Received data: {data}")  # Log the received data

            # Broadcast the received message to all connected clients
          
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
