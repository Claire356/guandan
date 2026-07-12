"""SQLite 持久化层，提供游戏记录、行为日志和性格评分 CRUD。"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine, event, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


# 数据库文件固定在 backend/game.db，不受启动命令所在目录影响。
DATABASE_PATH = Path(__file__).resolve().parents[2] / "game.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    """所有数据库模型的声明式基类。"""


class GameRecord(Base):
    """一局游戏的开始、结束、胜者和最终状态。"""

    __tablename__ = "game_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    winner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class BehaviorLog(Base):
    """记录某局中玩家发生的行为。"""

    __tablename__ = "behavior_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_record_id: Mapped[int] = mapped_column(
        ForeignKey("game_record.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    player_name: Mapped[str] = mapped_column(String(100), nullable=False)
    behavior_type: Mapped[str] = mapped_column(String(50), nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PersonalityScore(Base):
    """保存玩家旧版兼容评分与新版五维行为画像。"""

    __tablename__ = "personality_score"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_record_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("game_record.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    player_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    aggressive_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    balanced_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    conservative_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    aggression_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    cooperation_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    emotion_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    decision_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    personality_tags: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class GameActionRecord(Base):
    """附件定义的逐动作明细表，用于百分位画像和跨局统计。"""

    __tablename__ = "game_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cards_played: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    card_type: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    decision_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    opponent_cards: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_bomb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_risky_play: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    partner_action: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    game_result: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PlayerStatistics(Base):
    """附件定义的玩家跨局汇总表。"""

    __tablename__ = "player_statistics"

    player_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    total_games: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_rounds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bombs_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    protect_partner_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    feed_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    break_bomb_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quick_decisions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_decisions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_decision_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    decision_time_variance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# SQLite 默认不强制外键；连接时通过 PRAGMA 开启，确保级联和引用完整性生效。
engine = create_engine(DATABASE_URL, future=True)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """为每个 SQLite 连接开启外键校验。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def init_db() -> None:
    """幂等创建所有表；已有数据库和数据不会被覆盖。"""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # create_all 不会为已有 SQLite 表追加字段，因此执行安全、幂等的增量迁移。
    existing = {column["name"] for column in inspect(engine).get_columns("personality_score")}
    migrations = {
        "aggression_score": "FLOAT NOT NULL DEFAULT 50",
        "cooperation_score": "FLOAT NOT NULL DEFAULT 50",
        "emotion_score": "FLOAT NOT NULL DEFAULT 50",
        "risk_score": "FLOAT NOT NULL DEFAULT 50",
        "decision_score": "FLOAT NOT NULL DEFAULT 50",
        "personality_tags": "TEXT NOT NULL DEFAULT ''",
    }
    with engine.begin() as connection:
        for column, definition in migrations.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE personality_score ADD COLUMN {column} {definition}"))


def _to_json(value: Optional[Dict[str, Any]]) -> str:
    """将可选字典转换为可存储的 JSON 文本。"""
    return json.dumps(value or {}, ensure_ascii=False)


def create_game_record(
    state: Optional[Dict[str, Any]] = None,
    winner: Optional[str] = None,
    ended_at: Optional[datetime] = None,
) -> GameRecord:
    """创建游戏记录。"""
    with SessionLocal() as session:
        record = GameRecord(state_json=_to_json(state), winner=winner, ended_at=ended_at)
        session.add(record)
        session.commit()
        return record


def get_game_record(record_id: int) -> Optional[GameRecord]:
    """按主键查询游戏记录。"""
    with SessionLocal() as session:
        return session.get(GameRecord, record_id)


def list_game_records(limit: int = 100, offset: int = 0) -> List[GameRecord]:
    """分页查询游戏记录，最新记录优先。"""
    with SessionLocal() as session:
        statement = select(GameRecord).order_by(GameRecord.id.desc()).limit(limit).offset(offset)
        return list(session.scalars(statement))


