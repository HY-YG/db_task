import json

from langchain.agents import create_agent
from langchain.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import ai_crud
from backend.schemas.ai_sch import AiMessageCreate
from backend.services.langchain_utils import extract_text_from_agent_result
from backend.services import rag, tools as builtin_tools
from backend.services.llm import chat_completion, get_langchain_chat_model


async def handle_chat(
    *,
    db: AsyncSession,
    session_id: int,
    user_id: int,
    message: str,
    course_id: int | None,
    top_k: int,
    allow_personal_context: bool = True,
    mode_hint: str = "general",
    recent_history: list[dict[str, str]] | None = None,
    memory_contexts: list[dict] | None = None,
) -> tuple[str, str | None, dict | None, list[dict]]:
    contexts = await rag.search_chunks(db, question=message, course_id=course_id, top_k=top_k)
    called_tools: list[dict] = []

    @tool
    async def get_course_resources() -> str:
        """查询当前课程的章节与学习资料。"""
        if course_id is None:
            data = {"error": "course_id is required"}
        else:
            data = await builtin_tools.query_course_resources(db, course_id=course_id)
        called_tools.append({"tool": "query_course_resources", "result": data})
        await ai_crud.create_message(
            db,
            AiMessageCreate(
                session_id=session_id,
                sender="tool",
                message_content={"type": "tool", "tool": "query_course_resources", "result": data},
            ),
        )
        return json.dumps(data, ensure_ascii=False)

    tools = [get_course_resources]
    tool_names = ["课程资料"]

    if allow_personal_context:
        @tool
        async def get_user_notes() -> str:
            """查询当前学生在本课程下的学习笔记。"""
            data = await builtin_tools.query_user_notes(db, user_id=user_id, course_id=course_id)
            called_tools.append({"tool": "query_user_notes", "result": data})
            await ai_crud.create_message(
                db,
                AiMessageCreate(
                    session_id=session_id,
                    sender="tool",
                    message_content={"type": "tool", "tool": "query_user_notes", "result": data},
                ),
            )
            return json.dumps(data, ensure_ascii=False)

        @tool
        async def get_study_plans() -> str:
            """查询当前学生最近的学习计划，用于分析计划安排和执行情况。"""
            data = await builtin_tools.query_study_plans(db, user_id=user_id)
            called_tools.append({"tool": "query_study_plans", "result": data})
            await ai_crud.create_message(
                db,
                AiMessageCreate(
                    session_id=session_id,
                    sender="tool",
                    message_content={"type": "tool", "tool": "query_study_plans", "result": data},
                ),
            )
            return json.dumps(data, ensure_ascii=False)

        @tool
        async def get_assignment_status() -> str:
            """查询当前学生在本课程下的作业完成情况。"""
            if course_id is None:
                data = {"error": "course_id is required"}
            else:
                data = await builtin_tools.query_assignment_status(db, user_id=user_id, course_id=course_id)
            called_tools.append({"tool": "query_assignment_status", "result": data})
            await ai_crud.create_message(
                db,
                AiMessageCreate(
                    session_id=session_id,
                    sender="tool",
                    message_content={"type": "tool", "tool": "query_assignment_status", "result": data},
                ),
            )
            return json.dumps(data, ensure_ascii=False)

        @tool
        async def get_learning_memories() -> str:
            """查询当前学生最近的学习摘要记忆，用于辅助连续分析。"""
            data = await builtin_tools.query_learning_memories(
                db,
                user_id=user_id,
                course_id=course_id,
                limit=5,
            )
            called_tools.append({"tool": "query_learning_memories", "result": data})
            await ai_crud.create_message(
                db,
                AiMessageCreate(
                    session_id=session_id,
                    sender="tool",
                    message_content={"type": "tool", "tool": "query_learning_memories", "result": data},
                ),
            )
            return json.dumps(data, ensure_ascii=False)

        tools.extend([get_user_notes, get_study_plans, get_assignment_status, get_learning_memories])
        tool_names.extend(["学生笔记", "学习计划", "作业完成情况", "学习摘要记忆"])

    prompt_lines = [
        "你是数据库课程学习助教。",
        f"当前可使用的工具包括：{', '.join(tool_names)}。",
        "你还会收到一组已检索到的资料片段（contexts），请结合它们回答。",
    ]
    if allow_personal_context:
        prompt_lines.append("你已获得授权，可以读取当前学生的个人学习资料。")
    else:
        prompt_lines.append("你当前没有权限读取学生的个人学习资料，只能使用公共课程资料。")
    if mode_hint == "personal_analysis":
        prompt_lines.append("当前任务重点是结合已授权的数据，对学生的学习情况做个性化分析并给出建议。")
    prompt_lines.extend(
        [
            "要求：",
            "1. 用中文回答。",
            "2. 不要输出 JSON。",
            "3. 不要暴露你的工具调用过程。",
            "4. 如果问题需要数据支撑，请主动调用工具。",
        ]
    )
    system_prompt = "\n".join(prompt_lines)
    history_text = "无"
    if recent_history:
        history_text = "\n".join(
            [f"{'用户' if item['role'] == 'user' else '助手'}: {item['content']}" for item in recent_history]
        )
    memory_text = "无"
    if memory_contexts:
        lines = []
        for index, item in enumerate(memory_contexts, start=1):
            lines.append(f"[记忆{index}] 摘要: {item.get('summary_text', '')}")
            topics = item.get("topics", [])
            if topics:
                lines.append(f"主题: {', '.join([str(topic) for topic in topics])}")
            weak_points = item.get("weak_points", [])
            if weak_points:
                lines.append(f"薄弱点: {', '.join([str(point) for point in weak_points])}")
            goals = item.get("goals", [])
            if goals:
                lines.append(f"目标: {', '.join([str(goal) for goal in goals])}")
        memory_text = "\n".join(lines)

    model = get_langchain_chat_model(temperature=0.2)
    answer: str | None = None
    if model is not None:
        agent = create_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
        )
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"最近几轮对话：\n{history_text}\n\n"
                            f"相关摘要记忆：\n{memory_text}\n\n"
                            f"当前问题：{message}\n\n"
                            f"课程资料片段（contexts）：\n{json.dumps(contexts, ensure_ascii=False)}"
                        ),
                    }
                ]
            }
        )
        answer = extract_text_from_agent_result(result)

    if answer is None:
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"最近几轮对话：\n{history_text}"},
            {"role": "user", "content": f"相关摘要记忆：\n{memory_text}"},
            {"role": "user", "content": message},
            {"role": "user", "content": json.dumps({"contexts": contexts}, ensure_ascii=False)},
        ]
        answer = chat_completion(llm_messages) or "当前没有可用的资料或工具结果。"

    tool_name: str | None = None
    tool_result: dict | None = None
    if called_tools:
        if len(called_tools) == 1:
            tool_name = called_tools[0]["tool"]
            tool_result = called_tools[0]["result"]
        else:
            tool_name = "multiple"
            tool_result = {"tools": called_tools}

    return answer, tool_name, tool_result, contexts
