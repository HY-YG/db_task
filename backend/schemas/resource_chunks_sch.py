from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class ResourceChunkCreate(ORMModel):
    resource_id: int
    chunk_index: int = Field(ge=0)
    content: str
    embedding: str


class ResourceChunkResponse(ORMModel):
    chunk_id: int
    resource_id: int
    chunk_index: int
    content: str
    embedding: str
    created_at: datetime
