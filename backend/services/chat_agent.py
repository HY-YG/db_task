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
) -> tuple[str, str | None, dict | None, list[dict]]:
    contexts = await rag.search_chunks(db, question=message, course_id=course_id, top_k=top_k)
    called_tools: list[dict] = []

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

    system_prompt = (
        "你是数据库课程学习助教。\n"
        "你可以使用工具查询：学生笔记、课程资料、作业完成情况。\n"
        "你还会收到一组已检索到的资料片段（contexts），请结合它们回答。\n"
        "要求：\n"
        "1. 用中文回答。\n"
        "2. 不要输出 JSON。\n"
        "3. 不要暴露你的工具调用过程。\n"
        "4. 如果问题需要数据支撑，请主动调用工具。"
    )

    model = get_langchain_chat_model(temperature=0.2)
    answer: str | None = None
    if model is not None:
        agent = create_agent(
            model=model,
            tools=[get_user_notes, get_course_resources, get_assignment_status],
            system_prompt=system_prompt,
        )
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"问题：{message}\n\n"
                            f"课程资料片段（contexts）：\n{json.dumps(contexts, ensure_ascii=False)}"
                        ),
                    }
                ]
            }
        )
        answer = extract_text_from_agent_result(result)

    if answer is None:
        llm_messages = [
            {"role": "system", "content": "你是课程学习助教，请结合工具结果与资料片段回答问题。"},
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
