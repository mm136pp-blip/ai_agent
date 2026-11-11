from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
# 启动
from  app.core.config import  settings
from  app.core.logging import  get_logger , configure_logging

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



@app.get('/health',summary='健康检查')
async def health_check() -> dict[str, str]:
    logger.info("执行健康检查")
    return {"status": "ok"}


# 按装订区域中的绿色按钮以运行脚本。
if __name__ == '__main__':
    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
        reload=False,
    )