from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager

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