def update_game_record(
    record_id: int,
    state: Optional[Dict[str, Any]] = None,
    winner: Optional[str] = None,
    ended_at: Optional[datetime] = None,
) -> Optional[GameRecord]:
    """更新游戏记录；不存在时返回 None。"""
    with SessionLocal() as session:
        record = session.get(GameRecord, record_id)
        if record is None:
            return None
        if state is not None:
            record.state_json = _to_json(state)
        if winner is not None:
            record.winner = winner
        if ended_at is not None:
            record.ended_at = ended_at
        session.commit()
        return record


def delete_game_record(record_id: int) -> bool:
    """删除游戏记录；返回是否实际删除。"""
    with SessionLocal() as session:
        record = session.get(GameRecord, record_id)
        if record is None:
            return False
        session.delete(record)
        session.commit()
        return True


def create_behavior_log(
    game_record_id: int,
    player_name: str,
    behavior_type: str,
    detail: Optional[Dict[str, Any]] = None,
) -> BehaviorLog:
    """创建行为日志。"""
    with SessionLocal() as session:
        log = BehaviorLog(
            game_record_id=game_record_id,
            player_name=player_name,
            behavior_type=behavior_type,
            detail_json=_to_json(detail),
        )
        session.add(log)
        session.commit()
        return log


def get_behavior_log(log_id: int) -> Optional[BehaviorLog]:
    """按主键查询行为日志。"""
    with SessionLocal() as session:
        return session.get(BehaviorLog, log_id)


