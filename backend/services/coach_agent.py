"""封装学习教练代理，负责诊断学习状态并生成分阶段辅导建议。"""

from dataclasses import dataclass
import json
from typing import Any

from fastapi import HTTPException
from langchain.agents import create_agent
from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import ai_crud, study_plans_crud
from backend.schemas.ai_sch import AiMessageCreate, AiSessionUpdate
from backend.schemas.study_plans_sch import StudyPlanCreate, StudyPlanUpdate
from backend.services.langchain_utils import extract_text_from_agent_result, invoke_chat_model_text
from backend.services import memory_service, tools as coach_tools
from backend.services.llm import chat_completion, get_langchain_chat_model


@dataclass
class ExecuteIntent:
    need_completion: bool
    need_adjustment: bool
    need_daily_review: bool


@dataclass
class DiagnoseStageResult:
    session_id: int
    stage: str
    assistant_message: str
    questions: list[str]
    diagnosis_summary: str | None
    next_stage: str | None

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "assistant_message": self.assistant_message,
            "questions": self.questions,
            "diagnosis_summary": self.diagnosis_summary,
            "next_stage": self.next_stage,
        }


@dataclass
class PlanStageResult:
    session_id: int
    stage: str
    assistant_message: str
    plan_id: int | None
    study_plan: str | None
    next_stage: str | None

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "assistant_message": self.assistant_message,
            "plan_id": self.plan_id,
            "study_plan": self.study_plan,
            "next_stage": self.next_stage,
        }


@dataclass
class ExecuteStageResult:
    session_id: int
    stage: str
    assistant_message: str
    plan_id: int | None
    study_plan: str | None
    execution_feedback: str | None
    next_stage: str | None

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "stage": self.stage,
            "assistant_message": self.assistant_message,
            "plan_id": self.plan_id,
            "study_plan": self.study_plan,
            "execution_feedback": self.execution_feedback,
            "next_stage": self.next_stage,
        }


async def _get_coach_course_id(db: AsyncSession, session_id: int) -> int | None:
    start_message = await ai_crud.get_latest_ai_message_json(
        db,
        session_id=session_id,
        message_type="coach_start",
        stage="coach_diagnose",
    )
    if start_message is None:
        return None
    return start_message.message_content.get("course_id")


async def _run_langchain_text(*, system_prompt: str, user_content: str) -> str | None:
    return await invoke_chat_model_text(system_prompt=system_prompt, user_content=user_content, temperature=0.2)


async def _store_coach_memory(
    *,
    db: AsyncSession,
    session: Any,
    memory_kind: str,
    coach_stage: str | None,
    source_text: str,
    extra_meta: dict[str, Any] | None = None,
) -> None:
    course_id = await _get_coach_course_id(db, session.session_id)
    await memory_service.summarize_text_to_memory(
        db=db,
        session_id=session.session_id,
        user_id=session.user_id,
        course_id=course_id,
        source_text=source_text,
        memory_kind=memory_kind,
        coach_stage=coach_stage,
        extra_meta=extra_meta,
    )


async def handle_start(*, db: AsyncSession, session: Any, course_id: int) -> str:
    stage = "coach_diagnose"
    await ai_crud.update_session(db, session, AiSessionUpdate(session_status=stage))
    system_prompt = (
        "你是AI学习教练。你的目标是帮助学生在本课程中更高效地学习。\n"
        "请按阶段推进：先诊断，再给出可执行的学习计划。\n"
        "当前阶段：诊断。你需要先问3-5个澄清问题，确认学生的基础、目标、时间、薄弱点。"
    )
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="system",
            message_content={"type": "coach_start", "course_id": course_id, "stage": stage, "prompt": system_prompt},
        ),
    )
    return stage


