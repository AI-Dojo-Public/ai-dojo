from pydantic import BaseModel, Field
from typing import Optional


class AgentAddition(BaseModel):
    path: str
    local: Optional[bool] = Field(default=False)
    editable: Optional[bool] = Field(default=False)
    user: Optional[str] = Field(default="")
    access_token: Optional[str] = Field(default="")


class AgentRemoval(BaseModel):
    name: str
    delete_code: Optional[bool] = Field(default=False)
    force: Optional[bool] = Field(default=False)
