from app.core.exceptions import ApplicationError

class ChatThreadNotFound(ApplicationError):
    """当前会话不存在 或者 不属于当前用户"""

    status_code: int = 400
    code: str = "CHAT_THREAD_NOT_FOUND"
    message: str = "当前会话不存在 或者 不属于当前用户"