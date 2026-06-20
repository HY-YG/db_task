from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import (
    course_chapters_crud,
    course_resources_crud,
    courses_crud,
    enrollment_relations_crud,
    resource_tags_crud,
    resource_versions_crud,
    tags_crud,
    teaching_relations_crud,
)
from backend.schemas.course_chapters_sch import CourseChapterCreate, CourseChapterResponse, CourseChapterUpdate
from backend.schemas.course_resources_sch import CourseResourceCreate, CourseResourceResponse, CourseResourceUpdate
from backend.schemas.courses_sch import CourseCreate, CourseResponse, CourseUpdate
from backend.schemas.enrollment_relations_sch import EnrollmentRelationCreate, EnrollmentRelationResponse
from backend.schemas.resource_tags_sch import ResourceTagCreate, ResourceTagResponse
from backend.schemas.resource_versions_sch import ResourceVersionCreate, ResourceVersionResponse, ResourceVersionUpdate
from backend.schemas.tags_sch import TagCreate, TagResponse, TagUpdate
from backend.schemas.teaching_relations_sch import TeachingRelationCreate, TeachingRelationResponse
from backend.utils.response import success_response

router = APIRouter(tags=["courses"])

courses_router = APIRouter(prefix="/courses", tags=["courses"])
chapters_router = APIRouter(prefix="/course-chapters", tags=["course_chapters"])
resources_router = APIRouter(prefix="/course-resources", tags=["course_resources"])
versions_router = APIRouter(prefix="/resource-versions", tags=["resource_versions"])
tags_router = APIRouter(prefix="/tags", tags=["tags"])
resource_tags_router = APIRouter(prefix="/resource-tags", tags=["resource_tags"])
teaching_router = APIRouter(prefix="/teaching-relations", tags=["teaching_relations"])
enrollment_router = APIRouter(prefix="/enrollment-relations", tags=["enrollment_relations"])


@courses_router.post("", status_code=status.HTTP_201_CREATED)
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.create_course(db, payload)
    return success_response(CourseResponse.model_validate(course))


@courses_router.get("")
async def list_courses(db: AsyncSession = Depends(get_db)) -> dict:
    courses = await courses_crud.list_courses(db)
    return success_response([CourseResponse.model_validate(item) for item in courses])