async def _run_langchain_coach_agent(
    *,
    db: AsyncSession,
    session: Any,
    plan_content: str,
    progress_text: str,
    system_prompt: str,
) -> str | None:
    model = get_langchain_chat_model(temperature=0.2)
    if model is None:
        return None

    course_id = await _get_coach_course_id(db, session.session_id)
    user_id = session.user_id

    @tool
    async def get_user_notes() -> str:
        """查询当前学生在本课程下的学习笔记，用于分析卡点和复盘。"""
        data = await coach_tools.query_user_notes(db, user_id=user_id, course_id=course_id)
        return json.dumps(data, ensure_ascii=False)

    @tool
    async def get_course_resources() -> str:
        """查询当前课程的章节与学习资料，用于推荐复习材料。"""
        if course_id is None:
            return json.dumps({"error": "course_id is missing"}, ensure_ascii=False)
        data = await coach_tools.query_course_resources(db, course_id=course_id)
        return json.dumps(data, ensure_ascii=False)

    @tool
    async def get_assignment_status() -> str:
        """查询当前学生在本课程下的作业完成情况，用于调整学习计划。"""
        if course_id is None:
            return json.dumps({"error": "course_id is missing"}, ensure_ascii=False)
        data = await coach_tools.query_assignment_status(db, user_id=user_id, course_id=course_id)
        return json.dumps(data, ensure_ascii=False)

    agent = create_agent(
        model=model,
        tools=[get_user_notes, get_course_resources, get_assignment_status],
        system_prompt=system_prompt
        + "\n你正在处理数据库课程学习教练的执行阶段。"
        + "\n如果需要了解学生历史笔记、课程资料或作业完成情况，请主动调用工具。"
        + "\n如果不需要工具，也可以直接回答。"
        + "\n最终回答必须是中文纯文本，不要输出 JSON，不要暴露你的工具调用过程。",
    )
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"当前学习计划：\n{plan_content}\n\n学生本次反馈：\n{progress_text}",
                }
            ]
        }
    )
    return extract_text_from_agent_result(result)


async def handle_diagnose(*, db: AsyncSession, session: Any, message: str | None) -> DiagnoseStageResult:
    questions = get_diagnose_questions()
    assistant_message = "我先做一个能力诊断。请按顺序回答下面问题，越具体越好。"

    if message is None or not message.strip():
        has_questions = await ai_crud.has_ai_message_json(
            db,
            session_id=session.session_id,
            message_type="coach_questions",
            stage="coach_diagnose",
        )
        if not has_questions:
            await ai_crud.create_message(
                db,
                AiMessageCreate(
                    session_id=session.session_id,
                    sender="ai",
                    message_content={
                        "type": "coach_questions",
                        "stage": "coach_diagnose",
                        "assistant_message": assistant_message,
                        "questions": questions,
                    },
                ),
            )
        return DiagnoseStageResult(
            session_id=session.session_id,
            stage="coach_diagnose",
            assistant_message=assistant_message,
            questions=questions,
            diagnosis_summary=None,
            next_stage=None,
        )

    answer_text = message.strip()
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="user",
            message_content={"type": "coach_answer", "stage": "coach_diagnose", "text": answer_text},
        ),
    )

    diagnosis_summary = await _run_langchain_text(
        system_prompt=diagnosis_prompt(),
        user_content=answer_text,
    ) or chat_completion(
        [
            {"role": "system", "content": diagnosis_prompt()},
            {"role": "user", "content": answer_text},
        ]
    ) or build_diagnosis_fallback(answer_text)

    next_stage = "coach_plan"
    session = await ai_crud.update_session(db, session, AiSessionUpdate(session_status=next_stage))
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="ai",
            message_content={
                "type": "coach_diagnosis",
                "stage": next_stage,
                "summary": diagnosis_summary,
            },
        ),
    )
    await _store_coach_memory(
        db=db,
        session=session,
        memory_kind="coach_diagnosis_summary",
        coach_stage="coach_plan",
        source_text=diagnosis_summary,
        extra_meta={"source": "coach_diagnose"},
    )
    return DiagnoseStageResult(
        session_id=session.session_id,
        stage=session.session_status,
        assistant_message="我已经完成初步能力诊断，下一步会给你生成学习计划。",
        questions=[],
        diagnosis_summary=diagnosis_summary,
        next_stage=next_stage,
    )


