from pydantic import BaseModel, constr, Field
from typing import Optional, Any, Dict
from cyst.api.environment.platform_specification import PlatformSpecification, PlatformType


# @pydantic.dataclasses.dataclass(frozen=True)
# class Platform(PlatformSpecification):
#     pass

class Parametrization(BaseModel):
    """ """
    parameters: dict[str, Any]

class Environment(BaseModel):
    """ """
    id: Optional[str] = None
    platform: PlatformSpecification = Field(default=PlatformSpecification(PlatformType.SIMULATED_TIME, "CYST"))
    configuration: str = Field(default="configuration_1")
    parameters: Dict[str, Any] = Field(default={})


class EnvironmentOut(BaseModel):
    """ """
    id: str
    platform: str
    provider: str
    state: str
    agent_manager_port: int
