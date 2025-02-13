from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from dojo.schemas.environment import Environment
from dojo.controller import environments, EnvironmentWrapper, EnvironmentAction


router = APIRouter(
    prefix="/environment",
    tags=["environments"],
    responses={
        404: {"description": "Not found"},
    },
)


def get_environment_wrapper(name: str) -> EnvironmentWrapper:
    try:
        return environments[name]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Environment {name} not found")


platform_type_description = """
## Platform types
- **1 = simulation (default)**
- **2 = emulation**
"""


@router.post(
    "/create/",
    status_code=status.HTTP_201_CREATED,
    responses={201: {"description": "Object successfully created"}},
    description=platform_type_description,
)
async def create(env: Environment):
    if env.name in environments:
        raise HTTPException(status_code=409, detail=f"Environment {env.name} already exists")
    ew = EnvironmentWrapper(env.platform, env.name, env.configuration)
    ew.start()
    environments[env.name] = ew


@router.post(
    "/init/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment initialized"}},
)
async def init(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.INIT)


@router.post(
    "/configure/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment configured"}},
)
async def configure(name: str):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.CONFIGURE)


@router.post(
    "/reset/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment retested"}},
)
async def reset(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.RESET)


@router.post(
    "/terminate/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment terminated"}},
)
async def terminate(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.TERMINATE)


@router.post(
    "/close/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment closed"}},
)
async def close(name):
    await get_environment_wrapper(name).perform_action(None)
    environments.pop(name)


@router.post(
    "/commit/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment commited"}},
)
async def commit(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.COMMIT)


@router.post(
    "/pause/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment paused"}},
)
async def pause(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.PAUSE)


@router.post(
    "/run/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment running"}},
)
async def run(name):
    await get_environment_wrapper(name).perform_action(EnvironmentAction.RUN)


@router.get(
    "/list/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Listed environments"}},
)
async def list_environments():
    environments_info = dict()
    for env_name, env in environments.items():
        environments_info[env_name] = {
            "state": await env.perform_action(EnvironmentAction.GET_STATE),
            "platform": env.platform.type.name,
        }
    return JSONResponse(content=environments_info)


@router.get(
    "/get/",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Environment info"}},
)
async def get_environment(name):
    env = get_environment_wrapper(name)
    env_info = {"state": await env.perform_action(EnvironmentAction.GET_STATE), "platform": env.platform.type.name}
    return JSONResponse(content=env_info)
