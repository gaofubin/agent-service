from sqlalchemy.ext.asyncio import AsyncSession

from .models import Product
from .repository import ProductRepository
from decimal import Decimal


class ProductService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProductRepository(session)

    async def list_product(
        self,
        category: str | None = None,
    ) -> list[Product]:
        return await self.repository.query_by_category(category)

    async def list_candidates(
        self,
        categories: list[str],
        premium_min: Decimal | None,
        limit_per_category: int,
    ) -> list[Product]:
        return await self.repository.find_candidates(
            categories=categories,
            premium_min=premium_min,
            limit_per_category=limit_per_category,
        )
