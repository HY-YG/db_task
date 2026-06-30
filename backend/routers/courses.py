"""提供课程、章节、资源、标签、授课与选课等课程域接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import (
    assignments_crud,
    course_chapters_crud,
    course_resources_crud,
    courses_crud,
    enrollment_relations_crud,
    learning_progress_crud,
    notes_crud,
    resource_tags_crud,
    resource_versions_crud,
    tags_crud,
    teaching_relations_crud,
    users_crud,
)
from backend.models.assignments_mod import Assignment
from backend.models.course_chapters_mod import CourseChapter
from backend.models.course_resources_mod import CourseResource
from backend.models.courses_mod import Course
from backend.models.enrollment_relations_mod import EnrollmentRelation
from backend.models.learning_progress_mod import LearningProgress
from backend.schemas.assignments_sch import AssignmentResponse
from backend.schemas.course_chapters_sch import CourseChapterCreate, CourseChapterResponse, CourseChapterUpdate
from backend.schemas.course_resources_sch import CourseResourceCreate, CourseResourceResponse, CourseResourceUpdate
from backend.schemas.courses_sch import CourseCreate, CourseResponse, CourseUpdate
from backend.schemas.course_views_sch import (
    CourseDetailBundleResponse,
    CourseManagementBundleResponse,
    CourseOverviewItem,
    CourseOverviewResponse,
)
from backend.schemas.enrollment_relations_sch import EnrollmentRelationCreate, EnrollmentRelationResponse
from backend.schemas.learning_progress_sch import LearningProgressResponse
from backend.schemas.notes_sch import NoteResponse
from backend.schemas.resource_tags_sch import ResourceTagCreate, ResourceTagResponse
from backend.schemas.resource_versions_sch import ResourceVersionCreate, ResourceVersionResponse, ResourceVersionUpdate
from backend.schemas.tags_sch import TagCreate, TagResponse, TagUpdate
from backend.schemas.teaching_relations_sch import TeachingRelationCreate, TeachingRelationResponse
from backend.utils.response import success_response

router = APIRouter(tags=["courses"])

courses_router = APIRouter(prefix="/course", tags=["courses"])
chapters_router = APIRouter(prefix="/course/chapter", tags=["course_chapters"])
resources_router = APIRouter(prefix="/course/resource", tags=["course_resources"])
versions_router = APIRouter(prefix="/course/resource/version", tags=["resource_versions"])
tags_router = APIRouter(prefix="/course/tag", tags=["tags"])
resource_tags_router = APIRouter(prefix="/course/resource/tag", tags=["resource_tags"])
teaching_router = APIRouter(prefix="/course/teaching", tags=["teaching_relations"])
enrollment_router = APIRouter(prefix="/course/enrollment", tags=["enrollment_relations"])


@courses_router.post("/add")
async def create_course(payload: CourseCreate, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.create_course(db, payload)
    if payload.teacher_user_id is not None:
        # 新建课程时顺手补齐教师授课关系，避免教师端课程列表拿不到这门课。
        teacher = await users_crud.get_user(db, payload.teacher_user_id)
        if teacher is not None and teacher.role_id == 2:
            await teaching_relations_crud.create_teaching_relation(
                db,
                TeachingRelationCreate(
                    user_id=payload.teacher_user_id,
                    course_id=course.course_id,
                ),
            )
    return success_response(CourseResponse.model_validate(course))


@courses_router.get("/list")
async def list_courses(db: AsyncSession = Depends(get_db)) -> dict:
    courses = await courses_crud.list_courses(db)
    return success_response([CourseResponse.model_validate(item) for item in courses])


@courses_router.get("/detail/{course_id}")
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return success_response(CourseResponse.model_validate(course))


@courses_router.get("/overview/{user_id}")
async def get_course_overview(user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    # 概览页一次性聚合章节、资源、作业、选课和进度，前端只需一次请求即可完成首页渲染。
    chapter_counts_sq = (
        select(CourseChapter.course_id.label("course_id"), func.count(CourseChapter.chapter_id).label("chapter_count"))
        .group_by(CourseChapter.course_id)
        .subquery()
    )
    resource_counts_sq = (
        select(CourseChapter.course_id.label("course_id"), func.count(CourseResource.resource_id).label("resource_count"))
        .join(CourseResource, CourseResource.chapter_id == CourseChapter.chapter_id, isouter=True)
        .group_by(CourseChapter.course_id)
        .subquery()
    )
    assignment_counts_sq = (
        select(Assignment.course_id.label("course_id"), func.count(Assignment.assignment_id).label("assignment_count"))
        .group_by(Assignment.course_id)
        .subquery()
    )
    enrollment_sq = (
        select(
            EnrollmentRelation.course_id.label("course_id"),
            EnrollmentRelation.enrollment_status.label("enrollment_status"),
        )
        .where(EnrollmentRelation.user_id == user_id)
        .subquery()
    )
    progress_sq = (
        select(
            LearningProgress.course_id.label("course_id"),
            func.count(LearningProgress.progress_id).label("completed_count"),
        )
        .where(
            LearningProgress.user_id == user_id,
            LearningProgress.progress_status == "已完成",
        )
        .group_by(LearningProgress.course_id)
        .subquery()
    )

    stmt = (
        select(
            Course,
            func.coalesce(chapter_counts_sq.c.chapter_count, 0).label("chapter_count"),
            func.coalesce(resource_counts_sq.c.resource_count, 0).label("resource_count"),
            func.coalesce(assignment_counts_sq.c.assignment_count, 0).label("assignment_count"),
            enrollment_sq.c.enrollment_status.label("enrollment_status"),
            func.coalesce(progress_sq.c.completed_count, 0).label("completed_count"),
        )
        .outerjoin(chapter_counts_sq, chapter_counts_sq.c.course_id == Course.course_id)
        .outerjoin(resource_counts_sq, resource_counts_sq.c.course_id == Course.course_id)
        .outerjoin(assignment_counts_sq, assignment_counts_sq.c.course_id == Course.course_id)
        .outerjoin(enrollment_sq, enrollment_sq.c.course_id == Course.course_id)
        .outerjoin(progress_sq, progress_sq.c.course_id == Course.course_id)
        .order_by(Course.course_id)
    )
    rows = (await db.execute(stmt)).all()

    items: list[CourseOverviewItem] = []
    for course, chapter_count, resource_count, assignment_count, enrollment_status, completed_count in rows:
        # 课程总进度按“章节 + 资源 + 作业”三个维度统一折算，便于前端展示单一百分比。
        total_items = int(chapter_count) + int(resource_count) + int(assignment_count)
        progress_percent = round((int(completed_count) / total_items) * 100, 1) if total_items else 0.0
        items.append(
            CourseOverviewItem(
                course=CourseResponse.model_validate(course),
                chapter_count=int(chapter_count),
                resource_count=int(resource_count),
                assignment_count=int(assignment_count),
                progress_percent=progress_percent,
                is_enrolled=enrollment_status is not None,
                enrollment_status=enrollment_status,
            )
        )
    return success_response(CourseOverviewResponse(items=items))


@courses_router.get("/detail-bundle/{course_id}")
async def get_course_detail_bundle(
    course_id: int,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollments = await enrollment_relations_crud.list_enrollment_relations(db, user_id=user_id, course_id=course_id)
    chapters = await course_chapters_crud.list_chapters(db, course_id=course_id)
    resources = await course_resources_crud.list_resources_by_course(db, course_id=course_id)
    assignments = await assignments_crud.list_assignments(db, course_id=course_id)
    notes = await notes_crud.list_recent_notes(db, user_id=user_id, course_id=course_id, limit=5)
    progress_items = await learning_progress_crud.list_progress(db, user_id=user_id, course_id=course_id)

    return success_response(
        CourseDetailBundleResponse(
            course=CourseResponse.model_validate(course),
            enrollment=EnrollmentRelationResponse.model_validate(enrollments[0]) if enrollments else None,
            chapters=[CourseChapterResponse.model_validate(item) for item in chapters],
            resources=[CourseResourceResponse.model_validate(item) for item in resources],
            assignments=[AssignmentResponse.model_validate(item) for item in assignments],
            notes=[NoteResponse.model_validate(item) for item in notes],
            progress_items=[LearningProgressResponse.model_validate(item) for item in progress_items],
        )
    )


@courses_router.get("/management-bundle")
async def get_course_management_bundle(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    courses = await courses_crud.list_courses(db)
    chapters = await course_chapters_crud.list_chapters(db)
    resources = await course_resources_crud.list_resources(db)

    if user_id is not None:
        # 教师只应看到自己负责的课程、章节和资源，管理员则可查看全部内容。
        teaching_relations = await teaching_relations_crud.list_teaching_relations(db, user_id=user_id)
        allowed_course_ids = {item.course_id for item in teaching_relations}
        courses = [item for item in courses if item.course_id in allowed_course_ids]
        chapters = [item for item in chapters if item.course_id in allowed_course_ids]
        allowed_chapter_ids = {item.chapter_id for item in chapters}
        resources = [item for item in resources if item.chapter_id in allowed_chapter_ids]

    return success_response(
        CourseManagementBundleResponse(
            courses=[CourseResponse.model_validate(item) for item in courses],
            chapters=[CourseChapterResponse.model_validate(item) for item in chapters],
            resources=[CourseResourceResponse.model_validate(item) for item in resources],
        )
    )


@courses_router.put("/update/{course_id}")
async def update_course(course_id: int, payload: CourseUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    course = await courses_crud.update_course(db, course, payload)
    return success_response(CourseResponse.model_validate(course))


@courses_router.delete("/delete/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    await courses_crud.delete_course(db, course)
    return success_response()


@chapters_router.post("/add")
async def create_chapter(payload: CourseChapterCreate, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.create_chapter(db, payload)
    return success_response(CourseChapterResponse.model_validate(chapter))


@chapters_router.get("/list")
async def list_chapters(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    chapters = await course_chapters_crud.list_chapters(db, course_id=course_id)
    return success_response([CourseChapterResponse.model_validate(item) for item in chapters])


@chapters_router.get("/detail/{chapter_id}")
async def get_chapter(chapter_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return success_response(CourseChapterResponse.model_validate(chapter))


@chapters_router.put("/update/{chapter_id}")
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


@chapters_router.delete("/delete/{chapter_id}")
async def delete_chapter(chapter_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    chapter = await course_chapters_crud.get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    await course_chapters_crud.delete_chapter(db, chapter)
    return success_response()


@resources_router.post("/add")
async def create_resource(payload: CourseResourceCreate, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.create_resource(db, payload)
    return success_response(CourseResourceResponse.model_validate(resource))


@resources_router.get("/list")
async def list_resources(
    chapter_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    resources = await course_resources_crud.list_resources(db, chapter_id=chapter_id)
    return success_response([CourseResourceResponse.model_validate(item) for item in resources])


@resources_router.get("/detail/{resource_id}")
async def get_resource(resource_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return success_response(CourseResourceResponse.model_validate(resource))


@resources_router.put("/update/{resource_id}")
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


@resources_router.delete("/delete/{resource_id}")
async def delete_resource(resource_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    resource = await course_resources_crud.get_resource(db, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    await course_resources_crud.delete_resource(db, resource)
    return success_response()


@versions_router.post("/add")
async def create_version(payload: ResourceVersionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.create_version(db, payload)
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.get("/list")
async def list_versions(
    resource_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    versions = await resource_versions_crud.list_versions(db, resource_id=resource_id)
    return success_response([ResourceVersionResponse.model_validate(item) for item in versions])


@versions_router.get("/detail/{version_id}")
async def get_version(version_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.put("/update/{version_id}")
async def update_version(version_id: int, payload: ResourceVersionUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    version = await resource_versions_crud.update_version(db, version, payload)
    return success_response(ResourceVersionResponse.model_validate(version))


@versions_router.delete("/delete/{version_id}")
async def delete_version(version_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    version = await resource_versions_crud.get_version(db, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Resource version not found")
    await resource_versions_crud.delete_version(db, version)
    return success_response()


@tags_router.post("/add")
async def create_tag(payload: TagCreate, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.create_tag(db, payload)
    return success_response(TagResponse.model_validate(tag))


@tags_router.get("/list")
async def list_tags(db: AsyncSession = Depends(get_db)) -> dict:
    tags = await tags_crud.list_tags(db)
    return success_response([TagResponse.model_validate(item) for item in tags])


@tags_router.get("/detail/{tag_id}")
async def get_tag(tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return success_response(TagResponse.model_validate(tag))


@tags_router.put("/update/{tag_id}")
async def update_tag(tag_id: int, payload: TagUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    tag = await tags_crud.update_tag(db, tag, payload)
    return success_response(TagResponse.model_validate(tag))


@tags_router.delete("/delete/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    tag = await tags_crud.get_tag(db, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    await tags_crud.delete_tag(db, tag)
    return success_response()


@resource_tags_router.post("/add")
async def create_resource_tag(payload: ResourceTagCreate, db: AsyncSession = Depends(get_db)) -> dict:
    rel = await resource_tags_crud.create_resource_tag(db, payload)
    return success_response(ResourceTagResponse.model_validate(rel))


@resource_tags_router.get("/list")
async def list_resource_tags(
    resource_id: int | None = Query(default=None),
    tag_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    relations = await resource_tags_crud.list_resource_tags(db, resource_id=resource_id, tag_id=tag_id)
    return success_response([ResourceTagResponse.model_validate(item) for item in relations])


@resource_tags_router.delete("/delete")
async def delete_resource_tag(resource_id: int, tag_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await resource_tags_crud.delete_resource_tag(db, resource_id=resource_id, tag_id=tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Resource tag relation not found")
    return success_response()


@teaching_router.post("/add")
async def create_teaching_relation(payload: TeachingRelationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    relation = await teaching_relations_crud.create_teaching_relation(db, payload)
    return success_response(TeachingRelationResponse.model_validate(relation))


@teaching_router.get("/list")
async def list_teaching_relations(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    relations = await teaching_relations_crud.list_teaching_relations(db, user_id=user_id)
    return success_response([TeachingRelationResponse.model_validate(item) for item in relations])


@enrollment_router.post("/add")
async def create_enrollment_relation(payload: EnrollmentRelationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    relation = await enrollment_relations_crud.create_enrollment_relation(db, payload)
    return success_response(EnrollmentRelationResponse.model_validate(relation))


@enrollment_router.get("/list")
async def list_enrollment_relations(
    user_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    relations = await enrollment_relations_crud.list_enrollment_relations(db, user_id=user_id, course_id=course_id)
    return success_response([EnrollmentRelationResponse.model_validate(item) for item in relations])


router.include_router(courses_router)
router.include_router(chapters_router)
router.include_router(resources_router)
router.include_router(versions_router)
router.include_router(tags_router)
router.include_router(resource_tags_router)
router.include_router(teaching_router)
router.include_router(enrollment_router)
