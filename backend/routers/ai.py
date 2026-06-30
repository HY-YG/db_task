"""提供 AI 会话、消息、上传与统一助手对话相关接口。"""

import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import ai_crud
from backend.schemas.ai_sch import (
    AiAssistantChatRequest,
    AiAssistantChatResponse,
    AiChatRequest,
    AiChatResponse,
    AiCoachNextRequest,
    AiCoachNextResponse,
    AiCoachStartRequest,
    AiCoachStartResponse,
    AiMessageCreate,
    AiMessageResponse,
    AiQaRequest,
    AiQaResponse,
    AiSessionCreate,
    AiSessionResponse,
    AiSessionUpdate,
    AiVectorizeRequest,
    AiVectorizeResponse,
)
from backend.services import assistant_orchestrator, chat_agent, coach_agent, qa_agent, upload_agent, vectorize_agent
from backend.utils.response import success_response

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/session/add")
async def create_session(payload: AiSessionCreate, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.create_session(db, payload)
    return success_response(AiSessionResponse.model_validate(session))


@router.get("/session/list")
async def list_sessions(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    sessions = await ai_crud.list_sessions(db, user_id=user_id)
    return success_response([AiSessionResponse.model_validate(item) for item in sessions])


@router.put("/session/update/{session_id}")
async def update_session(session_id: int, payload: AiSessionUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session = await ai_crud.update_session(db, session, payload)
    return success_response(AiSessionResponse.model_validate(session))


@router.post("/message/add")
async def create_message(payload: AiMessageCreate, db: AsyncSession = Depends(get_db)) -> dict:
    message = await ai_crud.create_message(db, payload)
    return success_response(AiMessageResponse.model_validate(message))


@router.get("/message/list")
async def list_messages(
    session_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    messages = await ai_crud.list_messages(db, session_id=session_id)
    return success_response([AiMessageResponse.model_validate(item) for item in messages])


@router.delete("/session/delete/{session_id}")
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return success_response()


@router.post("/coach/start")
async def coach_start(payload: AiCoachStartRequest, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.get_session(db, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != payload.user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    stage = await coach_agent.handle_start(db=db, session=session, course_id=payload.course_id)
    return success_response(AiCoachStartResponse(session_id=session.session_id, stage=stage))


@router.post("/coach/next")
async def coach_next(payload: AiCoachNextRequest, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.get_session(db, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != payload.user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if session.session_status not in {"coach_diagnose", "coach_plan", "coach_execute", "coach_done"}:
        raise HTTPException(status_code=400, detail="Session is not in coach flow")

    if session.session_status == "coach_done":
        return success_response(
            AiCoachNextResponse(
                session_id=session.session_id,
                stage=session.session_status,
                assistant_message="这一轮学习计划已经完成了。你可以回顾本轮收获，或者重新开启下一轮教练流程。",
                next_stage="coach_done",
            )
        )

    if session.session_status == "coach_diagnose":
        diagnose_result = await coach_agent.handle_diagnose(
            db=db,
            session=session,
            message=payload.message,
        )
        return success_response(AiCoachNextResponse(**diagnose_result.to_response_payload()))

    if session.session_status == "coach_plan":
        plan_result = await coach_agent.handle_plan(db=db, session=session)
        return success_response(AiCoachNextResponse(**plan_result.to_response_payload()))

    if session.session_status == "coach_execute":
        execute_result = await coach_agent.handle_execute(
            db=db,
            session=session,
            message=payload.message,
        )
        return success_response(AiCoachNextResponse(**execute_result.to_response_payload()))

    raise HTTPException(status_code=400, detail="Unsupported coach stage")


@router.post("/upload")
async def upload_resource(
    chapter_id: int = Form(...),
    file: UploadFile = File(...),
    resource_title: str | None = Form(default=None),
    version_description: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await upload_agent.handle_upload(
        db=db,
        chapter_id=chapter_id,
        file=file,
        resource_title=resource_title,
        version_description=version_description,
    )
    return success_response(result)


@router.post("/vectorize")
async def vectorize(payload: AiVectorizeRequest, db: AsyncSession = Depends(get_db)) -> dict:
    result = await vectorize_agent.handle_vectorize(db=db, resource_id=payload.resource_id)
    return success_response(AiVectorizeResponse(**result.to_response_payload()))


@router.post("/qa")
async def qa(payload: AiQaRequest, db: AsyncSession = Depends(get_db)) -> dict:
    answer, contexts = await qa_agent.handle_qa(
        db=db,
        question=payload.question,
        course_id=payload.course_id,
        top_k=payload.top_k,
    )

    if payload.session_id is not None:
        await ai_crud.create_message(
            db,
            AiMessageCreate(session_id=payload.session_id, sender="user", message_content={"type": "text", "text": payload.question}),
        )
        await ai_crud.create_message(
            db,
            AiMessageCreate(session_id=payload.session_id, sender="ai", message_content={"type": "text", "text": answer}),
        )

    return success_response(AiQaResponse(answer=answer, contexts=contexts))


@router.post("/chat")
async def chat(payload: AiChatRequest, db: AsyncSession = Depends(get_db)) -> dict:
    await ai_crud.create_message(
        db,
        AiMessageCreate(session_id=payload.session_id, sender="user", message_content={"type": "text", "text": payload.message}),
    )
    answer, tool_name, tool_result, contexts = await chat_agent.handle_chat(
        db=db,
        session_id=payload.session_id,
        user_id=payload.user_id,
        message=payload.message,
        course_id=payload.course_id,
        top_k=payload.top_k,
    )

    await ai_crud.create_message(
        db,
        AiMessageCreate(session_id=payload.session_id, sender="ai", message_content={"type": "text", "text": answer}),
    )
    return success_response(
        AiChatResponse(answer=answer, tool_name=tool_name, tool_result=tool_result, contexts=contexts)
    )


@router.post("/assistant/chat")
async def assistant_chat(payload: AiAssistantChatRequest, db: AsyncSession = Depends(get_db)) -> dict:
    session = await ai_crud.get_session(db, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != payload.user_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    result = await assistant_orchestrator.handle_assistant_chat(
        db=db,
        session=session,
        user_id=payload.user_id,
        message=payload.message,
        course_id=payload.course_id,
        top_k=payload.top_k,
        confirm_personal_context=payload.confirm_personal_context,
    )
    return success_response(AiAssistantChatResponse(**result.to_response_payload()))
