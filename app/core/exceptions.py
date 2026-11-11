class ApplicationError(Exception):
    """应用业务异常基类"""

    status_code: int = 500                # 默认http状态码
    code: str = "APPLICATION_ERROR"       # 默认错误码
    message: str = "服务器内部错误"         # 默认错误消息