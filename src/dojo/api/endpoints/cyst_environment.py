import base64

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pathlib import Path

from dataclasses import asdict
from dojo.schemas.environment import Environment
from dojo.schemas.configuration import Configuration
from dojo.controller import environments, EnvironmentWrapper, EnvironmentAction, ActionResponse, EnvironmentState


router = APIRouter(
    prefix="/environment",
    tags=["environments"],
    responses={
        404: {"description": "Not found"},
    },
)

max_concurrent_environments = 1


def get_environment_wrapper(id: str) -> EnvironmentWrapper:
    try:
        return environments[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=asdict(ActionResponse(id, EnvironmentState.TERMINATED.name, False, "The environment with the given id was not found.")))


platform_type_description = """
## Platform types
- **1 = simulation (default)**
- **2 = emulation**
"""


@router.post(
    "/create/",
    status_code=status.HTTP_201_CREATED,
    description=platform_type_description,
)
async def create(env: Environment) -> ActionResponse:
    if len(environments) >= max_concurrent_environments:
        raise HTTPException(status_code=409, detail=asdict(ActionResponse(env.id, "", False, f"At most {max_concurrent_environments} concurrent environments can be run at the same time.")))

    if env.id and env.id in environments:
        raise HTTPException(status_code=409, detail=asdict(ActionResponse(env.id, "", False, f"Environment with id {env.id} already exists, cannot create a new one.")))

    config_str = None
    if env.configuration:
        if len(env.configuration) < 256:
            path = Path("src", "dojo", "configurations").joinpath(env.configuration + ".json")
            if path.exists():
                with open(path, "r") as f:
                    config_str = f.read()
        if not config_str:
            config_str = base64.b64decode(env.configuration).decode("utf-8")

    ew = EnvironmentWrapper(env.platform, env.id, config_str)
    response = await ew.start()
    environments[str(ew.id)] = ew

    return response


@router.post(
    "/init/",
    status_code=status.HTTP_200_OK,
)
async def init(id) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.INIT)


@router.post(
    "/configure/",
    status_code=status.HTTP_200_OK,
)
async def configure(id: str, cfg: Configuration) -> ActionResponse:
    config_str = None
    if cfg.config:
        if len(cfg.config) < 256:
            path = Path("src", "dojo", "configurations").joinpath(cfg.config + ".json")
            if path.exists():
                with open(path, "r") as f:
                    config_str = f.read()
        if not config_str:
            config_str = base64.b64decode(cfg.config).decode("utf-8")
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.CONFIGURE, config_str)


@router.post(
    "/reset/",
    status_code=status.HTTP_200_OK,
)
async def reset(id) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.RESET)


@router.post(
    "/terminate/",
    status_code=status.HTTP_200_OK,
)
async def terminate(id) -> ActionResponse:
    response = await get_environment_wrapper(id).perform_action(EnvironmentAction.TERMINATE)
    if id in environments:
        del environments[id]
    return response


@router.post(
    "/commit/",
    status_code=status.HTTP_200_OK,
)
async def commit(id) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.COMMIT)


@router.post(
    "/pause/",
    status_code=status.HTTP_200_OK,
)
async def pause(id) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.PAUSE)


@router.post(
    "/run/",
    status_code=status.HTTP_200_OK,
)
async def run(id: str) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.RUN)


@router.get(
    "/list/",
    status_code=status.HTTP_200_OK,
)
async def list_environments() -> JSONResponse:
    environments_info = dict()
    for env_name, env in environments.items():
        environments_info[env_name] = {
            "state": (await env.perform_action(EnvironmentAction.GET_STATE)).state,
            "type": env.platform.type.name,
            "provider": env.platform.provider
        }
    return JSONResponse(status_code=200, content=environments_info)


@router.get(
    "/get/",
    status_code=status.HTTP_200_OK,
)
async def get_environment(id) -> JSONResponse:
    env = get_environment_wrapper(id)
    env_info = {"state": (await env.perform_action(EnvironmentAction.GET_STATE)).state, "platform": env.platform.type.name}
    return JSONResponse(content=env_info)
