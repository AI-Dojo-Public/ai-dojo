from typing import Any

from pydantic import BaseModel


class AvailableConfigurations(BaseModel):
    available_configurations: list[str]

class ScenarioOut(BaseModel):
    configuration_json: str
    description: str