async def handle_plan(*, db: AsyncSession, session: Any) -> PlanStageResult:
    latest_plan_message = await ai_crud.get_latest_ai_message_json(
        db,
        session_id=session.session_id,
        message_type="coach_plan",
        stage="coach_plan",
    )
    if latest_plan_message is not None:
        content = latest_plan_message.message_content
        return PlanStageResult(
            session_id=session.session_id,
            stage=session.session_status,
            assistant_message="学习计划已经生成好了，你可以直接按计划执行。",
            plan_id=content.get("plan_id"),
            study_plan=content.get("plan_content"),
            next_stage="coach_execute",
        )

    diagnosis_message = await ai_crud.get_latest_ai_message_json(
        db,
        session_id=session.session_id,
        message_type="coach_diagnosis",
    )
    if diagnosis_message is None:
        raise HTTPException(status_code=400, detail="Diagnosis summary not found")

    diagnosis_summary = diagnosis_message.message_content.get("summary", "")
    plan_content = await _run_langchain_text(
        system_prompt=plan_prompt(),
        user_content=diagnosis_summary,
    ) or chat_completion(
        [
            {"role": "system", "content": plan_prompt()},
            {"role": "user", "content": diagnosis_summary},
        ]
    ) or build_plan_fallback(diagnosis_summary)

    plan = await study_plans_crud.create_plan(
        db,
        StudyPlanCreate(user_id=session.user_id, plan_content=plan_content, plan_status="未开始"),
    )
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="ai",
            message_content={
                "type": "coach_plan",
                "stage": "coach_plan",
                "plan_id": plan.plan_id,
                "plan_content": plan_content,
            },
        ),
    )
    session = await ai_crud.update_session(db, session, AiSessionUpdate(session_status="coach_execute"))
    await _store_coach_memory(
        db=db,
        session=session,
        memory_kind="coach_plan_summary",
        coach_stage="coach_execute",
        source_text=plan_content,
        extra_meta={"plan_id": plan.plan_id, "source": "coach_plan"},
    )
    return PlanStageResult(
        session_id=session.session_id,
        stage=session.session_status,
        assistant_message="我已经根据诊断结果生成了两周学习计划，接下来你可以开始按计划执行。",
        plan_id=plan.plan_id,
        study_plan=plan_content,
        next_stage="coach_execute",
    )


