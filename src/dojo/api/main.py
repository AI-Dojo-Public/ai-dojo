from fastapi import APIRouter

from dojo.api.endpoints import cyst_environment
from dojo.api.endpoints import agent_management
from dojo.api.endpoints import scenarios


api_router = APIRouter()
api_router.include_router(cyst_environment.router)
api_router.include_router(agent_management.router)
api_router.include_router(scenarios.router)