def list_behavior_logs(
    game_record_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[BehaviorLog]:
    """分页查询行为日志，也可限定某一局。"""
    with SessionLocal() as session:
        statement = select(BehaviorLog)
        if game_record_id is not None:
            statement = statement.where(BehaviorLog.game_record_id == game_record_id)
        statement = statement.order_by(BehaviorLog.id.desc()).limit(limit).offset(offset)
        return list(session.scalars(statement))


def update_behavior_log(
    log_id: int,
    behavior_type: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
) -> Optional[BehaviorLog]:
    """更新行为日志；不存在时返回 None。"""
    with SessionLocal() as session:
        log = session.get(BehaviorLog, log_id)
        if log is None:
            return None
        if behavior_type is not None:
            log.behavior_type = behavior_type
        if detail is not None:
            log.detail_json = _to_json(detail)
        session.commit()
        return log


def delete_behavior_log(log_id: int) -> bool:
    """删除行为日志；返回是否实际删除。"""
    with SessionLocal() as session:
        log = session.get(BehaviorLog, log_id)
        if log is None:
            return False
        session.delete(log)
        session.commit()
        return True


def create_personality_score(
    player_name: str,
    aggressive_score: float = 0.0,
    balanced_score: float = 0.0,
    conservative_score: float = 0.0,
    game_record_id: Optional[int] = None,
    aggression_score: float = 50.0,
    cooperation_score: float = 50.0,
    emotion_score: float = 50.0,
    risk_score: float = 50.0,
    decision_score: float = 50.0,
    personality_tags: str = "",
) -> PersonalityScore:
    """创建一条玩家性格评分。"""
    with SessionLocal() as session:
        score = PersonalityScore(
            game_record_id=game_record_id,
            player_name=player_name,
            aggressive_score=aggressive_score,
            balanced_score=balanced_score,
            conservative_score=conservative_score,
            aggression_score=aggression_score,
            cooperation_score=cooperation_score,
            emotion_score=emotion_score,
            risk_score=risk_score,
            decision_score=decision_score,
            personality_tags=personality_tags,
        )
        session.add(score)
        session.commit()
        return score


def get_personality_score(score_id: int) -> Optional[PersonalityScore]:
    """按主键查询性格评分。"""
    with SessionLocal() as session:
        return session.get(PersonalityScore, score_id)


def list_personality_scores(
    player_name: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[PersonalityScore]:
    """分页查询性格评分，也可限定玩家名称。"""
    with SessionLocal() as session:
        statement = select(PersonalityScore)
        if player_name is not None:
            statement = statement.where(PersonalityScore.player_name == player_name)
        statement = statement.order_by(PersonalityScore.id.desc()).limit(limit).offset(offset)
        return list(session.scalars(statement))


def update_personality_score(
    score_id: int,
    aggressive_score: Optional[float] = None,
    balanced_score: Optional[float] = None,
    conservative_score: Optional[float] = None,
    aggression_score: Optional[float] = None,
    cooperation_score: Optional[float] = None,
    emotion_score: Optional[float] = None,
    risk_score: Optional[float] = None,
    decision_score: Optional[float] = None,
    personality_tags: Optional[str] = None,
) -> Optional[PersonalityScore]:
    """更新指定评分字段；不存在时返回 None。"""
    with SessionLocal() as session:
        score = session.get(PersonalityScore, score_id)
        if score is None:
            return None
        if aggressive_score is not None:
            score.aggressive_score = aggressive_score
        if balanced_score is not None:
            score.balanced_score = balanced_score
        if conservative_score is not None:
            score.conservative_score = conservative_score
        for field, value in {
            "aggression_score": aggression_score,
            "cooperation_score": cooperation_score,
            "emotion_score": emotion_score,
            "risk_score": risk_score,
            "decision_score": decision_score,
            "personality_tags": personality_tags,
        }.items():
            if value is not None:
                setattr(score, field, value)
        score.updated_at = datetime.utcnow()
        session.commit()
        return score


def delete_personality_score(score_id: int) -> bool:
    """删除性格评分；返回是否实际删除。"""
    with SessionLocal() as session:
        score = session.get(PersonalityScore, score_id)
        if score is None:
            return False
        session.delete(score)
        session.commit()
        return True


def create_game_action_record(
    game_id: str,
    player_id: str,
    action_type: str,
    **fields: Any,
) -> GameActionRecord:
    """实时保存一次玩家操作，并同步最常用的玩家统计计数。"""
    with SessionLocal() as session:
        record = GameActionRecord(game_id=game_id, player_id=player_id, action_type=action_type, **fields)
        session.add(record)
        statistics = session.get(PlayerStatistics, player_id)
        if statistics is None:
            statistics = PlayerStatistics(player_id=player_id)
            session.add(statistics)
        previous_total = statistics.total_decisions
        statistics.total_decisions += 1
        decision_time = float(fields.get("decision_time", 0.0) or 0.0)
        statistics.avg_decision_time = (
            (statistics.avg_decision_time * previous_total + decision_time) / statistics.total_decisions
        )
        if decision_time < 4.0:
            statistics.quick_decisions += 1
        if bool(fields.get("is_bomb", False)):
            statistics.total_bombs_used += 1
        if bool(fields.get("partner_action", False)):
            statistics.protect_partner_count += 1
        statistics.updated_at = datetime.utcnow()
        session.commit()
        return record


def list_game_action_records(player_id: Optional[str] = None, limit: int = 1000) -> List[GameActionRecord]:
    """查询动作明细，可用于跨玩家百分位计算。"""
    with SessionLocal() as session:
        statement = select(GameActionRecord)
        if player_id is not None:
            statement = statement.where(GameActionRecord.player_id == player_id)
        return list(session.scalars(statement.order_by(GameActionRecord.id.asc()).limit(limit)))


__all__ = [
    "DATABASE_PATH",
    "DATABASE_URL",
    "GameRecord",
    "BehaviorLog",
    "PersonalityScore",
    "GameActionRecord",
    "PlayerStatistics",
    "SessionLocal",
    "init_db",
    "create_game_record",
    "get_game_record",
    "list_game_records",
    "update_game_record",
    "delete_game_record",
    "create_behavior_log",
    "get_behavior_log",
    "list_behavior_logs",
    "update_behavior_log",
    "delete_behavior_log",
    "create_personality_score",
    "get_personality_score",
    "list_personality_scores",
    "update_personality_score",
    "delete_personality_score",
    "create_game_action_record",
    "list_game_action_records",
]
