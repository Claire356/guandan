from typing import List, Optional

from .card import Card
from .card_type import BASE_LEVEL, card_strength, is_wild_card
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
        self.current_level = "2"
        self.state = GameState(current_level=self.current_level)

    def start_new_game(self) -> None:
        """开始新局，重置玩家和牌堆。"""
        self.deck = Deck()
        self.deck.shuffle()
        self.players = []
        for index, name in enumerate(self.player_names):
            # 掼蛋对家为队友：0/2一队，1/3一队，不采用相邻座位组队。
            team_id = index % 2
            self.players.append(Player(name=name, team_id=team_id, is_human=(index == 0)))
        self.deck.deal_to_players(self.players, cards_per_player=Rulebook.CARDS_PER_PLAYER)
        # 手牌按点数、花色稳定排序；API 返回顺序与实际手牌顺序一致，出牌下标不会错位。
        suit_order = {"♠": 0, "♥": 1, "♣": 2, "♦": 3, "Joker": 4}
        for player in self.players:
            player.hand.sort(key=lambda card: (card.value, suit_order.get(card.suit, 9), card.color or ""))
        self.current_round = Round(self.players, current_level=self.current_level)
        self.round_number = 1
        self.phase = "ready"
        self.winner = None
        self.state = GameState(current_level=self.current_level, phase="ready", log=[f"新局开始，当前打{self.current_level}"])

    def check_winner(self) -> Optional[Player]:
        """检查是否有玩家手牌为空，若为空则视为胜负。"""
        for player in self.players:
            if not player.hand and player.name not in self.state.finish_order:
                self.state.finish_order.append(player.name)
                if self.winner is None:
                    self.winner = player
                return player
        return None

    @staticmethod
    def upgrade_steps(partner_finish: int) -> int:
        """头游对家二游/三游/末游分别升3/2/1级。"""
        if partner_finish not in (2, 3, 4):
            raise ValueError("头游对家名次必须是2、3或4")
        return {2: 3, 3: 2, 4: 1}[partner_finish]

    def advance_level(self, steps: int) -> str:
        """从打2开始升级，最高到A；同步 GameState 与当前 Round。"""
        levels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        index = min(levels.index(self.current_level) + steps, len(levels) - 1)
        self.current_level = levels[index]
        self.state.current_level = self.current_level
        if self.current_round is not None:
            self.current_round.current_level = self.current_level
        return self.current_level

    def apply_round_upgrade(self, partner_finish: int) -> str:
        """按头游对家名次结算本轮升级。"""
        return self.advance_level(self.upgrade_steps(partner_finish))

    def exchange_tribute(
        self,
        giver: Player,
        receiver: Player,
        tribute_card: Card,
        return_card: Card,
    ) -> None:
        """执行一进一还的同步交换，并保证双方及全桌手牌总数不变。"""
        if tribute_card not in giver.hand or return_card not in receiver.hand:
            raise ValueError("贡牌或还贡牌不在对应玩家手中")
        eligible = [card for card in giver.hand if not is_wild_card(card, self.current_level)]
        if tribute_card not in eligible or card_strength(tribute_card, self.current_level) != max(card_strength(card, self.current_level) for card in eligible):
            raise ValueError("必须进贡除逢人配外最大的牌")
        low_returns = [card for card in receiver.hand if not card.is_joker and BASE_LEVEL.get(card.rank, 99) <= 10]
        if low_returns:
            if return_card not in low_returns:
                raise ValueError("有10及以下牌时必须从中还贡")
        elif return_card != min(receiver.hand, key=lambda card: card_strength(card, self.current_level)):
            raise ValueError("没有10及以下牌时必须还手中最小牌")
        total_before = sum(len(player.hand) for player in self.players)
        giver.hand.remove(tribute_card)
        receiver.hand.remove(return_card)
        giver.receive_cards([return_card])
        receiver.receive_cards([tribute_card])
        if sum(len(player.hand) for player in self.players) != total_before:
            raise RuntimeError("贡还贡后全桌手牌总数发生变化")

    @staticmethod
    def can_resist_tribute(players: List[Player]) -> bool:
        """单下本人或双下双方合计持有两张大王时抗贡。"""
        return sum(1 for player in players for card in player.hand if card.is_joker and card.color == "red") >= 2

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
            "currentLevel": self.current_level,
            "players": [player.to_dict() for player in self.players],
            "winner": self.winner.name if self.winner else None,
            "phase": self.phase,
            "state": self.state.to_dict(),
        }
