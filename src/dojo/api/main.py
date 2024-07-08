from fastapi import APIRouter

from dojo.api.endpoints import cyst_environment


api_router = APIRouter()
api_router.include_router(cyst_environment.router)
