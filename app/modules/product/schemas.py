from decimal import Decimal
from pydantic import field_validator, BaseModel


class ProductResponse(BaseModel):
    """保险产品响应结果"""

    id: int
    name: str
    clause_name: str
    category: str
    insurer: str
    image_url: str
    description: str
    min_premium: Decimal | None
    max_premium: Decimal | None
    target_group: str | None
    highlights: list[str]
    status: str

    @field_validator("highlights", mode="before")
    @classmethod
    def normalize_highlights(cls, value: list[str] | None) -> list[str]:
        return value or []