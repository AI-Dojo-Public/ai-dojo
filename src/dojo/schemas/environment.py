import dataclasses
from enum import Enum

import pydantic
from pydantic import BaseModel, constr, Field
from cyst.api.environment.platform_specification import PlatformType


class PlatformProvider(str, Enum):
    cyst = 'CYST'
    docker_cryton = 'docker+cryton'

class PlatformSpecification(BaseModel):
    type: PlatformType
    provider: PlatformProvider


class Environment(BaseModel):
    name: constr(min_length=1)
    platform: PlatformSpecification
    configuration: str
