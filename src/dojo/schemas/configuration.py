from typing import Any

from pydantic import BaseModel


class AvailableConfigurations(BaseModel):
    available_configurations: list[str]

class ConfigurationJson(BaseModel):
    configuration_json: str
