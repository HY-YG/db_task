import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import ai_crud
from backend.schemas.ai_sch import AiMessageCreate
from backend.services import chat_agent, coach_agent, memory_service, qa_agent
from backend.services.langchain_utils import invoke_chat_model_text

COACH_STATUSES = {"coach_diagnose", "coach_plan", "coach_execute", "coach_done"}
RECENT_HISTORY_LIMIT = 6
SUMMARY_TRIGGER_COUNT = 8
SUMMARY_BATCH_COUNT = 6
PERSONAL_CONTEXT_KEYWORDS = (
    "我的情况",
    "我的学习情况",
    "根据我的",
    "帮我分析",
    "哪里掌握不好",
    "哪些地方薄弱",
    "我的笔记",
    "我的计划",
    "我的作业",
    "我的进度",
)
COACH_REQUEST_KEYWORDS = (
    "制定计划",
    "学习计划",
    "诊断",
    "薄弱点",
    "学习教练",
    "长期辅导",
    "带我学",
    "监督我",
)
QA_HINT_KEYWORDS = ("什么是", "解释", "区别", "原理", "概念", "为什么", "如何理解")
PERMISSION_CONFIRM_WORDS = {"同意", "可以", "确认", "继续", "允许", "授权", "好", "好的", "行"}


@dataclass
class AssistantOrchestratorResult:
    answer: str
    mode: str
    tool_name: str | None = None
    tool_result: dict | None = None
    contexts: list[dict] | None = None
    permission_required: bool = False
    permission_reason: str | None = None
    coach_stage: str | None = None

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "mode": self.mode,
            "tool_name": self.tool_name,
            "tool_result": self.tool_result,
            "contexts": self.contexts or [],
            "permission_required": self.permission_required,
            "permission_reason": self.permission_reason,
            "coach_stage": self.coach_stage,
        }


@dataclass
class RouteDecision:
    intent: str
    needs_rag: bool
    needs_personal_context: bool
    suggest_coach: bool
    reason: str


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _needs_personal_context(text: str) -> bool:
    return _contains_any(text, PERSONAL_CONTEXT_KEYWORDS)


def _looks_like_coach_request(text: str) -> bool:
    return _contains_any(text, COACH_REQUEST_KEYWORDS)


def _prefer_qa_mode(text: str, course_id: int | None) -> bool:
    return course_id is not None and _contains_any(text, QA_HINT_KEYWORDS)


def _looks_like_permission_confirmation(text: str) -> bool:
    normalized = text.strip().replace("。", "").replace("，", "").replace("！", "").replace("!", "")
    return normalized in PERMISSION_CONFIRM_WORDS


def _parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        data = json.loads(stripped)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _history_role_from_message(sender: str, message_type: str) -> str | None:
    if sender == "user" and message_type in {"assistant_user", "assistant_permission_confirm"}:
        return "user"
    if sender == "ai" and message_type in {
        "assistant_answer",
        "assistant_permission_request",
        "assistant_coach_suggestion",
        "assistant_coach_started",
    }:
        return "assistant"
    return None


def _normalize_route_decision(data: dict[str, Any]) -> RouteDecision | None:
    intent = data.get("intent")
    if intent not in {"general", "course_qa", "personal_analysis", "coach_request"}:
        return None
    return RouteDecision(
        intent=intent,
        needs_rag=bool(data.get("needs_rag", False)),
        needs_personal_context=bool(data.get("needs_personal_context", False)),
        suggest_coach=bool(data.get("suggest_coach", False)),
        reason=str(data.get("reason", "")).strip(),
    )


def _route_by_rules(text: str, course_id: int | None) -> RouteDecision:
    needs_personal_context = _needs_personal_context(text)
    suggest_coach = _looks_like_coach_request(text)
    if suggest_coach:
        intent = "coach_request"
    elif needs_personal_context:
        intent = "personal_analysis"
    elif _prefer_qa_mode(text, course_id):
        intent = "course_qa"
    else:
        intent = "general"
    return RouteDecision(
        intent=intent,
        needs_rag=intent == "course_qa",
        needs_personal_context=needs_personal_context,
        suggest_coach=suggest_coach,
        reason="fallback_rule_router",
    )


