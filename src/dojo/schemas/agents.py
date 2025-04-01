from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional


class AgentMethod(Enum):
    GIT = "git"
    PYPI = "pypi"

class AgentAddition(BaseModel):
    method: AgentMethod
    path: str
    user: Optional[str] = Field(default="")
    access_token: Optional[str] = Field(default="")


class AgentRemoval(BaseModel):
    name: str
    delete_code: Optional[bool] = Field(default=False)
    force: Optional[bool] = Field(default=False)
