from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime, func

# SQLAlchemy的基类，所有数据库表模型都必须继承
class Base(DeclarativeBase):
    """
    所有 ORM 模型的基类。

    注意：只有继承了它，SQLAlchemy 才知道"这是个要和数据库打交道的类"。
    __tablename__、mapped_column 这些东西，都是继承之后才会被扫描解析的。
    """

    def __repr__(self) -> str:
        """
        通用 repr，方便 print(对象) 时看到内容，也方便日志排查。

        当前实现是够用的（因为 infra/database.py 里设了
        expire_on_commit=False，commit 后属性不会失效，vars(self) 拿得到值）。

        两个已知的小局限，遇到再改：
        1. 如果哪天把 expire_on_commit 改回 True，
           commit 之后 vars(self) 会变成空字典，打印出来是 User({})。
        2. 顺序跟着"属性被加载的顺序"走，不完全是模型定义的顺序。
           想固定顺序就要用 inspect(self).mapper.column_attrs 遍历。
        """
        cls_name = self.__class__.__name__
        attrs = {}
        for key, val in vars(self).items():
            if key.startswith("_"):
                # 过滤掉 SQLAlchemy 内部字段，比如 _sa_instance_state
                continue
            if isinstance(val, datetime):
                attrs[key] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                attrs[key] = val
        return f"{cls_name}({attrs})"

# 通用的时间戳【混入类】，这样其它数据模型不用重复定义时间相关字段
class CreateAtMixin:
    # func.now() 会让数据库在插入时自动生成服务器时间（如 PostgreSQL 的 NOW()）
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class UpdateAtMixin:
    # onupdate=func.now() 会在每次数据行被 UPDATE 时，由 SQLAlchemy 自动更新该字段
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )