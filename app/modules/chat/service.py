from fastapi.sse import ServerSentEvent
from langchain.messages import HumanMessage
from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.chat_thread.repository import ChatThreadRepository
from app.modules.chat_thread.exceptions import ChatThreadNotFound
from .schema import ChatRequest


class ChatService:

    def __init__(self, session: AsyncSession, agent: CompiledStateGraph):
        self.agent = agent
        self.repository = ChatThreadRepository(session)

    async def chat_stream(self, user_id: int, request: ChatRequest):
        """实现Agent流式对话的函数"""

        # 1.校验，判断当前thread_id是否属于当前用户
        chat_thread = await self.repository.required_owner(user_id, request.thread_id)
        if not chat_thread:
            # 指定会话不属于当前用户
            raise ChatThreadNotFound()

        # 2.组织消息
        _input = {"messages": [HumanMessage(request.message)]}

        # 3.组织config，实现会话记忆
        config = {"configurable": {"thread_id": request.thread_id}}

        # 4.调用Agent
        stream = await self.agent.astream_events(
            _input,
            config,
            version="v3"
        )

        # 5.返回结果
        async for event in stream:
            method = event['method']
            # 判断事件类型，可以是messages、interrupts等等
            if method == 'messages':
                data = event['params']['data'][0]
                if isinstance(data, AIMessage):
                    yield ServerSentEvent(data=data.text, event="message")
                elif data.get('delta') and data['delta'].get('text'):
                    yield ServerSentEvent(data=data['delta'].get('text'), event="message")

        yield ServerSentEvent(data="END", event="done")