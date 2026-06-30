"""处理课程资源切片向量化与向量索引写入流程。"""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course_resources_mod import CourseResource
from backend.services import rag


def build_suggested_questions(*, resource_title: str, chunk_count: int) -> list[str]:
    title = resource_title or "这份资料"
    questions = [
        f"{title} 主要讲了哪些知识点？",
        f"请结合 {title} 帮我总结 3 个最重要的概念。",
        f"基于 {title} 给我出 3 个由浅入深的练习问题。",
    ]
    if chunk_count > 0:
        questions.append(f"如果我要快速复习 {title}，应该先看哪几个重点片段？")
    return questions


@dataclass
class VectorizeResult:
    resource_id: int
    chunk_count: int
    vectorized: bool
    message: str
    suggested_questions: list[str]

    def to_response_payload(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "chunk_count": self.chunk_count,
            "vectorized": self.vectorized,
            "message": self.message,
            "suggested_questions": self.suggested_questions,
        }


async def handle_vectorize(*, db: AsyncSession, resource_id: int) -> VectorizeResult:
    resource = await db.get(CourseResource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    can_vectorize, reason = rag.can_vectorize_resource(resource)
    if not can_vectorize:
        return VectorizeResult(
            resource_id=resource_id,
            chunk_count=0,
            vectorized=False,
            message=reason or "当前资源不支持自动向量化。",
            suggested_questions=[],
        )

    chunk_count = await rag.vectorize_resource(db, resource_id=resource_id)
    if chunk_count == 0:
        return VectorizeResult(
            resource_id=resource_id,
            chunk_count=0,
            vectorized=False,
            message="资源已读取，但没有提取到可用于切块的有效文本。",
            suggested_questions=[],
        )

    return VectorizeResult(
        resource_id=resource_id,
        chunk_count=chunk_count,
        vectorized=True,
        message=f"资源已完成向量化，共生成 {chunk_count} 个切片。",
        suggested_questions=build_suggested_questions(
            resource_title=resource.resource_title,
            chunk_count=chunk_count,
        ),
    )
