"""
接口出入参模型（Pydantic Schema）。

注意：这个文件不是数据库映射表！
- 数据库表结构 → app/modules/product/models.py
- 接口出参结构 → 本文件
两者分开的好处：数据库字段可以随便改，只要接口字段不变，前端就不用动。
"""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    """保险产品响应结果（出参）"""

    # ✅ 必加：允许直接从 SQLAlchemy 的 ORM 对象构造，不用手动转 dict
    #    有了它，才能写 ProductResponse.model_validate(product_orm_obj)
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    clause_name: str
    category: str
    insurer: str

    # ============================================================
    # ⚠️ 第三个 bug：可空性没和数据库模型对齐
    #
    # models.py 里这三个字段是 Mapped[xxx | None]（数据库允许 NULL），
    # 但这里原来写成了非可选类型：
    #
    #     image_url: str            ← 模型是 str | None
    #     description: str          ← 模型是 str | None
    #     highlights: list[str]     ← 模型是 list[str] | None
    #
    # 后果：数据库里只要有一条记录的 image_url 是 NULL，
    #       FastAPI 做 response_model 校验时就会抛
    #       ResponseValidationError → 整个接口 500。
    #       而你会以为"查询写错了"，其实是出参类型写错了。
    #
    # 规则：模型可空 → Schema 必须也写上 | None，并给个默认值 None。
    # ============================================================
    image_url: str | None = None
    description: str | None = None

    min_premium: Decimal | None = None
    max_premium: Decimal | None = None
    target_group: str | None = None

    highlights: list[str] | None = None

    status: str
