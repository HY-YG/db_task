import json

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import course_resources_crud, resource_versions_crud
from backend.schemas.course_resources_sch import CourseResourceCreate, CourseResourceResponse
from backend.schemas.resource_versions_sch import ResourceVersionCreate, ResourceVersionResponse
from backend.services import storage, vectorize_agent


async def handle_upload(
    *,
    db: AsyncSession,
    chapter_id: int,
    file: UploadFile,
    resource_title: str | None,
    version_description: str | None,
) -> dict:
    meta = await storage.save_upload_file(file)
    resource = await course_resources_crud.create_resource(
        db,
        CourseResourceCreate(
            chapter_id=chapter_id,
            resource_title=resource_title or meta["original_name"],
            resource_content=meta["stored_path"],
            resource_type=meta["mime_type"],
        ),
    )
    version_payload = {
        "note": version_description,
        "file": meta,
    }
    version = await resource_versions_crud.create_version(
        db,
        ResourceVersionCreate(
            resource_id=resource.resource_id,
            version_status="current",
            version_description=json.dumps(version_payload, ensure_ascii=False),
        ),
    )
    vectorize_result = await vectorize_agent.handle_vectorize(db=db, resource_id=resource.resource_id)
    return {
        "resource": CourseResourceResponse.model_validate(resource),
        "version": ResourceVersionResponse.model_validate(version),
        "file": meta,
        "vectorize_result": vectorize_result.to_response_payload(),
        "suggested_questions": vectorize_result.suggested_questions,
    }
