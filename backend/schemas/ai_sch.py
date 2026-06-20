from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class AiSessionCreate(ORMModel):
    user_id: int
    session_status: str = Field(default="进行中", max_length=20)


class AiSessionUpdate(ORMModel):
    session_status: str | None = Field(default=None, max_length=20)


class AiSessionResponse(ORMModel):
    session_id: int
    user_id: int
    session_status: str
    started_at: datetime


class AiMessageCreate(ORMModel):
    session_id: int
    sender: str = Field(..., max_length=20)
    message_content: dict


class AiMessageResponse(ORMModel):
    message_id: int
    session_id: int
    sender: str
    message_content: dict
    sent_at: datetime


class AiQaRequest(ORMModel):
    question: str
    user_id: int | None = None
    course_id: int | None = None
    session_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class AiQaContext(ORMModel):
    resource_id: int
    chunk_id: int
    content: str
    score: float


class AiQaResponse(ORMModel):
    answer: str
    contexts: list[AiQaContext] = Field(default_factory=list)


class AiChatRequest(ORMModel):
    session_id: int
    user_id: int
    message: str
    course_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class AiChatResponse(ORMModel):
    answer: str
    tool_name: str | None = None
    tool_result: dict | None = None
    contexts: list[AiQaContext] = Field(default_factory=list)


class AiVectorizeRequest(ORMModel):
    resource_id: int


class AiVectorizeResponse(ORMModel):
    resource_id: int
    chunk_count: int
    vectorized: bool = True
    message: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)


class AiCoachStartRequest(ORMModel):
    session_id: int
    user_id: int
    course_id: int


class AiCoachStartResponse(ORMModel):
    session_id: int
    stage: str


class AiCoachNextRequest(ORMModel):
    session_id: int
    user_id: int
    message: str | None = None


class AiCoachNextResponse(ORMModel):
    session_id: int
    stage: str
    assistant_message: str
    questions: list[str] = Field(default_factory=list)
    diagnosis_summary: str | None = None
    plan_id: int | None = None
    study_plan: str | None = None
    execution_feedback: str | None = None
    next_stage: str | None = None
