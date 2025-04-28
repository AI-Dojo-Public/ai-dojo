from fastapi import FastAPI, WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str: WebSocket] = {}

    async def connect(self, websocket: WebSocket, environment_id: str):
        await websocket.accept()
        self.active_connections[environment_id] = websocket

    def disconnect(self, environment_id: str):
        del self.active_connections[environment_id]

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_personal_message(self, message: str, environment_id: str):
        await self.active_connections[environment_id].send_text(message)

socket_manager = ConnectionManager()
