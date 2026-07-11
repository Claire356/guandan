"""FastAPI 应用入口。"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.errors import register_exception_handlers
from .api.router import router
from .database.sqlite import init_db


app = FastAPI(
    title="AI 掼蛋训练 API",
    version="1.0.0",
    description="基于内存游戏引擎的掼蛋训练接口。",
)
allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
app.include_router(router)
register_exception_handlers(app)


@app.get("/health", tags=["system"])
def health_check():
    """提供轻量启动检查。"""
    return {"status": "ok"}
