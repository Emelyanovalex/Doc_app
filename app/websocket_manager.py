from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


# Экземпляр ConnectionManager
manager = ConnectionManager()


async def broadcast(self, message: str):
    print(f"Broadcasting message: {message}")
    for connection in self.active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Failed to send message: {e}")