async def handle_execute(*, db: AsyncSession, session: Any, message: str | None) -> ExecuteStageResult:
    latest_plan_message = await ai_crud.get_latest_ai_message_json(
        db,
        session_id=session.session_id,
        message_type="coach_plan",
        stage="coach_plan",
    )
    if latest_plan_message is None:
        raise HTTPException(status_code=400, detail="Study plan not found")

    content = latest_plan_message.message_content
    plan_id = content.get("plan_id")
    plan_content = content.get("plan_content", "")

    if message is None or not message.strip():
        return ExecuteStageResult(
            session_id=session.session_id,
            stage=session.session_status,
            assistant_message="你已经进入执行阶段了。把你今天的学习进展、卡点或疑问发给我，我会基于当前计划给你建议。",
            plan_id=plan_id,
            study_plan=plan_content,
            execution_feedback=None,
            next_stage="coach_execute",
        )

    progress_text = message.strip()
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="user",
            message_content={"type": "coach_progress", "stage": "coach_execute", "text": progress_text},
        ),
    )

    intent = analyze_execute_intent(progress_text)

    if intent.need_completion and plan_id is not None:
        completion_summary = await _run_langchain_coach_agent(
            db=db,
            session=session,
            plan_content=plan_content,
            progress_text=progress_text,
            system_prompt=completion_prompt(),
        ) or (
            chat_completion(
                [
                    {"role": "system", "content": completion_prompt()},
                    {"role": "user", "content": f"本轮计划：\n{plan_content}\n\n学生反馈：\n{progress_text}"},
                ]
            )
            or build_completion_fallback(plan_content, progress_text)
        )
        plan = await study_plans_crud.get_plan(db, plan_id)
        if plan is not None:
            await study_plans_crud.update_plan(db, plan, StudyPlanUpdate(plan_status="已完成"))
        session = await ai_crud.update_session(db, session, AiSessionUpdate(session_status="coach_done"))
        await ai_crud.create_message(
            db,
            AiMessageCreate(
                session_id=session.session_id,
                sender="ai",
                message_content={
                    "type": "coach_completion",
                    "stage": "coach_done",
                    "plan_id": plan_id,
                    "summary": completion_summary,
                },
            ),
        )
        await _store_coach_memory(
            db=db,
            session=session,
            memory_kind="coach_completion_summary",
            coach_stage="coach_done",
            source_text=completion_summary,
            extra_meta={"plan_id": plan_id, "source": "coach_completion"},
        )
        return ExecuteStageResult(
            session_id=session.session_id,
            stage=session.session_status,
            assistant_message="恭喜你，这一轮学习计划已经完成。我已经帮你做了阶段总结。",
            plan_id=plan_id,
            study_plan=plan_content,
            execution_feedback=completion_summary,
            next_stage="coach_done",
        )

    if plan_id is not None:
        plan = await study_plans_crud.get_plan(db, plan_id)
        if plan is not None and plan.plan_status == "未开始":
            await study_plans_crud.update_plan(db, plan, StudyPlanUpdate(plan_status="进行中"))

    adjusted_plan = None
    if intent.need_adjustment and plan_id is not None:
        adjusted_plan = await _run_langchain_coach_agent(
            db=db,
            session=session,
            plan_content=plan_content,
            progress_text=progress_text,
            system_prompt=adjustment_prompt(),
        ) or (
            chat_completion(
                [
                    {"role": "system", "content": adjustment_prompt()},
                    {"role": "user", "content": f"原计划：\n{plan_content}\n\n学生反馈：\n{progress_text}"},
                ]
            )
            or build_adjusted_plan_fallback(plan_content, progress_text)
        )
        plan_content = adjusted_plan
        plan = await study_plans_crud.get_plan(db, plan_id)
        if plan is not None:
            await study_plans_crud.update_plan(
                db,
                plan,
                StudyPlanUpdate(plan_content=adjusted_plan, plan_status="进行中"),
            )
        await ai_crud.create_message(
            db,
            AiMessageCreate(
                session_id=session.session_id,
                sender="ai",
                message_content={
                    "type": "coach_plan_adjustment",
                    "stage": "coach_execute",
                    "plan_id": plan_id,
                    "plan_content": adjusted_plan,
                },
            ),
        )
        await _store_coach_memory(
            db=db,
            session=session,
            memory_kind="coach_adjustment_summary",
            coach_stage="coach_execute",
            source_text=adjusted_plan,
            extra_meta={"plan_id": plan_id, "source": "coach_adjustment"},
        )

    review_mode = intent.need_daily_review
    execution_feedback = await _run_langchain_coach_agent(
        db=db,
        session=session,
        plan_content=plan_content,
        progress_text=progress_text,
        system_prompt=execute_prompt(review_mode=review_mode),
    ) or chat_completion(
        [
            {"role": "system", "content": execute_prompt(review_mode=review_mode)},
            {"role": "user", "content": f"学习计划：\n{plan_content}\n\n学生反馈：\n{progress_text}"},
        ]
    ) or (
        build_daily_review_fallback(plan_content, progress_text)
        if review_mode
        else build_execute_fallback(plan_content, progress_text)
    )
    await ai_crud.create_message(
        db,
        AiMessageCreate(
            session_id=session.session_id,
            sender="ai",
            message_content={
                "type": "coach_daily_review" if review_mode else "coach_execute_feedback",
                "stage": "coach_execute",
                "plan_id": plan_id,
                "feedback": execution_feedback,
            },
        ),
    )
    await _store_coach_memory(
        db=db,
        session=session,
        memory_kind="coach_execution_summary",
        coach_stage="coach_execute",
        source_text=execution_feedback,
        extra_meta={
            "plan_id": plan_id,
            "review_mode": review_mode,
            "source": "coach_execute_feedback",
        },
    )
    return ExecuteStageResult(
        session_id=session.session_id,
        stage=session.session_status,
        assistant_message=(
            "我已经根据你今天的执行情况做了复盘总结。"
            if review_mode
            else "我已经根据你当前的执行情况给出建议。"
        )
        + (" 我还顺手帮你微调了学习计划。" if adjusted_plan is not None else " 你可以按这个建议继续往下走。"),
        plan_id=plan_id,
        study_plan=plan_content,
        execution_feedback=execution_feedback,
        next_stage="coach_execute",
    )


