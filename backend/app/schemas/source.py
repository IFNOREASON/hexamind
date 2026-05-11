from pydantic import BaseModel
from datetime import datetime


class SourceOut(BaseModel):
    id: int
    name: str
    source_type: str
    file_type: str
    file_size: int | None = None
    url: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LinkCreate(BaseModel):
    url: str
    name: str
