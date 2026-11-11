from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ChatThread


class ChatThreadRepository:

    def __init__(self, session:AsyncSession):
        self.session = session

    async def add(self, chat_thread: ChatThread):
        self.session.add(chat_thread)

    async def list_by_user_id(self, user_id: int):
        # 1.根据user_id查询会话
        threads = await self.session.scalars(
            # SELECT * FROM chat_threads WHERE user_id = 1 ORDER BY update_at DESC
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(
                ChatThread.updated_at.desc(),
                ChatThread.created_at.desc()
            )
        )
        # 2.返回列表
        return threads.all()

    async def delete(self, chat_thread: ChatThread):
        # 删除会话
        await self.session.delete(chat_thread)

    async def required_owner(self, user_id: int, id: str) -> ChatThread:
        """校验指定会话是否属于指定用户"""

        return await self.session.scalar(
            # SELECT * FROM chat_threads WHERE user_id = 1 AND id = '32'
            select(ChatThread)
            .where(ChatThread.id == id, ChatThread.user_id == user_id)
        )