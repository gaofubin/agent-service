import re
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings
from app.core.logging import get_logger
from .schemas import RouteResult
logger = get_logger(__name__)


SYSTEM_PROMPT = """
你是保险商城智能客服的意图识别节点，请判断用户消息应该交给哪个工作流。

intent只能从以下选项中选择：
- recommendation_plan：保险产品咨询、产品条款、保险推荐、方案管理和投保咨询
- claim：报案、理赔责任、理赔材料、理赔流程和理赔进度
- human_handoff：投诉、高风险问题或用户明确要求人工服务
- chitchat：与保险业务无关的普通聊天
- fallback：无法判断用户意图
""".strip()

class IntentRouter:

    def __init__(self):
        # 初始化模型
        model = init_chat_model(
            "deepseek-v4-flash",
            api_key=settings.llm.api_key,
            extra_body = {"thinking": {"type": "disabled"}}
        )
        # 给模型绑定结构化输出，让模型按照要求输出路由结果
        self.route_model = model.with_structured_output(RouteResult).with_config({
            "tags": ["nostream"]
        })

    def route(
        self,
        query: str, # 用户本轮的提问
        context: str    # 历史对话的上下文（上一轮的工作流名字、上一轮AI回复的消息）
    ) -> RouteResult:
        try:
            # 1.寒暄识别（基于规则，正则表达式匹配）
            intent = match_social_intent(query)
            if intent:
                # 识别出是寒暄中的一种，返回寒暄固定回复
                return response_by_social_intent(intent)

            # 2.基于模型识别意图
            result: RouteResult = self.route_model.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"用户问题:{query}\n 历史上下文：{context}\n")
            ])
        except Exception:
            # 兜底方案，意图识别失败了，返回固定回复
            result = RouteResult(intent="fallback", reason="意图识别出现异常")

        logger.info(f"意图识别完成，intent:{result.intent}, reason:{result.reason}")
        return result


# 基于规则的识别是否为寒暄

# 寒暄类型枚举
SocialIntent = Literal["greeting", "thanks", "goodbye"]
# 寒暄的匹配规则
SOCIAL_PATTERNS = {
    "greeting": (
        r"(你|您)?好(呀|啊|哦)?",
        r"嗨",
        r"哈喽",
        r"hello",
        r"hi",
        r"在吗",
    ),
    "thanks": (
        r"谢谢(你|您)?",
        r"多谢(你|您)?",
        r"感谢(你|您)?",
        r"辛苦了",
    ),
    "goodbye": (
        r"再见",
        r"拜拜",
        r"先这样",
        r"没事了",
    ),
}
# 寒暄的固定回复
SOCIAL_RESPONSES = {
    "greeting": "您好，我是您的保险顾问，可以帮您咨询产品、推荐方案或办理理赔。",
    "thanks": "不客气，后续有保险问题可以随时问我。",
    "goodbye": "好的，后续需要帮助时随时联系我。",
}

def normalize_message(message: str) -> str:
    """格式化消息，去掉无效字符"""

    return re.sub(r"[\s，。！？、,.!?~～]", "", message).lower()


def match_social_intent(message: str) -> SocialIntent | None:
    """基于规则匹配的路由"""

    normalized = normalize_message(message)
    for intent, patterns in SOCIAL_PATTERNS.items():
        if any(re.fullmatch(pattern, normalized) for pattern in patterns):
            return intent
    return None

def response_by_social_intent(intent: SocialIntent):
    """根据规则识别出的意图返回固定回复"""

    return SOCIAL_RESPONSES.get(intent)



# 创建好对象，方便对方使用
router = IntentRouter()