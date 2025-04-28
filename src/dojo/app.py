from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

from dojo.api.endpoints.socket_manager import socket_manager
from dojo.core.config import settings
from dojo.api.main import api_router
from dojo.controller import environments, EnvironmentAction


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    yield

    print("Shutting down...", end="")
    for env in environments.values():
        await env.perform_action(EnvironmentAction.TERMINATE)
    print("[OK]")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Hello there"}


@app.websocket("/ws/{environment_id}")
async def websocket_endpoint(websocket: WebSocket, environment_id: str):
    await socket_manager.connect(websocket, environment_id)
    try:
        while True:
            await websocket.receive_text()
            # await socker_manager.broadcast(data)
    except WebSocketDisconnect as ex:
        socket_manager.disconnect(environment_id)