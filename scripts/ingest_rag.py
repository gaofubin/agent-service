"""RAG知识库构建脚本：查询所有保险产品，解析条款并写入向量库和数据库"""

import asyncio

from langchain_milvus import BM25BuiltInFunction, Milvus
from langchain_ollama import OllamaEmbeddings

from app.core.config import settings
from app.core.logging import get_logger
from app.infra.database import AsyncSessionFactory
from app.modules.product.service import ProductService
from app.rag.pipeline import RAGPipeline

logger = get_logger(__name__)


async def main() -> None:
    # 1.初始化EmbeddingModel
    embeddings = OllamaEmbeddings(
        model="qwen3-embedding:0.6b",  # 性价比高的模型
        dimensions=1024,  # 可选：减少维度以节省存储
    )

    # 2.初始化VectorStore，会自动创建Collection
    vector_store = Milvus(
        embedding_function=embeddings,
        collection_name="insurance_collection",
        builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
        vector_field=["dense", "sparse"],
        connection_args={"uri": settings.rag.milvus_url},
        auto_id=True,
    )

    # 3.初始化Pipeline
    pipeline = RAGPipeline(vector_store)

    try:
        # 4.查询所有products
        async with AsyncSessionFactory() as session:
            service = ProductService(session)
            products = await service.list_product()
        logger.info(f"查询到 {len(products)} 个产品")

        # 5.逐个产品构建知识库
        for product in products:
            logger.info(f"正在构建知识库: {product.name}...")
            await pipeline.ingest(product)
            logger.info(f"完成: {product.name}")

        logger.info("RAG知识库构建完成✅")
    finally:
        pipeline.close()
        vector_store.client.close()


if __name__ == "__main__":
    asyncio.run(main())