async def _get_recent_assistant_history(
    db: AsyncSession,
    *,
    session_id: int,
    limit: int = RECENT_HISTORY_LIMIT,
) -> list[dict[str, str]]:
    messages = await ai_crud.list_messages(db, session_id=session_id)
    history: list[dict[str, str]] = []
    for item in reversed(messages):
        payload = item.message_content
        if not isinstance(payload, dict):
            continue
        message_type = payload.get("type")
        text = payload.get("text")
        if not isinstance(message_type, str) or not isinstance(text, str) or not text.strip():
            continue
        role = _history_role_from_message(item.sender, message_type)
        if role is None:
            continue
        history.append({"role": role, "content": text.strip()})
        if len(history) >= limit:
            break
    history.reverse()
    return history


async def _get_effective_assistant_dialogue(
    db: AsyncSession,
    *,
    session_id: int,
) -> list[dict[str, Any]]:
    messages = await ai_crud.list_messages(db, session_id=session_id)
    dialogue: list[dict[str, Any]] = []
    for item in messages:
        payload = item.message_content
        if not isinstance(payload, dict):
            continue
        message_type = payload.get("type")
        text = payload.get("text")
        if not isinstance(message_type, str) or not isinstance(text, str) or not text.strip():
            continue
        role = _history_role_from_message(item.sender, message_type)
        if role is None:
            continue
        dialogue.append(
            {
                "message_id": item.message_id,
                "role": role,
                "content": text.strip(),
                "type": message_type,
            }
        )
    return dialogue


def _format_recent_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "无"
    lines = []
    for item in history:
        role = "用户" if item["role"] == "user" else "助手"
        lines.append(f"{role}: {item['content']}")
    return "\n".join(lines)


def _format_memory_contexts(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return "无"
    lines = []
    for index, item in enumerate(memories, start=1):
        lines.append(f"[记忆{index}] 摘要: {item.get('summary_text', '')}")
        topics = item.get("topics", [])
        weak_points = item.get("weak_points", [])
        goals = item.get("goals", [])
        next_actions = item.get("next_actions", [])
        if topics:
            lines.append(f"主题: {', '.join([str(topic) for topic in topics])}")
        if weak_points:
            lines.append(f"薄弱点: {', '.join([str(point) for point in weak_points])}")
        if goals:
            lines.append(f"目标: {', '.join([str(goal) for goal in goals])}")
        if next_actions:
            lines.append(f"下一步: {', '.join([str(action) for action in next_actions])}")
    return "\n".join(lines)


async def _maybe_store_dialogue_summary(
    *,
    db: AsyncSession,
    session_id: int,
    user_id: int,
    course_id: int | None,
) -> None:
    memories = await memory_service.list_relevant_memories(
        db=db,
        user_id=user_id,
        session_id=session_id,
        course_id=course_id,
        memory_kind="dialogue_summary",
        limit=1,
    )
    covered_until_message_id = 0
    if memories:
        covered_until_message_id = int(memories[0].memory_meta.get("covered_until_message_id", 0) or 0)

    dialogue = await _get_effective_assistant_dialogue(db, session_id=session_id)
    pending_items = [item for item in dialogue if int(item["message_id"]) > covered_until_message_id]
    if len(pending_items) < SUMMARY_TRIGGER_COUNT:
        return

    summary_items = pending_items[:SUMMARY_BATCH_COUNT]
    history = [{"role": str(item["role"]), "content": str(item["content"])} for item in summary_items]
    await memory_service.summarize_history_to_memory(
        db=db,
        session_id=session_id,
        user_id=user_id,
        course_id=course_id,
        history=history,
        memory_kind="dialogue_summary",
        extra_meta={
            "covered_until_message_id": int(summary_items[-1]["message_id"]),
            "source_message_ids": [int(item["message_id"]) for item in summary_items],
        },
    )


async def _route_with_llm(
    *,
    text: str,
    course_id: int | None,
    recent_history: list[dict[str, str]] | None = None,
    memory_contexts: list[dict[str, Any]] | None = None,
) -> RouteDecision:
    system_prompt = (
        "你是 AI 助手系统中的路由器，只负责判断用户意图，不负责回答业务内容。\n"
        "请根据用户输入，输出一个 JSON 对象，不要输出任何额外解释，不要使用 Markdown。\n"
        "你只能从以下 intent 中选择一个：\n"
        '1. "general": 普通闲聊、泛知识、与课程无强相关的随意对话。\n'
        '2. "course_qa": 与课程知识点、术语、概念、原理、用途、区别有关的问题，适合优先结合课程资料回答。\n'
        '3. "personal_analysis": 用户希望结合自己的笔记、计划、作业、进度来分析自己的学习情况。\n'
        '4. "coach_request": 用户希望得到持续跟进式的学习辅导、诊断、制定计划、监督执行。\n'
        "你还要输出以下字段：\n"
        '- "needs_rag": 是否建议优先检索课程资料。\n'
        '- "needs_personal_context": 是否需要读取用户个人学习资料。\n'
        '- "suggest_coach": 是否建议进入学习教练流程。\n'
        '- "reason": 用一句中文简要说明判断依据。\n'
        "判断原则：\n"
        "1. 像“XXX是什么”“XXX有什么用”“你知道XXX吗”这类问题，如果明显在问概念、定义、用途或原理，通常归类为 course_qa。\n"
        "2. 只有在确实需要用户个人学习信息时，才把 needs_personal_context 设为 true。\n"
        "3. 只有在用户明确表现出长期辅导、诊断、制定计划、持续跟进需求时，才把 suggest_coach 设为 true。\n"
        "4. 如果 course_id 为空，仍然可以判断 intent，但对 needs_rag 要更保守。\n"
        '最终只输出形如 {"intent":"course_qa","needs_rag":true,"needs_personal_context":false,"suggest_coach":false,"reason":"..."} 的 JSON。'
    )
    history_text = _format_recent_history(recent_history or [])
    memory_text = _format_memory_contexts(memory_contexts or [])
    user_content = (
        f"course_id={course_id}\n"
        f"最近几轮对话：\n{history_text}\n\n"
        f"相关摘要记忆：\n{memory_text}\n\n"
        f"用户当前消息：{text}"
    )
    raw = await invoke_chat_model_text(system_prompt=system_prompt, user_content=user_content, temperature=0)
    if raw is None:
        return _route_by_rules(text, course_id)
    parsed = _parse_json_object(raw)
    if parsed is None:
        return _route_by_rules(text, course_id)
    decision = _normalize_route_decision(parsed)
    if decision is None:
        return _route_by_rules(text, course_id)
    return decision


def _build_coach_answer(
    *,
    assistant_message: str,
    questions: list[str] | None = None,
    diagnosis_summary: str | None = None,
    study_plan: str | None = None,
    execution_feedback: str | None = None,
) -> str:
    parts = [assistant_message]
    if questions:
        numbered = "\n".join([f"{index + 1}. {question}" for index, question in enumerate(questions)])
        parts.append(numbered)
    if diagnosis_summary:
        parts.append(f"诊断总结：\n{diagnosis_summary}")
    if study_plan:
        parts.append(f"学习计划：\n{study_plan}")
    if execution_feedback:
        parts.append(f"执行建议：\n{execution_feedback}")
    return "\n\n".join([part for part in parts if part])


async def _save_user_message(db: AsyncSession, session_id: int, message: str) -> None:
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session_id,
            sender="user",
            message_content={"type": "assistant_user", "text": message},
        ),
    )


