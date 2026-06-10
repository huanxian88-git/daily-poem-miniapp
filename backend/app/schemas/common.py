"""通用响应格式和错误码定义。

错误码规范：
    0          = 成功
    40001-40099 = 业务逻辑错误
    40101-40199 = 鉴权错误
    40401-40499 = 资源不存在
    50001-50099 = 服务端错误
"""

from typing import Any, Optional
from pydantic import BaseModel


class ResponseBase(BaseModel):
    """统一响应格式。

    Example:
        {"code": 0, "data": {"token": "xxx"}, "message": "success"}
    """

    code: int = 0
    data: Any = None
    message: str = "success"


class ErrorResponse(BaseModel):
    """错误响应格式。"""

    code: int
    data: Any = None
    message: str


# ---- 错误码常量 ----

# 成功
SUCCESS = 0

# 业务逻辑错误 (40001-40099)
ERR_INVALID_PARAMS = 40001
ERR_USER_NOT_FOUND = 40002

# 鉴权错误 (40101-40199)
ERR_INVALID_CODE = 40101
ERR_WECHAT_API_FAILED = 40102
ERR_TOKEN_EXPIRED = 40103
ERR_TOKEN_INVALID = 40104
ERR_REFRESH_TOKEN_EXPIRED = 40105
ERR_REFRESH_TOKEN_INVALID = 40106

# 资源不存在 (40401-40499)
ERR_NOT_FOUND = 40401

# 服务端错误 (50001-50099)
ERR_INTERNAL = 50001
ERR_DATABASE = 50002
ERR_REDIS = 50003


ERROR_MESSAGES = {
    SUCCESS: "success",
    ERR_INVALID_PARAMS: "Invalid parameters",
    ERR_USER_NOT_FOUND: "User not found",
    ERR_INVALID_CODE: "Invalid WeChat login code",
    ERR_WECHAT_API_FAILED: "WeChat API call failed",
    ERR_TOKEN_EXPIRED: "Access token expired",
    ERR_TOKEN_INVALID: "Invalid access token",
    ERR_REFRESH_TOKEN_EXPIRED: "Refresh token expired",
    ERR_REFRESH_TOKEN_INVALID: "Invalid refresh token",
    ERR_NOT_FOUND: "Resource not found",
    ERR_INTERNAL: "Internal server error",
    ERR_DATABASE: "Database error",
    ERR_REDIS: "Redis error",
}
