"""为每局 AI 玩家生成可替换的头像与昵称。"""

import random
from typing import Dict, List, Optional, Sequence


class AvatarProvider:
    """头像提供器接口。

    当前实现从经过筛选的 500×500 真人头像地址中无重复抽取。以后接入 AI
    图片服务时，只需继承此类并重写 ``generate``，游戏与前端接口无需变化。
    """

    STYLES: Sequence[str] = (
        "都市时尚风", "潮流电竞风", "国风写真", "二次元真人写真风", "高颜值美女", "高颜值帅哥",
    )
    # pravatar 提供固定编号的高清方形真人头像；通过 size=500 保持展示规格一致。
    AVATAR_IDS: Sequence[int] = tuple(range(1, 71))

    def __init__(self, random_source: Optional[random.Random] = None) -> None:
        self.random = random_source or random.SystemRandom()

    def generate(self, count: int = 3) -> List[Dict[str, str]]:
        """生成本局互不重复的头像资料。"""
        if count < 0 or count > len(self.AVATAR_IDS):
            raise ValueError("头像数量超出可用范围")
        avatar_ids = self.random.sample(list(self.AVATAR_IDS), count)
        styles = list(self.STYLES)
        self.random.shuffle(styles)
        return [
            {
                "url": f"https://i.pravatar.cc/500?img={avatar_id}",
                "style": styles[index % len(styles)],
                "width": 500,
                "height": 500,
            }
            for index, avatar_id in enumerate(avatar_ids)
        ]


class NameProvider:
    """五个汉字以内的年轻化 AI 昵称提供器。"""

    NAMES: Sequence[str] = (
        "牌圣", "炸到底", "别管我", "稳住哥", "天选人", "王炸王", "冲冲冲", "赌一手",
        "别炸我", "过过过", "小钢板", "小对子", "同花顺", "六六六", "起飞啦", "别送了",
        "快上车", "逆风局", "听我炸", "牌桌显眼包", "拿捏了", "稳稳上分", "牌运爆棚",
        "主打陪伴", "别催在想", "一手拿下", "今天必胜", "上桌开冲", "绝不白给",
    )

    def __init__(self, random_source: Optional[random.Random] = None) -> None:
        self.random = random_source or random.SystemRandom()

    def generate(self, count: int = 3, excluded: Optional[Sequence[str]] = None) -> List[str]:
        """在本局内无重复抽取昵称，并排除真人玩家已有名称。"""
        blocked = set(excluded or ())
        candidates = [name for name in self.NAMES if name not in blocked and len(name) <= 5]
        if count < 0 or count > len(candidates):
            raise ValueError("昵称数量超出可用范围")
        return self.random.sample(candidates, count)


__all__ = ["AvatarProvider", "NameProvider"]