def build_diagnosis_fallback(answer: str) -> str:
    preview = answer.strip().replace("\r", " ").replace("\n", " ")
    preview = preview[:180] + ("..." if len(preview) > 180 else "")
    return (
        "这是初步能力诊断结果：\n"
        "1. 你已经提供了当前基础、卡点和学习目标，说明问题描述意愿较强。\n"
        "2. 目前最需要优先补强的是：概念辨析、建模表达、把概念落实到作业与 CRUD 代码。\n"
        "3. 下一阶段我会根据这份诊断，给你生成一个更细的学习计划。\n"
        f"4. 你的原始回答摘要：{preview}"
    )


def get_diagnose_questions() -> list[str]:
    return [
        "你目前对本课程的基础掌握情况如何？（0-10分自评 + 你觉得最薄弱的3个点）",
        "你最近一次卡住/学不懂的具体内容是什么？请给出章节/概念/题目，并描述卡住的地方。",
        "你做题时更常见的问题是哪类？（看不懂题/不会建模/推导不出来/粗心/时间不够/记不住）",
        "你是否能用自己的话解释：主键、外键、1:N、N:M、范式 的区别？分别说一句你的理解。",
        "你希望两周内把能力提升到什么程度？（能独立完成作业/能写出ER图+表结构/能写CRUD+查询优化等）",
    ]


def build_plan_fallback(diagnosis_summary: str) -> str:
    return (
        "这是根据当前诊断生成的两周学习计划：\n"
        "第1周：先补概念基础，每天 40-60 分钟，重点复习主键、外键、1:N、N:M、范式，并手写 2 个小型表设计。\n"
        "第2周：把概念落到代码，每天完成 1 个小 CRUD 练习，复盘 ai_messages、users、courses 这类表的模型与接口。\n"
        "每两天回顾一次错题和卡点，把不懂的点再发给学习教练。\n"
        f"本次诊断依据：{diagnosis_summary[:180]}{'...' if len(diagnosis_summary) > 180 else ''}"
    )


def build_execute_fallback(plan_content: str, progress_text: str) -> str:
    return (
        "这是执行阶段的建议：\n"
        "1. 先不要追求一次学完，先把今天计划里最关键的一小项做完。\n"
        "2. 如果你卡在概念，请先用自己的话复述，再回到 ER 图、表结构、模型定义里各找一个例子对应。\n"
        "3. 如果你卡在代码，请把任务拆成：看懂字段 -> 看懂关系 -> 写最小 CRUD -> 再联调。\n"
        "4. 明天开始前先复盘今天卡住的 1 个点，并记录下来继续问我。\n"
        f"当前计划摘要：{plan_content[:120]}{'...' if len(plan_content) > 120 else ''}\n"
        f"你的进展反馈：{progress_text[:120]}{'...' if len(progress_text) > 120 else ''}"
    )


def build_adjusted_plan_fallback(plan_content: str, progress_text: str) -> str:
    return (
        "这是微调后的学习计划：\n"
        "1. 先把原计划压缩成每天 30-40 分钟，只保留最关键的概念复习和 1 个最小 CRUD 练习。\n"
        "2. 本周先聚焦主键、外键、1:N、N:M 建模，不再同时展开过多主题。\n"
        "3. 如果当天时间不够，优先完成“看懂一个关系 + 写一个最小查询”这件事。\n"
        "4. 把较难内容顺延到下一次复盘后再继续推进。\n"
        f"原计划摘要：{plan_content[:120]}{'...' if len(plan_content) > 120 else ''}\n"
        f"本次调整依据：{progress_text[:120]}{'...' if len(progress_text) > 120 else ''}"
    )


def build_daily_review_fallback(plan_content: str, progress_text: str) -> str:
    return (
        "这是今天的复盘总结：\n"
        "1. 今日完成情况：你已经开始按计划行动，并且能明确说出今天做了什么，这说明执行已经启动。\n"
        "2. 暴露问题：当前还需要继续加强概念辨析和关系建模，不要一次展开太多主题。\n"
        "3. 明日建议：明天优先完成一个最小目标，例如重新画一遍 1:N/N:M 关系，或写一个最小 CRUD。\n"
        f"当前计划摘要：{plan_content[:120]}{'...' if len(plan_content) > 120 else ''}\n"
        f"今日反馈摘要：{progress_text[:120]}{'...' if len(progress_text) > 120 else ''}"
    )


