from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    """
    Менеджер для управления WebSocket-соединениями.

    Атрибуты:
        active_connections (List[WebSocket]): Список активных WebSocket-соединений.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Подключает клиента к WebSocket и добавляет соединение в список активных.

        Аргументы:
            websocket (WebSocket): WebSocket-соединение клиента.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Отключает клиента от WebSocket и удаляет соединение из списка активных.

        Аргументы:
            websocket (WebSocket): WebSocket-соединение клиента.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        """
        Отправляет сообщение конкретному клиенту через WebSocket.

        Аргументы:
            message (str): Сообщение для отправки.
            websocket (WebSocket): WebSocket-соединение клиента.
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """
        Отправляет сообщение всем подключенным клиентам.

        Аргументы:
            message (str): Сообщение для отправки.
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Ошибка при отправке сообщения: {e}")


# Экземпляр ConnectionManager для работы с WebSocket
manager = ConnectionManager()
