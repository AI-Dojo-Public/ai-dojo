import dataclasses
import pydantic
from pydantic import BaseModel, constr, Field
from cyst.api.environment.platform_specification import PlatformSpecification, PlatformType


# @pydantic.dataclasses.dataclass(frozen=True)
# class Platform(PlatformSpecification):
#     pass


class Environment(BaseModel):
    """ """

    name: constr(min_length=1)
    platform: PlatformSpecification = Field(default=PlatformSpecification(PlatformType.SIMULATION, "CYST"))
    configuration: str
