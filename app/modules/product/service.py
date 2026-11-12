"""
Service 层：只负责编排业务流程。

职责边界：
- 不写 SQL        → 交给 Repository
- 不碰 HTTP 细节  → 交给 Router
- 不定义数据结构  → 交给 schemas
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.repository import ProductRepository
from app.modules.product.schemas import ProductResponse


class ProductService:
    """产品业务服务"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProductRepository(session)

    # ============================================================
    # ⚠️⚠️ 这就是你报错的原因 ⚠️⚠️
    #
    # 原来这个 async def 缩进成了 8 个空格，被写进了 __init__ 的方法体里面，
    # Python 会把它当成"__init__ 内部定义的一个局部函数"：
    #
    #     def __init__(self, session):
    #         self.repository = ProductRepository(session)
    #         async def list_products(self, ...):   # ← 局部函数
    #             ...
    #
    # 结果有三个：
    #   1. 它没有挂到 ProductService 类上 → 类上没有这个属性
    #   2. 它从来没有被调用过 → 定义完就丢了
    #   3. router 里 service.list_products(...) 找不到它 → AttributeError
    #
    # 修法：把 def 的缩进从 8 空格改成 4 空格，和 __init__ 平级。
    #
    # 记忆口诀：类里面的方法，缩进必须和 __init__ 一样。
    #          比 __init__ 更深一层的，是"函数里套函数"，不是类方法。
    # ============================================================
    async def list_products(
        self,
        category: str | None = None,
    ) -> list[ProductResponse]:
        # Repository 返回的是 ORM 对象（Product 实例），
        # 这里显式转成 ProductResponse，好处是：
        #   1. 类型标注是真的（返回值确实是 ProductResponse，不是 ORM 对象）
        #   2. service 可以被单独单元测试，不依赖 FastAPI 的 response_model
        # 前提：ProductResponse 里要配 model_config = ConfigDict(from_attributes=True)
        rows = await self.repository.find_by_category(category)
        return [ProductResponse.model_validate(row) for row in rows]
