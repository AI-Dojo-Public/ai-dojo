from fastapi import FastAPI
from fastapi.routing import APIRoute

from dojo.core.config import settings
from dojo.api.main import api_router
from dojo.controller import environments, EnvironmentAction


# def custom_generate_unique_id(route: APIRoute) -> str:
#     return f"{route.tags[0]}-{route.name}"
#

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # generate_unique_id_function=custom_generate_unique_id,
)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...", end="")
    for env in environments.values():
        await env.perform_action(EnvironmentAction.TERMINATE)
    print("[OK]")


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Hello there"}