async def _save_custom_user_message(db: AsyncSession, *, session_id: int, message_type: str, message: str) -> None:
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session_id,
            sender="user",
            message_content={"type": message_type, "text": message},
        ),
    )


async def _save_ai_message(
    db: AsyncSession,
    *,
    session_id: int,
    message_type: str,
    answer: str,
    mode: str,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {"type": message_type, "text": answer, "mode": mode}
    if extra:
        payload.update(extra)
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session_id,
            sender="ai",
            message_content=payload,
        ),
    )


async def _get_latest_pending_permission_context(
    db: AsyncSession,
    *,
    session_id: int,
) -> tuple[str, int | None, RouteDecision] | None:
    permission_message = await ai_crud.get_latest_ai_message_json(
        db,
        session_id=session_id,
        message_type="assistant_permission_request",
    )
    if permission_message is None:
        return None

    content = permission_message.message_content
    pending_user_message = content.get("pending_user_message")
    pending_course_id = content.get("pending_course_id")
    if not isinstance(pending_user_message, str) or not pending_user_message.strip():
        messages = await ai_crud.list_messages(db, session_id=session_id)
        for item in reversed(messages):
            payload = item.message_content
            if item.sender == "user" and payload.get("type") == "assistant_user":
                pending_user_message = payload.get("text")
                break
    if not isinstance(pending_user_message, str) or not pending_user_message.strip():
        return None

    cached_decision = _normalize_route_decision(
        {
            "intent": content.get("pending_intent"),
            "needs_rag": content.get("pending_needs_rag", False),
            "needs_personal_context": content.get("pending_needs_personal_context", True),
            "suggest_coach": content.get("pending_suggest_coach", False),
            "reason": content.get("router_reason", "resume_from_permission_request"),
        }
    )
    if cached_decision is None:
        cached_decision = await _route_with_llm(text=pending_user_message.strip(), course_id=pending_course_id)
    return pending_user_message.strip(), pending_course_id, cached_decision


