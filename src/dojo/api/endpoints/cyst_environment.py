import asyncio
import base64
import json
import socket
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pathlib import Path

from dataclasses import asdict
from dojo.schemas.environment import Environment, EnvironmentOut, Parametrization
from dojo.schemas.configuration import ScenarioOut, AvailableConfigurations
from dojo.controller import environments, EnvironmentWrapper, EnvironmentAction, ActionResponse, EnvironmentState
from dojo.lib import util


async_lock = asyncio.Lock()

router = APIRouter(
    prefix="/environment",
    tags=["environments"],
    responses={
        404: {"description": "Not found"},
    },
)


def get_environment_wrapper(id: str) -> EnvironmentWrapper:
    try:
        return environments[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=asdict(ActionResponse(id, EnvironmentState.TERMINATED.name, False, "The environment with the given id was not found.")))


platform_type_description = """
## Platform types
- **1 = Simulated time**
- **2 = Real time**
"""


@router.post(
    "/create/",
    status_code=status.HTTP_201_CREATED,
    description=platform_type_description,
)
async def create(env: Environment) -> ActionResponse:
    if env.id and env.id in environments:
        raise HTTPException(status_code=409, detail=asdict(ActionResponse(env.id, "", False, f"Environment with id {env.id} already exists, cannot create a new one.")))

    config_str = None
    if env.configuration:
        if len(env.configuration) < 256:
            try:
                json_configuration_path = util.ensure_json_configuration(env.configuration)
            except RuntimeError as e:
                raise HTTPException(status_code=409, detail=str(e))

            with open(json_configuration_path, "r") as f:
                config_str = f.read()
        if not config_str:
            config_str = base64.b64decode(env.configuration).decode("utf-8")

    async with async_lock:
        agent_env_port = await util.set_first_available_env_manager_port()

    ew = EnvironmentWrapper(env.platform, env.id, config_str, env.parameters, agent_env_port)
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
async def configure(id: str, parameters: Parametrization) -> ActionResponse:
    return await get_environment_wrapper(id).perform_action(EnvironmentAction.CONFIGURE, parameters.parameters)


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
async def list_environments() -> list[EnvironmentOut]:
    environments_info = []
    for env_name, env in environments.items():
        environments_info.append(EnvironmentOut(
            id=env_name,
            state=(await env.perform_action(EnvironmentAction.GET_STATE)).state,
            platform=env.platform.type.name,
            provider=env.platform.provider,
            agent_manager_port=env.agent_manager_port,
        ))

    return environments_info


@router.get(
    "/get/",
    status_code=status.HTTP_200_OK,
)
async def get_environment(id) -> EnvironmentOut:
    env = get_environment_wrapper(id)
    response = EnvironmentOut(
        id=env.id,
        state=(await env.perform_action(EnvironmentAction.GET_STATE)).state,
        platform=env.platform.type.name,
        provider=env.platform.provider,
        agent_manager_port=env.agent_manager_port
        )

    return response

@router.get(
    "/configuration/list/",
    status_code=status.HTTP_200_OK,
)
async def list_configurations() -> AvailableConfigurations:
    return AvailableConfigurations(available_configurations=util.list_scenario_files())


@router.get(
    "/configuration/get/",
    status_code=status.HTTP_200_OK,
)
async def get_configuration(file_name: str) -> ScenarioOut:
    try:
        util.ensure_json_configuration(file_name)
        return ScenarioOut(configuration_json=util.read_scenario_file(file_name))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
