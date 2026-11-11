from langchain_core.messages import AIMessage, BaseMessage
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import Command

from .schemas import InsuranceAgentState, Intent
from .intent_router import router
from .chitchat import init_chitchat_agent
from .insurance_advisor import init_insurance_advisor

# 1.定义节点

# 1.1.意图识别节点
def route_node(state: InsuranceAgentState) -> Command[Intent]:
    # 获取上一轮的路由结果
    previous_workflow = state.get("active_workflow", "")
    # 获取用户本轮的提问问题
    messages = state['messages']
    # 准备上下文
    previous_ai_message = find_previous_ai_message(messages)
    context = f"上一轮工作流：{previous_workflow} \n 上一轮AI回复的信息：{previous_ai_message}"

    # 调用路由工具，完成意图识别
    result = router.route(messages[-1].text, context)

    if isinstance(result, str):
        # 当前识别出的是寒暄，直接返回固定回复结果
        return Command(
            update={
                "active_workflow": "chitchat",
                "previous_workflow": previous_workflow,
                "messages": [AIMessage(content=result)]
            },
            goto=END
        )

    return Command(
        update={
            "active_workflow": result.intent,
            "previous_workflow": previous_workflow
        },
        goto=result.intent
    )

def find_previous_ai_message(messages: list[BaseMessage]) -> str:
    """查找本轮用户消息之前最近一条可展示的AI回复"""

    for message in reversed(messages[:-1]):
        # 跳过非AIMessage
        if not isinstance(message, AIMessage):
            continue
        # 跳过工具消息
        if message.tool_calls:
            continue
        # 如果是正常AIMessage，直接返回
        if message.text:
            return message.text
    # 如果是空消息
    return ""

# 1.2.保险方案推荐咨询节点
# def recommendation_node(state: InsuranceAgentState):
#     return {"messages": [AIMessage("保险方案推荐功能尚未完成~")]}

# 1.3.理赔咨询节点
def claim_node(state: InsuranceAgentState):
    return {"messages": [AIMessage("理赔咨询功能尚未完成~")]}

# 1.4.闲聊节点
# def chitchat_node(state: InsuranceAgentState):
#     return {"messages": [AIMessage("哈哈，欢迎你来到安心保商城，今天聊点啥~")]}

# 1.5.人工
def human_handoff_node(state: InsuranceAgentState):
    return {"messages": [AIMessage("你的请求已转人工，请耐心等待~~")]}

# 1.6.fallback
def fallback_node(state: InsuranceAgentState):
    return {"messages": [AIMessage("无法识别您的意图，请再说一遍~~")]}

# 2.创建Graph，用Edge连接Node
async def init_insurance_agent(checkpointer):
    # 建造器
    builder = StateGraph(InsuranceAgentState)

    # 添加节点
    builder.add_node("route", route_node)
    builder.add_node("recommendation_plan",await init_insurance_advisor())
    builder.add_node("chitchat", init_chitchat_agent())
    builder.add_node("claim", claim_node)
    builder.add_node("human_handoff", human_handoff_node)
    builder.add_node("fallback", fallback_node)

    # 添加Edge，连Node
    builder.add_edge(START, "route")
    builder.add_edge("recommendation_plan", END)
    builder.add_edge("claim", END)
    builder.add_edge("human_handoff", END)
    builder.add_edge("fallback", END)
    builder.add_edge("chitchat", END)

    # 编译Graph
    return builder.compile(checkpointer=checkpointer)