async def _handle_active_coach_flow(
    *,
    db: AsyncSession,
    session: Any,
    message: str,
) -> AssistantOrchestratorResult:
    stripped = message.strip() or None
    if session.session_status == "coach_done":
        return AssistantOrchestratorResult(
            answer="这一轮学习计划已经完成了。你可以回顾本轮收获，或者重新开启下一轮教练流程。",
            mode="coach_active",
            coach_stage="coach_done",
        )

    if session.session_status == "coach_diagnose":
        result = await coach_agent.handle_diagnose(db=db, session=session, message=stripped)
        return AssistantOrchestratorResult(
            answer=_build_coach_answer(
                assistant_message=result.assistant_message,
                questions=result.questions,
                diagnosis_summary=result.diagnosis_summary,
            ),
            mode="coach_active",
            coach_stage=result.stage,
        )

    if session.session_status == "coach_plan":
        result = await coach_agent.handle_plan(db=db, session=session)
        return AssistantOrchestratorResult(
            answer=_build_coach_answer(
                assistant_message=result.assistant_message,
                study_plan=result.study_plan,
            ),
            mode="coach_active",
            coach_stage=result.stage,
        )

    result = await coach_agent.handle_execute(db=db, session=session, message=stripped)
    return AssistantOrchestratorResult(
        answer=_build_coach_answer(
            assistant_message=result.assistant_message,
            study_plan=result.study_plan,
            execution_feedback=result.execution_feedback,
        ),
        mode="coach_active",
        coach_stage=result.stage,
    )


async def _start_coach_flow(
    *,
    db: AsyncSession,
    session: Any,
    course_id: int,
) -> AssistantOrchestratorResult:
    stage = await coach_agent.handle_start(db=db, session=session, course_id=course_id)
    session = await ai_crud.get_session(db, session.session_id)
    if session is None:
        return AssistantOrchestratorResult(
            answer="学习教练流程启动失败，请稍后重试。",
            mode="coach_suggestion",
            coach_stage=None,
        )
    result = await coach_agent.handle_diagnose(db=db, session=session, message=None)
    return AssistantOrchestratorResult(
        answer=_build_coach_answer(
            assistant_message="我已经为你开启学习教练流程，先做第一轮能力诊断。",
            questions=result.questions,
        ),
        mode="coach_started",
        coach_stage=stage,
    )


