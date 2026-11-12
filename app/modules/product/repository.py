"""
Repository 层：只负责数据库访问。

职责边界：
- 不处理接口参数校验 → 交给 schemas
- 不组装响应对象     → 交给 schemas / service
- 一个方法 = 一次（或一组）数据库操作
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product


class ProductRepository:
    """产品数据访问"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_category(
        self,
        category: str | None = None,
    ) -> Sequence[Product]:
        # ---- 1. 组装查询条件 ----
        # 默认只查上架（active）的产品
        conditions = [Product.status == "active"]

        # ============================================================
        # ⚠️ 这是第二个 bug（修完 service 缩进后会立刻遇到）
        #
        # 原来的写法：if conditions:
        #   conditions 在上一行刚被赋值成 [Product.status == "active"]，
        #   这个列表永远非空，所以 if 永远成立 → 条件永远会被追加。
        #
        #   后果：当 category 是 None 时，也会追加
        #         Product.category == None
        #   SQLAlchemy 会把它编译成 category IS NULL，
        #   而数据库里 category 是 NOT NULL 字段 → 永远查不到数据。
        #
        #   症状：接口返回 200，但 items 一直是空数组 []，
        #        也不报错，很难发现。
        #
        # 正确写法：判断"参数"有没有值，而不是判断"列表"空不空：if category:
        # ============================================================
        if category:
            conditions.append(Product.category == category)

        # ---- 2. 组装并执行查询 ----
        stmt = (
            select(Product)
            .where(*conditions)          # 把条件列表解包成多个 AND 条件
            .order_by(Product.id.asc())  # 排序，保证返回顺序稳定
        )
        result = await self.session.scalars(stmt)
        return result.all()
