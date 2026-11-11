from langchain_ollama import OllamaEmbeddings
from langchain_milvus import Milvus, BM25BuiltInFunction
from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import ParentChunkRetriever

# 1.初始化向量模型
embeddings = OllamaEmbeddings(
    model="qwen3-embedding:0.6b",  # 性价比高的模型
    dimensions=1024  # 可选：减少维度以节省存储
)

# 2、初始化 VectorStore，会自动创建Collection
vector_store = Milvus(
    embedding_function=embeddings,
    collection_name="insurance_collection",
    builtin_function=BM25BuiltInFunction(analyzer_params={"type": "chinese"}),
    vector_field=["dense", "sparse"],
    connection_args={"uri": settings.rag.milvus_url},
    auto_id=True,
)

# 3.创建Pipeline
rag_pipeline = RAGPipeline(vector_store)

# 4.创建Retriever
retriever = ParentChunkRetriever(vector_store)


# 5.关闭资源
def close_rag():
    rag_pipeline.close()
    vector_store.client.close()

__all__ = ['pipeline', 'retriever', 'close_rag']