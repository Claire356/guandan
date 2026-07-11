"""FastAPI 请求与响应模型。"""

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class StartGameRequest(BaseModel):
    """开始游戏时使用的四名玩家名称。"""

    player_names: List[str] = Field(
        default_factory=lambda: ["你", "AI-1", "AI-2", "AI-3"],
        min_length=4,
        max_length=4,
    )


class PlayRequest(BaseModel):
    """按当前玩家手牌下标选择准备出的牌。"""

    card_indices: List[int] = Field(min_length=1)


class RecommendRequest(BaseModel):
    """选择规则 AI 风格；推荐接口不会执行出牌。"""

    strategy: Literal["aggressive", "balanced", "conservative"] = "balanced"


class GameResponse(BaseModel):
    """游戏状态响应。"""

    success: bool = True
    game: Dict[str, Any]


class ActionResponse(GameResponse):
    """出牌或过牌响应。"""

    turn: Dict[str, Any]


class RecommendResponse(BaseModel):
    """AI 推荐结果响应。"""

    success: bool = True
    should_pass: bool
    cards: List[Dict[str, Any]]
    card_type: Dict[str, Any]


class HistoryResponse(BaseModel):
    """当前牌局历史响应。"""

    success: bool = True
    logs: List[str]
    turns: List[Dict[str, Any]]


class ErrorDetail(BaseModel):
    """统一错误详情。"""

    code: int
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    """统一错误响应。"""

    success: bool = False
    error: ErrorDetail
