"""兼容入口：推荐使用 ``uvicorn app.main:app`` 从 backend 目录启动。"""

from .app.main import app


__all__ = ["app"]
