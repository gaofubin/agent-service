from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from app.common.schemas import PageResult
from app.infra.database import get_session, AsyncSessionFactory
from app.modules.product.schemas import ProductResponse
from app.modules.product.service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["产品相关接口"])

# 1.抽取公共函数，来生成service
def get_product_service(session: AsyncSession = Depends(get_session)):
    return ProductService(session)
# 2.需要什么，就让FastAPI注入什么，把这个依赖的东西作为参数
# 3.在参数列表中，指定这个依赖的内容的来源，Depends(来源函数名)

@router.get("", response_model=list[ProductResponse])
async def list_product(
    category: str | None = None,
    service:ProductService = Depends(get_product_service)
):
    # 调用Service，返回product列表
    return await service.list_product(category)


@router.get("/candidates", response_model=list[ProductResponse])
async def list_candidates(
    categories: list[str] = Query(min_length=1),
    premium_min: Decimal | None = None,
    limit_per_category: int = 5,
    service:ProductService = Depends(get_product_service)
) -> list[ProductResponse]:
    # 2.查询结果
    return await service.list_candidates(
        categories=categories,
        premium_min=premium_min,
        limit_per_category=limit_per_category,
    )