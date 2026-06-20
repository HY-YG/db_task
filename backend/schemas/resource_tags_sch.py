from backend.schemas.base import ORMModel


class ResourceTagCreate(ORMModel):
    resource_id: int
    tag_id: int


class ResourceTagResponse(ORMModel):
    resource_id: int
    tag_id: int
