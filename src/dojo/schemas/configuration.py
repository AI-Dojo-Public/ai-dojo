from pydantic import BaseModel


class Configuration(BaseModel):
    config: str