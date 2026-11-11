from sqlalchemy import *
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product
from decimal import Decimal

class ProductRepository:

    def __init__(self, session: AsyncSession):
        self.session = session


    async def query_by_category(
        self,
        category: str | None = None,
    ) -> list[Product]:

        # 1.动态组装查询条件
        # 1.1.产品必须是上架产品，status是active
        conditions = [Product.status == 'active']
        # 1.1.分类条件
        if category:
            conditions.append(Product.category == category)

        # 2.执行查询
        result = await self.session.scalars(
            select(Product)
            .where(*conditions)
            .order_by(Product.id.asc())
        )

        # 3.返回结果
        return result.all()

    async def find_candidates(
        self,
        categories: list[str],
        premium_min: Decimal | None,
        limit_per_category: int,
    ) -> list[Product]:
        # 每个险种查limit_per_category条，所以先定义list，收集结果
        candidate_products: list[Product] = []

        # 利用dict去重，并保留调用方传入的险种顺序，然后遍历逐个查询
        for category in dict.fromkeys(categories):
            conditions = [
                Product.status == "active",
                Product.category == category,
            ]
            if premium_min is not None:
                conditions.append(Product.min_premium < premium_min)

            products = await self.session.scalars(
                select(Product)
                .where(*conditions)
                .order_by(
                    Product.min_premium.asc().nullslast(),
                    Product.id.asc(),
                )
                .limit(limit_per_category)
            )
            candidate_products.extend(products.all())

        return candidate_products