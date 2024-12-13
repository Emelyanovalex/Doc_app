from fastapi import WebSocket
from typing import List

class ConnectionManager:
    """
    Менеджер для управления WebSocket-соединениями, с поддержкой разделения по item_id.
    """

    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, item_id: int):
        """
        Подключает клиента к WebSocket и добавляет соединение в группу по item_id.

        Аргументы:
            websocket (WebSocket): WebSocket-соединение клиента.
            item_id (int): Идентификатор группы.
        """
        await websocket.accept()
        if item_id not in self.active_connections:
            self.active_connections[item_id] = []
        self.active_connections[item_id].append(websocket)

    def disconnect(self, websocket: WebSocket, item_id: int):
        """
        Отключает клиента от WebSocket и удаляет соединение из группы по item_id.

        Аргументы:
            websocket (WebSocket): WebSocket-соединение клиента.
            item_id (int): Идентификатор группы.
        """
        if item_id in self.active_connections:
            self.active_connections[item_id].remove(websocket)
            if not self.active_connections[item_id]:
                del self.active_connections[item_id]

    async def broadcast(self, message: str, item_id: int):
        """
        Рассылает сообщение всем клиентам в группе по item_id.

        Аргументы:
            message (str): Сообщение для отправки.
            item_id (int): Идентификатор группы.
        """
        if item_id in self.active_connections:
            for connection in self.active_connections[item_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения: {e}")

# Экземпляр ConnectionManager для работы с WebSocket
manager = ConnectionManager()