@courses_router.get("/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return success_response(CourseResponse.model_validate(course))


@courses_router.put("/{course_id}")
async def update_course(course_id: int, payload: CourseUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    course = await courses_crud.update_course(db, course, payload)
    return success_response(CourseResponse.model_validate(course))


@courses_router.delete("/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    await courses_crud.delete_course(db, course)
    return success_response()


@chapters_router.post("", status_code=status.HTTP_201_CREATED)
async def create_chapter(payload: CourseChapterCreate, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.create_chapter(db, payload)
    return success_response(CourseChapterResponse.model_validate(chapter))


@chapters_router.get("")
async def list_chapters(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    chapters = await course_chapters_crud.list_chapters(db, course_id=course_id)
    return success_response([CourseChapterResponse.model_validate(item) for item in chapters])


@chapters_router.get("/{chapter_id}")
async def get_chapter(chapter_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return success_response(CourseChapterResponse.model_validate(chapter))


@chapters_router.put("/{chapter_id}")
async def update_chapter(
    chapter_id: int,
    payload: CourseChapterUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    chapter = await course_chapters_crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    chapter = await course_chapters_crud.update_chapter(db, chapter, payload)
    return success_response(CourseChapterResponse.model_validate(chapter))


@chapters_router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    await course_chapters_crud.delete_chapter(db, chapter)
    return success_response()


@resources_router.post("", status_code=status.HTTP_201_CREATED)
async def create_resource(payload: CourseResourceCreate, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.create_resource(db, payload)
    return success_response(CourseResourceResponse.model_validate(resource))


@resources_router.get("")
async def list_resources(
    chapter_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    resources = await course_resources_crud.list_resources(db, chapter_id=chapter_id)
    return success_response([CourseResourceResponse.model_validate(item) for item in resources])


@resources_router.get("/{resource_id}")
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return success_response(CourseResourceResponse.model_validate(resource))


@resources_router.put("/{resource_id}")
async def update_resource(
    resource_id: int,
    payload: CourseResourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    resource = await course_resources_crud.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    resource = await course_resources_crud.update_resource(db, resource, payload)
    return success_response(CourseResourceResponse.model_validate(resource))


@resources_router.delete("/{resource_id}")
async def delete_resource(resource_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    await course_resources_crud.delete_resource(db, resource)
    return success_response()


@versions_router.post("", status_code=status.HTTP_201_CREATED)
async def create_version(payload: ResourceVersionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.create_version(db, payload)
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.get("")
async def list_versions(
    resource_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    versions = await resource_versions_crud.list_versions(db, resource_id=resource_id)
    return success_response([ResourceVersionResponse.model_validate(item) for item in versions])


@versions_router.get("/{version_id}")
async def get_version(version_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.put("/{version_id}")
async def update_version(version_id: int, payload: ResourceVersionUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    version = await resource_versions_crud.update_version(db, version, payload)
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.delete("/{version_id}")
async def delete_version(version_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    await resource_versions_crud.delete_version(db, version)
    return success_response()


@tags_router.post("", status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.create_tag(db, payload)
    return success_response(TagResponse.model_validate(tag))


@tags_router.get("")
async def list_tags(db: AsyncSession = Depends(get_db)) -> dict:
    tags = await tags_crud.list_tags(db)
    return success_response([TagResponse.model_validate(item) for item in tags])


@tags_router.get("/{tag_id}")
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return success_response(TagResponse.model_validate(tag))


@tags_router.put("/{tag_id}")
async def update_tag(tag_id: int, payload: TagUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    tag = await tags_crud.update_tag(db, tag, payload)
    return success_response(TagResponse.model_validate(tag))


@tags_router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    await tags_crud.delete_tag(db, tag)
    return success_response()


@resource_tags_router.post("", status_code=status.HTTP_201_CREATED)
async def create_resource_tag(payload: ResourceTagCreate, db: AsyncSession = Depends(get_db)) -> dict:
    rel = await resource_tags_crud.create_resource_tag(db, payload)
    return success_response(ResourceTagResponse.model_validate(rel))


@resource_tags_router.get("")
async def list_resource_tags(
    resource_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    relations = await resource_tags_crud.list_resource_tags(db, resource_id=resource_id, tag_id=tag_id)
    return success_response([ResourceTagResponse.model_validate(item) for item in relations])


@resource_tags_router.delete("")
async def delete_resource_tag(resource_id: int, tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await resource_tags_crud.delete_resource_tag(db, resource_id=resource_id, tag_id=tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Resource tag relation not found")
    return success_response()


@teaching_router.post("", status_code=status.HTTP_201_CREATED)
async def create_teaching_relation(payload: TeachingRelationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    relation = await teaching_relations_crud.create_teaching_relation(db, payload)
    return success_response(TeachingRelationResponse.model_validate(relation))


@teaching_router.get("")
async def list_teaching_relations(db: AsyncSession = Depends(get_db)) -> dict:
    relations = await teaching_relations_crud.list_teaching_relations(db)
    return success_response([TeachingRelationResponse.model_validate(item) for item in relations])


@enrollment_router.post("", status_code=status.HTTP_201_CREATED)
async def create_enrollment_relation(payload: EnrollmentRelationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    relation = await enrollment_relations_crud.create_enrollment_relation(db, payload)
    return success_response(EnrollmentRelationResponse.model_validate(relation))


@enrollment_router.get("")
async def list_enrollment_relations(db: AsyncSession = Depends(get_db)) -> dict:
    relations = await enrollment_relations_crud.list_enrollment_relations(db)
    return success_response([EnrollmentRelationResponse.model_validate(item) for item in relations])


router.include_router(courses_router)
router.include_router(chapters_router)
router.include_router(resources_router)
router.include_router(versions_router)
router.include_router(tags_router)
router.include_router(resource_tags_router)
router.include_router(teaching_router)
router.include_router(enrollment_router)
