from fastapi import FastAPI
from fastapi.routing import APIRoute

from dojo.core.config import settings
from dojo.api.main import api_router


# def custom_generate_unique_id(route: APIRoute) -> str:
#     return f"{route.tags[0]}-{route.name}"
#

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # generate_unique_id_function=custom_generate_unique_id,
)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def home() -> dict[str, str]:
    return {"message": "Hello there"}
