from typing import List, Optional

from .card import Card
from .deck import Deck
from .player import Player
from .round import Round
from .rulebook import Rulebook
from .state import GameState
from .turn import Turn


class Game:
    """游戏总控对象，负责初始化、发牌、回合推进与胜负判断。"""

    def __init__(self, player_names: Optional[List[str]] = None) -> None:
        self.player_names = player_names or ["你", "AI-1", "AI-2", "AI-3"]
        self.players: List[Player] = []
        self.deck = Deck()
        self.current_round: Optional[Round] = None
        self.winner: Optional[Player] = None
        self.phase = "idle"
        self.round_number = 0
        self.state = GameState()

    def start_new_game(self) -> None:
        """开始新局，重置玩家和牌堆。"""
        self.deck = Deck()
        self.deck.shuffle()
        self.players = []
        for index, name in enumerate(self.player_names):
            team_id = 0 if index < 2 else 1
            self.players.append(Player(name=name, team_id=team_id, is_human=(index == 0)))
        self.deck.deal_to_players(self.players, cards_per_player=Rulebook.CARDS_PER_PLAYER)
        self.current_round = Round(self.players)
        self.round_number = 1
        self.phase = "ready"
        self.winner = None
        self.state = GameState(phase="ready", log=["新局开始"])

    def check_winner(self) -> Optional[Player]:
        """检查是否有玩家手牌为空，若为空则视为胜负。"""
        for player in self.players:
            if not player.hand:
                self.winner = player
                self.phase = "finished"
                return player
        return None

    def check_winner_team(self) -> Optional[int]:
        """判断哪个队伍先完成出完手牌。"""
        for team_id in [0, 1]:
            team_players = [player for player in self.players if player.team_id == team_id]
            if all(not player.hand for player in team_players):
                self.phase = "finished"
                return team_id
        return None

    def play_turn(self, player: Player, cards: List[Card]) -> Turn:
        """在当前回合中执行一次出牌动作。"""
        if self.current_round is None:
            raise ValueError("当前没有可用回合对象")
        turn = self.current_round.play_turn(player, cards)
        if turn.is_valid:
            self.phase = "playing"
            self.state.phase = "playing"
            self.state.current_turn_count += 1
            self.state.current_player_index = self.current_round.current_player_index
            self.state.last_played_cards = list(cards)
            self.state.last_player_name = player.name
            self.state.add_log(f"{player.name} 出牌: {', '.join(str(card) for card in cards)}")
        return turn

    def handle_contribution(self, from_player: Player, cards: List[Card]) -> None:
        """处理进贡逻辑。"""
        if not cards:
            raise ValueError("进贡牌不能为空")
        from_player.give_contribution(cards)

    def handle_return_contribution(self, from_player: Player, cards: List[Card]) -> None:
        """处理还贡逻辑。"""
        if not cards:
            raise ValueError("还贡牌不能为空")
        from_player.return_contribution(cards)

    def get_team_status(self) -> dict:
        """返回双方队伍状态。"""
        team_a = [player for player in self.players if player.team_id == 0]
        team_b = [player for player in self.players if player.team_id == 1]
        return {
            "team_a": [player.to_dict() for player in team_a],
            "team_b": [player.to_dict() for player in team_b],
        }

    def to_dict(self) -> dict:
        """序列化当前游戏状态。"""
        return {
            "round_number": self.round_number,
            "players": [player.to_dict() for player in self.players],
            "winner": self.winner.name if self.winner else None,
            "phase": self.phase,
            "state": self.state.to_dict(),
        }
