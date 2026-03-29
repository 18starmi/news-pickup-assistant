from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: int
    name: str
    base_url: str
    kind: str
    is_active: bool
