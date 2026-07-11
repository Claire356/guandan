"""运行 100 局规则 AI，并将每一步行为写入 SQLite。"""

import json
from collections import Counter
from typing import Dict, List

from .ai_player import Aggressive, Balanced, Conservative
from .behavior_tracker import BehaviorTracker
from .game import Game
from ..database.sqlite import BehaviorLog, list_behavior_logs


def simulate_games(game_count: int = 100) -> Dict[str, object]:
    """模拟指定局数，返回行为汇总；默认按需求运行 100 局。"""
    strategy_classes = [Aggressive, Balanced, Conservative, Balanced]
    totals = Counter()
    generated_log_ids: List[int] = []

    for game_index in range(game_count):
        game = Game(["Aggressive", "Balanced-A", "Conservative", "Balanced-B"])
        game.start_new_game()
        rotated = strategy_classes[game_index % 4:] + strategy_classes[:game_index % 4]
        agents = {
            player: strategy(game, player)
            for player, strategy in zip(game.players, rotated)
        }
        tracker = BehaviorTracker(game)

        for step_index in range(2000):
            if game.winner is not None:
                break
            round_obj = game.current_round
            if round_obj is None:
                raise RuntimeError("模拟过程中回合对象意外丢失")
            player = round_obj.players[round_obj.current_player_index]
            # 固定频率模拟用户查看 AI 建议，确保点击行为也经过真实持久化路径。
            log = tracker.execute_ai_turn(
                agents[player],
                recommendation_clicked=(step_index % 10 == 0),
            )
            generated_log_ids.append(log.id)
            detail = tracker.detail(log)
            totals["steps"] += 1
            totals["passes"] += int(detail["passed"])
            totals["bombs_used"] += int(detail["bomb_used"])
            totals["helped_partner"] += int(detail["helped_partner"])
            totals["split_cards"] += int(detail["split_cards"])
            totals["critical_decisions"] += int(detail["critical_decision"])
        else:
            raise RuntimeError(f"第 {game_index + 1} 局未在限制步数内结束")

        tracker.finish_game()
        totals["games"] += 1
        totals["recommendation_clicks"] += tracker.recommendation_click_count
        totals[f"wins_{agents[game.winner].style}"] += 1

    # 查询本次最新日志并输出可读样本，完整日志均保存在 game.db。
    latest_logs = list_behavior_logs(limit=10)
    samples = [
        {
            "id": log.id,
            "game_record_id": log.game_record_id,
            "player_name": log.player_name,
            "behavior_type": log.behavior_type,
            "detail": json.loads(log.detail_json),
        }
        for log in latest_logs
        if isinstance(log, BehaviorLog)
    ]
    return {
        "summary": dict(totals),
        "written_game_step_logs": len(generated_log_ids),
        "latest_logs": samples,
    }


def main() -> None:
    """命令行执行入口。"""
    print(json.dumps(simulate_games(100), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
