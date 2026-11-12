"""
产品模块的数据库映射（SQLAlchemy 2.0 Annotated Declarative Table 风格）。

一个类 = 一张表，一个属性 = 一列，一个实例 = 一行。
"""

from decimal import Decimal

from sqlalchemy import ARRAY, BigInteger, Numeric, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import Base, CreateAtMixin, UpdateAtMixin


# ============================================================
# ⚠️ 继承顺序：Mixin 写在 Base 前面
#
# 原来是 class Product(Base, CreateAtMixin, UpdateAtMixin)
# 官方文档的写法是 Mixin 在前、Base 在后：
#     class User(Base, TimestampMixin)      ← 不推荐
#     class User(TimestampMixin, Base)      ← 官方风格
#
# 为什么？MRO（方法解析顺序）从左往右找。
# Mixin 里的 mapped_column 需要被 declarative 扫描到，
# Mixin 放前面语义更清晰；一旦 Mixin 用到了 declared_attr，
# 顺序错了会直接报错。现在改过来，以后加别的 Mixin 不会踩坑。
# ============================================================
class Product(CreateAtMixin, UpdateAtMixin, Base):
    """保险产品"""

    __tablename__ = "products"
    # ↑ 数据库里真实的表名，这个必须有，否则 SQLAlchemy 直接报错

    # BigInteger → PostgreSQL 的 BIGINT，配合主键会生成 BIGSERIAL（自增）
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Mapped[str]（没有 | None）→ SQLAlchemy 自动生成 NOT NULL
    # 这就是 2.0 的好处：不用再写 nullable=False，类型即约束
    name: Mapped[str] = mapped_column(String(200))
    clause_name: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(50))
    insurer: Mapped[str] = mapped_column(String(120))

    # Mapped[str | None] → 允许 NULL，等价于老写法的 nullable=True
    image_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    # 金额用 Numeric(14, 2) + Decimal，绝对不要用 Float
    # Numeric(14,2) = 总共 14 位数字，其中小数 2 位，最大 999999999999.99
    # 用 float 会出现 199.99999999 这种精度问题，算钱会错
    min_premium: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    max_premium: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    target_group: Mapped[str | None] = mapped_column(String(300))

    # ============================================================
    # ✅ 已加 MutableList 包装，修掉一个"静默丢数据"的坑
    #
    # ARRAY 是 PostgreSQL 专有类型（你们用的就是 PG，没问题）。
    # 但它有个经典陷阱：SQLAlchemy 追踪不到"原地修改"。
    #
    #     p = await session.get(Product, 1)
    #     p.highlights.append("新亮点")   # 不报错
    #     await session.commit()          # 什么都没写进去！
    #
    # 因为 SQLAlchemy 判断"字段有没有变化"是看对象身份，
    # 原地 append 后还是同一个 list 对象，它认为没变。
    #
    # 两种解法：
    #   A. 用 MutableList.as_mutable(...) 包一层（本文件采用）
    #   B. 每次整体重新赋值：p.highlights = [*p.highlights, "新亮点"]
    # ============================================================
    highlights: Mapped[list[str] | None] = mapped_column(
        MutableList.as_mutable(ARRAY(Text))
    )

    # status 目前用普通字符串，靠应用层保证取值。
    # 想要数据库层面也拦住脏数据，可以改成 Enum：
    #     status: Mapped[ProductStatus] = mapped_column(
    #         Enum(ProductStatus, name="product_status", native_enum=False, length=30)
    #     )
    # 现在这样也能跑，等真的写进 "Active"/"ACTIVE" 混用时再改。
    status: Mapped[str] = mapped_column(
        String(30),
        default="active",          # Python 层默认值：Product() 时自动填
        server_default="active",   # 数据库层默认值：直接用原生 SQL INSERT 也生效
        # 两个都写是双保险，分别管"ORM 插入"和"绕过 ORM 的插入"
    )


# ============================================================
# 建表说明（已核实）
#
# 全仓库搜不到 Base.metadata.create_all()，也没装 alembic。
# 但已确认数据库 insurance 里 products 表是存在的：
#     public.products —— 14 个字段，结构与本文件完全一致，当前 12 行数据
# 说明这张表是早先用一次性脚本建好的。
#
# 需要注意的风险：
#   以后你改了本文件的字段（加列/改类型），数据库不会自动跟着变。
#   开发阶段可以临时用下面这段重建：
#        from app.common.models import Base
#        from app.infra.database import engine
#        from app.modules.product.models import Product  # 必须 import，模型才会注册
#        async with engine.begin() as conn:
#            await conn.run_sync(Base.metadata.create_all)
#   但只要项目要上线，就必须换成 alembic 做迁移，否则生产库会炸。
# ============================================================
