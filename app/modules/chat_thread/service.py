from uuid import UUID

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import ChatThreadNotFound
from .repository import ChatThreadRepository
from .models import ChatThread
from .schemas import ChatHistoryResponse, ChatMessageResponse

class ChatThreadService:

    def __init__(self, session: AsyncSession, agent: CompiledStateGraph):
        self.session = session
        self.repository = ChatThreadRepository(session)
        self.agent = agent

    async def add(self, user_id: int , title: str) -> ChatThread:
        # 用上下文管理，开启事务，运行完成，自动commit，出现异常，自动rollback
        async with self.session.begin():
            # 创建对象，对象 映射 到数据库 一条数据
            chat_thread = ChatThread(user_id = user_id, title = title)
            # 新增对象，就是插入一条数据
            await self.repository.add(chat_thread)

            return chat_thread

    async def list_by_user(self, user_id: int):
        return await self.repository.list_by_user_id(user_id)

    async def remove(self, user_id: int, id: str):
        async with self.session.begin():
            # 1.查询会话，校验会话是否属于当前用户
            chat_thread = await self.repository.required_owner(user_id, id)
            if not chat_thread:
                raise ChatThreadNotFound()
            # 2.删除会话的历史消息（State的所有的快照）
            await self.agent.checkpointer.adelete_thread(id)
            # 3.删除会话
            await self.repository.delete(chat_thread)

    async def rename(self, user_id: int , id: str, title: str):
        async with self.session.begin():
            # 1.查询会话，校验会话是否属于当前用户
            chat_thread = await self.repository.required_owner(user_id, id)
            if not chat_thread:
                # raise: 就是指扔出去一个异常，代码会立刻终止，结束运行，把异常扔给调用者
                raise ChatThreadNotFound()
            # 2.修改标题
            chat_thread.title = title
            # 3.刷新数据
            await self.session.flush()
            await self.session.refresh(chat_thread)
            # 4.返回
            return chat_thread

    async def get_chat_history(self, user_id: int, thread_id: str):
        # 1.校验当前会话是否属于当前用户
        chat_thread = await self.repository.required_owner(user_id, thread_id)
        if not chat_thread:
            # raise: 就是指扔出去一个异常，代码会立刻终止，结束运行，把异常扔给调用者
            raise ChatThreadNotFound()
        # 2.查询会话历史
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = await self.agent.aget_state(config)

        # 3.封装历史消息
        messages = []
        for message in state_snapshot.values.get('messages', []):
            # 判断类型，决定role
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue

            if message.text:
                messages.append(ChatMessageResponse(role=role, content=message.text))


        return ChatHistoryResponse(
            thread_id = thread_id,
            messages = messages
        )
