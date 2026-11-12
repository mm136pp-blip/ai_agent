from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
# 启动
from  app.core.config import  settings
from  app.core.logging import  get_logger , configure_logging
# 导入路由
from app.modules.product.router import router as product_router

# 初始化日志系统
configure_logging(settings.logging.level)
# 在那个目录下记录日志
logger = get_logger(__name__)

# 生命周期管理（预留）
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"【{settings.app.name}】应用启动中...")
    from app.infra.database import check_database, close_database
    try:
        await check_database()
        yield
    finally:
        logger.info("应用关闭中... ")
        await close_database()

# 初始化app
app = FastAPI(
    title=settings.app.name,
    debug=settings.app.debug,
    lifespan=lifespan,
)

app.include_router(product_router)


@app.get('/health',summary='健康检查')
async def health_check() -> dict[str, str]:
    logger.info("执行健康检查")
    return {"status": "ok"}


# ============================================================
# ⚠️ 这里有个影响你排查效率的问题：热重载没生效
#
# 原来的写法：uvicorn.run(app, ..., reload=False)
#
# 两个问题：
#   1. reload=False → 改完代码必须手动重启，你说的"方法不存在"
#      如果是因为这个，重启一次就好了。但这种反复试错很浪费时间。
#   2. 传的是 app 对象而不是字符串 "main:app"
#      → 即使写成 reload=True 也不会生效！
#        因为 reload 的原理是"监视文件变化，杀掉进程重新 import 模块"，
#        而 app 对象已经在当前进程里创建好了，没法重新 import。
#
# 正确写法：传 "模块名:变量名" 字符串
#   uvicorn.run("main:app", reload=True)
#
# 注意：reload=True 时 uvicorn 会起一个监视进程 + 一个工作进程，
#       调试断点行为会变，所以不要在生产环境开。
# ============================================================
if __name__ == '__main__':
    uvicorn.run(
        "main:app",                          # ← 字符串形式，reload 才能工作
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,           # debug 模式下自动热重载
    )