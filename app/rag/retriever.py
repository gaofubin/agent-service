from langchain_milvus import Milvus
from pymilvus import Function, FunctionType

from app.infra.database import AsyncSessionFactory
from .repository import ParentChunkRepository


def create_cross_encoder_ranker(query: str):
    return Function(
        name="dashscope_semantic_ranker",  # ranker名词，唯一即可
        input_field_names=["text"],  # 原始文档字段
        function_type=FunctionType.RERANK,  # ranker类型，这里是固定值
        params={
            "reranker": "model",  # rerank类型，基于模型rerank，也就是cross-encoder
            "provider": "ali",  # rerank模型提供者
            "model_name": "gte-rerank-v2",  # rerank模型名称
            "queries": [query],  # 查询条件
            "max_client_batch_size": 5,  # 向模型发送请求时的批处理限制
        },
    )


class ParentChunkRetriever:

    def __init__(self, vector_store: Milvus):
        self._vector_store = vector_store

    async def retrieve(self, query: str, k: int, product_id: int):
        # 1.混合检索，召回子块 list[Document]
        child_chunks = await self._vector_store.asimilarity_search(
            query,
            k=k,  # 返回得分最高的K条
            fetch_k=10,  # 初筛时返回的文档的数量
            expr=f"product_id == {product_id}",
            reranker=create_cross_encoder_ranker(query)
        )

        # 2.从子块中拿到parent_id，并且去重
        parent_ids = list(
            dict.fromkeys(
                child.metadata.get("parent_id") for child in child_chunks
            )
        )
        if not parent_ids:
            return []

        # 3.查询父块
        async with AsyncSessionFactory() as session:
            repo = ParentChunkRepository(session)
            parents = await repo.query_by_ids(parent_ids)


        # 4.把parents按照检索回来的顺序排序

        # 4.1.把parents变成一个字典，key是parent_id，值是parent
        parent_id_dict = {
            str(parent.id): parent
            for parent in parents
        }

        # 4.2.遍历parent_ids，逐一找到parent，放到列表中
        parent_chunks = [
            parent_id_dict.get(id)
            for id in parent_ids
        ]

        return parent_chunks


