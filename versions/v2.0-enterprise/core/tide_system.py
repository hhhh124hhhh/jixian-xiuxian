import copy
import random
from typing import Optional


# 灵气潮汐效果池
TIDE_EFFECTS = [
    {
        "action": "cultivate",
        "stat": "exp",
        "ratio": 0.15,
        "label": "下次修炼经验 +15%",
        "tone": "buff"
    },
    {
        "action": "meditate",
        "stat": "mp",
        "ratio": 0.15,
        "label": "下次打坐回蓝 +15%",
        "tone": "buff"
    },
    {
        "action": "cultivate",
        "stat": "exp",
        "ratio": -0.10,
        "label": "下次修炼经验 -10%",
        "tone": "debuff"
    },
    {
        "action": "meditate",
        "stat": "mp",
        "ratio": -0.10,
        "label": "下次打坐回蓝 -10%",
        "tone": "debuff"
    }
]


class TideSystem:
    """灵气潮汐系统"""

    def __init__(self):
        self.action_count = 0
        self.pending = None
        self.total_triggered = 0

    def check_and_consume(
        self,
        action_name: str,
        result,
        character
    ) -> Optional[dict]:
        """消耗与当前动作匹配的待生效潮汐效果。"""
        if self.pending and self.pending["action"] == action_name:
            tide = self.pending
            stat = tide["stat"]
            ratio = tide["ratio"]

            if stat == "exp":
                before = result.effects.get("exp_gain", 0)
                delta = int(round(before * ratio))
                if delta != 0:
                    character.experience.add_experience(delta)
                    result.effects["exp_gain"] += delta
                after = before + delta
            else:
                before = result.effects.get("mp_recovery", 0)
                delta = int(round(before * ratio))
                if delta >= 0:
                    character.mana.restore(delta)
                else:
                    character.mana.current_mp = max(
                        0,
                        character.mana.current_mp + delta
                    )
                result.effects["mp_recovery"] += delta
                after = before + delta

            self.pending = None

            return {
                "label": tide["label"],
                "tone": tide["tone"],
                "before": before,
                "after": after
            }

        return None

    def register_action(self, result) -> Optional[dict]:
        """登记成功动作并在达到阈值时触发潮汐。"""
        if result.effects.get("level_up"):
            return None

        self.action_count += 1

        if self.action_count >= 5:
            self.pending = copy.deepcopy(random.choice(TIDE_EFFECTS))
            self.action_count = 0
            self.total_triggered += 1

            return {
                "effect": dict(self.pending),
                "total": self.total_triggered
            }

        return None
