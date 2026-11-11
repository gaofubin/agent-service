from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.graph.state import CompiledStateGraph

from app.core.config import settings
from app.core.logging import get_logger
from .tools import query_candidate_products, retrieve_insurance_clause

logger = get_logger(__name__)

SYSTEM_PROMPT = """
你是“安心保”的智能保险顾问。
你需要使用专业、准确、容易理解的语言回答用户的保险问题。
当信息不足时，应先向用户追问，不要编造保险产品或保障内容。
当用户询问保险条款问题时，必须调用工具查询条款，然后根据条款回答，不能自己编造。
"""


# agent在整个系统中，只初始化一次，
async def init_insurance_advisor() -> CompiledStateGraph:
    # 1.初始化模型
    model = init_chat_model(
        model=settings.llm.chat_model,
        api_key=settings.llm.api_key,
        extra_body={"thinking": {"type": "disabled"}}
    )

    # 2.创建Agent，绑定model、tools、Checkpointer
    agent = create_agent(
        model=model,
        tools=[query_candidate_products, retrieve_insurance_clause],
        checkpointer=True,
        system_prompt=SYSTEM_PROMPT
    )

    logger.info("保险顾问Agent初始化完毕~✅️")
    return agent