async def handle_assistant_chat(
    *,
    db: AsyncSession,
    session: Any,
    user_id: int,
    message: str,
    course_id: int | None,
    top_k: int,
    confirm_personal_context: bool,
) -> AssistantOrchestratorResult:
    text = message.strip()
    recent_history = await _get_recent_assistant_history(db, session_id=session.session_id)
    resume_from_permission_request = False
    resumed_course_id = course_id
    resumed_decision: RouteDecision | None = None
    if confirm_personal_context and (not text or _looks_like_permission_confirmation(text)):
        await _save_custom_user_message(
            db,
            session_id=session.session_id,
            message_type="assistant_permission_confirm",
            message=text or "已确认授权",
        )
        pending = await _get_latest_pending_permission_context(db, session_id=session.session_id)
        if pending is None:
            return AssistantOrchestratorResult(
                answer="当前没有待继续的个性化分析请求。你可以直接告诉我你想分析什么，我会继续帮你处理。",
                mode="general",
            )
        text, resumed_course_id, resumed_decision = pending
        resume_from_permission_request = True

    if not text:
        return AssistantOrchestratorResult(answer="你可以直接告诉我你想聊什么，或你在课程里遇到了什么问题。", mode="general")

    if session.session_status in COACH_STATUSES:
        return await _handle_active_coach_flow(db=db, session=session, message=text)

    course_id = resumed_course_id
    memory_contexts = await memory_service.get_memory_contexts(
        db=db,
        user_id=user_id,
        session_id=session.session_id,
        course_id=course_id,
        question=text,
        limit=3,
    )
    decision = resumed_decision or await _route_with_llm(
        text=text,
        course_id=course_id,
        recent_history=recent_history,
        memory_contexts=memory_contexts,
    )

    if decision.needs_personal_context and not confirm_personal_context:
        answer = "要更准确地结合你的学习情况来分析，我需要先读取你的笔记、学习计划或作业完成情况。"
        await _save_user_message(db, session.session_id, text)
        await _save_ai_message(
            db,
            session_id=session.session_id,
            message_type="assistant_permission_request",
            answer=answer,
            mode="permission_request",
            extra={
                "permission_required": True,
                "permission_reason": "需要读取你的个人学习资料，才能进行更准确的个性化分析。",
                "router_reason": decision.reason,
                "pending_user_message": text,
                "pending_course_id": course_id,
                "pending_intent": decision.intent,
                "pending_needs_rag": decision.needs_rag,
                "pending_needs_personal_context": decision.needs_personal_context,
                "pending_suggest_coach": decision.suggest_coach,
            },
        )
        await _maybe_store_dialogue_summary(
            db=db,
            session_id=session.session_id,
            user_id=user_id,
            course_id=course_id,
        )
        return AssistantOrchestratorResult(
            answer=answer,
            mode="permission_request",
            permission_required=True,
            permission_reason="需要读取你的个人学习资料，才能进行更准确的个性化分析。",
        )

    if decision.suggest_coach or decision.intent == "coach_request":
        if not resume_from_permission_request:
            await _save_user_message(db, session.session_id, text)
        if course_id is not None:
            coach_result = await _start_coach_flow(
                db=db,
                session=session,
                course_id=course_id,
            )
            await _save_ai_message(
                db,
                session_id=session.session_id,
                message_type="assistant_coach_started",
                answer=coach_result.answer,
                mode=coach_result.mode,
                extra={"course_id": course_id, "router_reason": decision.reason, "coach_stage": coach_result.coach_stage},
            )
            await _maybe_store_dialogue_summary(
                db=db,
                session_id=session.session_id,
                user_id=user_id,
                course_id=course_id,
            )
            return coach_result

        answer = "这更像一个需要持续跟进的学习辅导问题。我建议你进入学习教练流程，我会先做诊断，再给你计划并持续跟进执行情况。"
        if course_id is None:
            answer += "\n\n不过在开始之前，你需要先指定当前课程。"
        await _save_ai_message(
            db,
            session_id=session.session_id,
            message_type="assistant_coach_suggestion",
            answer=answer,
            mode="coach_suggestion",
            extra={"course_id": course_id, "router_reason": decision.reason},
        )
        await _maybe_store_dialogue_summary(
            db=db,
            session_id=session.session_id,
            user_id=user_id,
            course_id=course_id,
        )
        return AssistantOrchestratorResult(
            answer=answer,
            mode="coach_suggestion",
            coach_stage="coach_diagnose" if course_id is not None else None,
        )

    if not resume_from_permission_request:
        await _save_user_message(db, session.session_id, text)

    if decision.intent == "course_qa" or decision.needs_rag:
        answer, contexts = await qa_agent.handle_qa(
            db=db,
            question=text,
            course_id=course_id,
            top_k=top_k,
            recent_history=recent_history,
            memory_contexts=memory_contexts,
        )
        await _save_ai_message(
            db,
            session_id=session.session_id,
            message_type="assistant_answer",
            answer=answer,
            mode="qa",
            extra={"contexts_count": len(contexts), "router_reason": decision.reason},
        )
        await _maybe_store_dialogue_summary(
            db=db,
            session_id=session.session_id,
            user_id=user_id,
            course_id=course_id,
        )
        return AssistantOrchestratorResult(answer=answer, mode="qa", contexts=contexts)

    allow_personal_context = confirm_personal_context and decision.needs_personal_context
    chat_mode = "personal_analysis" if allow_personal_context and decision.intent == "personal_analysis" else "chat"
    answer, tool_name, tool_result, contexts = await chat_agent.handle_chat(
        db=db,
        session_id=session.session_id,
        user_id=user_id,
        message=text,
        course_id=course_id,
        top_k=top_k,
        allow_personal_context=allow_personal_context,
        mode_hint="personal_analysis" if chat_mode == "personal_analysis" else "general",
        recent_history=recent_history,
        memory_contexts=memory_contexts,
    )
    await _save_ai_message(
        db,
        session_id=session.session_id,
        message_type="assistant_answer",
        answer=answer,
        mode=chat_mode,
        extra={
            "tool_name": tool_name,
            "router_reason": decision.reason,
            "allow_personal_context": allow_personal_context,
        },
    )
    await _maybe_store_dialogue_summary(
        db=db,
        session_id=session.session_id,
        user_id=user_id,
        course_id=course_id,
    )
    return AssistantOrchestratorResult(
        answer=answer,
        mode=chat_mode,
        tool_name=tool_name,
        tool_result=tool_result,
        contexts=contexts,
    )
