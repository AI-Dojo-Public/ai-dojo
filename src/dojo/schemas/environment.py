import dataclasses
import pydantic
from pydantic import BaseModel, constr, Field
from typing import Optional
from cyst.api.environment.platform_specification import PlatformSpecification, PlatformType


# @pydantic.dataclasses.dataclass(frozen=True)
# class Platform(PlatformSpecification):
#     pass


class Environment(BaseModel):
    """ """
    id: Optional[str] = None
    platform: PlatformSpecification = Field(default=PlatformSpecification(PlatformType.SIMULATED_TIME, "CYST"))
    configuration: str
