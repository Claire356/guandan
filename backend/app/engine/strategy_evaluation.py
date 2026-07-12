"""规则 AI 的可复现 100 局策略评估与 CSV 输出。"""

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Type

from .ai_player import Aggressive, Balanced, BOMB_TYPES, Conservative, RuleAIPlayer
from .card_type import identify_card_type, is_wild_card
from .game import Game


STRATEGIES: List[Type[RuleAIPlayer]] = [Aggressive, Balanced, Conservative, Balanced]


def _same_cards(left, right) -> bool:
    return Counter(left) == Counter(right)


def simulate_strategy_games(game_count: int = 100, seed: int = 20260712) -> Dict[str, dict]:
    """模拟指定局数并返回按策略聚合的决策指标。"""
    random.seed(seed)
    metrics = defaultdict(Counter)

    for game_index in range(game_count):
        game = Game(["Aggressive", "Balanced-A", "Conservative", "Balanced-B"])
        game.start_new_game()
        rotated = STRATEGIES[game_index % 4:] + STRATEGIES[:game_index % 4]
        agents = {player: strategy(game, player) for player, strategy in zip(game.players, rotated)}
        for agent in agents.values():
            metrics[agent.style]["agent_entries"] += 1

        for _ in range(2000):
            if game.winner is not None:
                break
            round_obj = game.current_round
            player = round_obj.players[round_obj.current_player_index]
            ai = agents[player]
            style = ai.style
            hand_before = list(player.hand)
            previous_player = round_obj.last_player
            current_type = ai._current_card_type()
            legal = ai._legal_candidates(current_type)
            details = ai.recommend_with_reason()
            recommended = details["recommend_cards"]
            # 模拟采纳推荐：直接执行同一推荐，避免为了统计再次重复计算候选集。
            if recommended:
                turn = game.play_turn(player, recommended)
                game.check_winner()
            else:
                turn = round_obj.play_turn(player, [], is_pass=True)
                game.state.current_player_index = round_obj.current_player_index
                game.state.current_turn_count += 1
                if len(round_obj.turn_history) >= 3 and all(item.is_pass for item in round_obj.turn_history[-3:]):
                    round_obj.last_played_cards = None
                    round_obj.last_player = None
                    game.state.last_played_cards = None
                    game.state.last_player_name = None

            action_type = identify_card_type(turn.cards, game.state.current_level)
            bomb_used = action_type["type"] in BOMB_TYPES
            non_bomb_legal = [cards for cards in legal if identify_card_type(cards, game.state.current_level)["type"] not in BOMB_TYPES]
            partner_control = bool(previous_player and previous_player is not player and previous_player.team_id == player.team_id)
            helped_partner = bool(turn.is_pass and partner_control)
            opponent_endgame = any(item.team_id != player.team_id and len(item.hand) <= 5 for item in game.players)
            metrics[style]["decisions"] += 1
            metrics[style]["recommendations"] += 1
            metrics[style]["adopted"] += int((turn.is_pass and not recommended) or _same_cards(turn.cards, recommended))
            metrics[style]["bombs_used"] += int(bomb_used)
            metrics[style]["helped_partner"] += int(helped_partner)
            metrics[style]["expected_value_sum"] += float(details["expected_value"])
            metrics[style]["expected_value_count"] += 1

            if bomb_used and current_type is not None and current_type["type"] not in BOMB_TYPES and len(hand_before) > 8 and not opponent_endgame and non_bomb_legal:
                metrics[style]["wasted_bombs"] += 1
            if partner_control and not turn.is_pass and len(turn.cards) != len(hand_before):
                metrics[style]["partner_misses"] += 1

            wild_in_hand = any(is_wild_card(card, game.state.current_level) for card in hand_before)
            wild_candidates = [
                cards for cards in legal
                if any(is_wild_card(card, game.state.current_level) for card in cards)
                and identify_card_type(cards, game.state.current_level)["type"] not in BOMB_TYPES
            ]
            if wild_in_hand and wild_candidates and not partner_control:
                best_wild_size = max(map(len, wild_candidates))
                if not any(is_wild_card(card, game.state.current_level) for card in turn.cards) and best_wild_size > len(turn.cards):
                    metrics[style]["wildcard_misses"] += 1

            if len(hand_before) <= 8:
                metrics[style]["endgame_decisions"] += 1
                max_cards = max((len(cards) for cards in legal), default=0)
                correct = helped_partner or (not turn.is_pass and len(turn.cards) == max_cards) or (turn.is_pass and not legal)
                metrics[style]["endgame_correct"] += int(correct)
        else:
            raise RuntimeError(f"第{game_index + 1}局超过最大步数")

        winner_style = agents[game.winner].style
        metrics[winner_style]["wins"] += 1

    return {style: dict(values) for style, values in metrics.items()}


def build_rows(raw: Dict[str, dict], game_count: int) -> List[dict]:
    rows = []
    total = Counter()
    for style in ("aggressive", "balanced", "conservative"):
        item = Counter(raw.get(style, {}))
        total.update(item)
        decisions = item["decisions"] or 1
        endgames = item["endgame_decisions"] or 1
        rows.append({
            "strategy": style,
            "simulated_games": game_count,
            "recommendation_adoption_rate": round(item["adopted"] / (item["recommendations"] or 1), 4),
            "ai_win_rate": round(item["wins"] / (item["agent_entries"] or 1), 4),
            "bomb_usage_rate": round(item["bombs_used"] / decisions, 4),
            "endgame_accuracy": round(item["endgame_correct"] / endgames, 4),
            "help_partner_count": item["helped_partner"],
            "expected_value": round(item["expected_value_sum"] / (item["expected_value_count"] or 1), 4),
            "wasted_bombs": item["wasted_bombs"],
            "partner_misses": item["partner_misses"],
            "wildcard_misses": item["wildcard_misses"],
        })
    decisions = total["decisions"] or 1
    rows.append({
        "strategy": "overall",
        "simulated_games": game_count,
        "recommendation_adoption_rate": round(total["adopted"] / (total["recommendations"] or 1), 4),
        "ai_win_rate": round(total["wins"] / (total["agent_entries"] or 1), 4),
        "bomb_usage_rate": round(total["bombs_used"] / decisions, 4),
        "endgame_accuracy": round(total["endgame_correct"] / (total["endgame_decisions"] or 1), 4),
        "help_partner_count": total["helped_partner"],
        "expected_value": round(total["expected_value_sum"] / (total["expected_value_count"] or 1), 4),
        "wasted_bombs": total["wasted_bombs"],
        "partner_misses": total["partner_misses"],
        "wildcard_misses": total["wildcard_misses"],
    })
    return rows


def write_csv(rows: List[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument("--output", type=Path, default=Path("backend/reports/ai_strategy_100_games.csv"))
    args = parser.parse_args()
    rows = build_rows(simulate_strategy_games(args.games, args.seed), args.games)
    write_csv(rows, args.output)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    print(args.output)


if __name__ == "__main__":
    main()