def build_completion_fallback(plan_content: str, progress_text: str) -> str:
    return (
        "这是本轮学习计划的阶段总结：\n"
        "1. 你已经完成了这一轮的主要学习任务，说明执行力和持续性都在提升。\n"
        "2. 本轮最大的收获是：开始把概念学习和表设计、模型定义、CRUD 代码联系起来。\n"
        "3. 下一步建议：先休整并回顾本轮卡点，再进入下一轮更深入的练习或新计划。\n"
        f"本轮计划摘要：{plan_content[:120]}{'...' if len(plan_content) > 120 else ''}\n"
        f"完成反馈摘要：{progress_text[:120]}{'...' if len(progress_text) > 120 else ''}"
    )


def analyze_execute_intent(message: str) -> ExecuteIntent:
    adjust_keywords = ["调整", "微调", "改计划", "重排", "太多", "太难", "没时间", "来不及", "压缩", "减少"]
    review_keywords = ["复盘", "总结", "今天完成", "今天学了", "今天做了", "完成了", "学完", "回顾"]
    completion_keywords = ["计划完成", "完成这一轮", "这轮完成", "本轮完成", "全部完成", "已经完成计划", "这一轮学完", "本轮结束"]

    need_adjustment = any(word in message for word in adjust_keywords)
    need_daily_review = any(word in message for word in review_keywords)
    need_completion = any(word in message for word in completion_keywords) or (
        "完成" in message and any(word in message for word in ["这一轮", "本轮", "学习计划", "最后一个"])
    )
    return ExecuteIntent(
        need_completion=need_completion,
        need_adjustment=need_adjustment,
        need_daily_review=need_daily_review,
    )


def diagnosis_prompt() -> str:
    return (
        "你是数据库课程的 AI 学习教练。请基于学生的回答，给出一份初步能力诊断。\n"
        "要求：\n"
        "1. 用中文。\n"
        "2. 分成 3 段：当前基础、最薄弱的 3 个点、下一阶段建议。\n"
        "3. 语言温和、具体、可执行。\n"
        "4. 不要输出 JSON。"
    )


def plan_prompt() -> str:
    return (
        "你是数据库课程的 AI 学习教练。请根据诊断总结，输出一份未来两周的学习计划。\n"
        "要求：\n"
        "1. 用中文。\n"
        "2. 分为：总目标、第一周、第二周、每日建议、复盘方式。\n"
        "3. 每一部分都要具体、可执行。\n"
        "4. 不要输出 JSON。"
    )


def adjustment_prompt() -> str:
    return (
        "你是数据库课程的 AI 学习教练。学生希望你根据当前困难微调学习计划。\n"
        "要求：\n"
        "1. 用中文。\n"
        "2. 输出一份调整后的计划，包含：调整原因、接下来 3 天安排、保留重点、删除或延后内容。\n"
        "3. 计划要更轻量、更可执行。\n"
        "4. 不要输出 JSON。"
    )


def execute_prompt(*, review_mode: bool) -> str:
    if review_mode:
        return (
            "你是数据库课程的 AI 学习教练。请根据学生当前的学习计划与今日反馈，给出每日复盘总结。\n"
            "要求：\n"
            "1. 用中文。\n"
            "2. 分为：今日完成情况、暴露问题、明日建议。\n"
            "3. 语言温和、具体、可执行。\n"
            "4. 不要输出 JSON。"
        )
    return (
        "你是数据库课程的 AI 学习教练。请根据学生当前的学习计划与执行反馈，给出执行建议。\n"
        "要求：\n"
        "1. 用中文。\n"
        "2. 分为：当前判断、下一步建议、今天最小行动。\n"
        "3. 语言温和、具体、可执行。\n"
        "4. 不要输出 JSON。"
    )


def completion_prompt() -> str:
    return (
        "你是数据库课程的 AI 学习教练。学生表示这一轮学习计划已经完成，请输出阶段总结。\n"
        "要求：\n"
        "1. 用中文。\n"
        "2. 分为：本轮完成情况、主要收获、下一步建议。\n"
        "3. 语言温和、具体、鼓励性强。\n"
        "4. 不要输出 JSON。"
    )
