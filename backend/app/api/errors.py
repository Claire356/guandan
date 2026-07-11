"""FastAPI 统一异常处理。"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _error_response(status_code: int, message: str, details=None) -> JSONResponse:
    """构造所有接口共用的 JSON 错误结构。"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": status_code, "message": message, "details": details},
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """为应用注册参数、业务和未知异常处理器。"""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(422, "请求参数验证失败", exc.errors())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(exc.status_code, str(exc.detail))

    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
        return _error_response(400, str(exc))

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(500, "服务器内部错误")
