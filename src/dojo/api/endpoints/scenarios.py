import asyncio
import base64
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, File
from fastapi.responses import FileResponse

from dojo.lib import constants
from dojo.lib import util
from dojo.schemas.configuration import AvailableConfigurations, ScenarioOut

router = APIRouter(
    prefix="/scenario",
    tags=["scenarios"],
    responses={
        404: {"description": "Not found"},
    },
)

@router.get(
    "/list/",
    status_code=status.HTTP_200_OK,
)
async def list_scenarios() -> AvailableConfigurations:
    return AvailableConfigurations(available_configurations=util.list_scenario_files())


@router.get(
    "/get/",
    status_code=status.HTTP_200_OK,
)
async def get_scenario(file_name: str) -> ScenarioOut:
    try:
        util.ensure_json_configuration(file_name)
        return ScenarioOut(configuration_json=util.read_scenario_file(file_name), description=util.read_scenario_description(file_name))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/get/image/",
    status_code=status.HTTP_200_OK,
)
async def get_scenario_image(file_name: str) -> FileResponse:
    path = constants.PATH_CONFIGURATIONS.joinpath(file_name, file_name + ".png")
    if path.exists():
        return FileResponse(path)
    raise HTTPException(status_code=404)