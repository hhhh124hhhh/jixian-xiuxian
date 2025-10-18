"""
极简修仙游戏模型层 - 组件化架构设计
实现角色状态、动作系统、规则引擎的解耦
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RealmLevel(Enum):
    """修仙境界枚举"""
    QI_REFINING = "炼气期"
    FOUNDATION = "筑基期"
    CORE_FORMATION = "结丹期"
    NASCENT_SOUL = "元婴期"
    SPIRITUAL_TRANSFORMATION = "化神期"
    ASCENSION = "飞升"


@dataclass
class ActionResult:
    """动作执行结果"""
    success: bool
    message: str
    effects: Dict[str, int]
    costs: Dict[str, int]


@dataclass
class Cost:
    """动作消耗"""
    hp: int = 0
    mp: int = 0
    pills: int = 0
    time: int = 0


class HealthComponent:
    """生命值组件"""
    def __init__(self, max_hp: int = 100):
        self.max_hp = max_hp
        self.current_hp = max_hp
        self.recovery_rate = 1.0

    def restore(self, amount: int) -> int:
        """恢复生命值"""
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old_hp

    def consume(self, amount: int) -> int:
        """消耗生命值"""
        old_hp = self.current_hp
        self.current_hp = max(0, self.current_hp - amount)
        return old_hp - self.current_hp

    def is_alive(self) -> bool:
        """是否存活"""
        return self.current_hp > 0

    def get_hp_percentage(self) -> float:
        """获取生命值百分比"""
        return self.current_hp / self.max_hp


class ManaComponent:
    """仙力值组件"""
    def __init__(self, max_mp: int = 100):
        self.max_mp = max_mp
        self.current_mp = max_mp // 2  # 初始为一半
        self.recovery_rate = 1.0

    def restore(self, amount: int) -> int:
        """恢复仙力值"""
        old_mp = self.current_mp
        self.current_mp = min(self.max_mp, self.current_mp + amount)
        return self.current_mp - old_mp

    def consume(self, amount: int) -> bool:
        """消耗仙力值"""
        if self.current_mp >= amount:
            self.current_mp -= amount
            return True
        return False

    def get_mp_percentage(self) -> float:
        """获取仙力值百分比"""
        return self.current_mp / self.max_mp


class ExperienceComponent:
    """经验值组件 - 累积制"""
    def __init__(self):
        self.total_experience = 0  # 总累积经验
        self.current_level_experience = 0  # 当前境界的经验
        self.current_realm = RealmLevel.QI_REFINING

        # 各境界所需经验阈值
        self.realm_thresholds = {
            RealmLevel.QI_REFINING: 100,
            RealmLevel.FOUNDATION: 200,
            RealmLevel.CORE_FORMATION: 400,
            RealmLevel.NASCENT_SOUL: 800,
            RealmLevel.SPIRITUAL_TRANSFORMATION: 1600,
            RealmLevel.ASCENSION: float('inf')  # 飞升不需要经验
        }

    def add_experience(self, amount: int) -> Tuple[bool, Optional[str]]:
        """添加经验值，返回(是否突破, 突破消息)"""
        self.total_experience += amount
        self.current_level_experience += amount

        # 检查是否可以突破
        threshold = self.realm_thresholds[self.current_realm]
        if self.current_level_experience >= threshold and self.current_realm != RealmLevel.ASCENSION:
            # 尝试突破
            realms = list(RealmLevel)
            current_index = realms.index(self.current_realm)
            if current_index < len(realms) - 1:
                self.current_realm = realms[current_index + 1]
                self.current_level_experience = self.current_level_experience - threshold
                return True, f"突破至 {self.current_realm.value}！"

        return False, None

    def get_progress_percentage(self) -> float:
        """获取当前境界进度百分比"""
        threshold = self.realm_thresholds[self.current_realm]
        if threshold == float('inf'):
            return 100.0
        return min(100.0, (self.current_level_experience / threshold) * 100)


class TalentComponent:
    """资质组件"""
    def __init__(self, talent_value: int = None):
        if talent_value is None:
            import random
            talent_value = random.randint(1, 10)
        self.base_talent = talent_value

    def get_talent_bonus(self, base_value: float, action_type: str) -> float:
        """根据动作类型获取资质加成"""
        talent_multipliers = {
            "meditate": 0.8,      # 打坐修炼
            "cultivate": 1.5,     # 修炼功法
            "pill": 1.0,          # 服用丹药
        }
        multiplier = talent_multipliers.get(action_type, 1.0)
        return base_value + (self.base_talent * multiplier)


class InventoryComponent:
    """物品栏组件"""
    def __init__(self):
        self.items = {
            "pill": 0  # 丹药数量
        }

    def add_item(self, item_name: str, amount: int) -> bool:
        """添加物品"""
        if item_name in self.items:
            self.items[item_name] += amount
            return True
        return False

    def consume_item(self, item_name: str, amount: int) -> bool:
        """消耗物品"""
        if item_name in self.items and self.items[item_name] >= amount:
            self.items[item_name] -= amount
            return True
        return False

    def get_item_count(self, item_name: str) -> int:
        """获取物品数量"""
        return self.items.get(item_name, 0)


class CharacterStats:
    """角色状态管理类 - 组件化设计"""
    def __init__(self, name: str = "无名修士"):
        self.name = name
        self.health = HealthComponent()
        self.mana = ManaComponent()
        self.experience = ExperienceComponent()
        self.talent = TalentComponent()
        self.inventory = InventoryComponent()

        # 行为计数器
        self.meditation_streak = 0  # 连续打坐次数
        self.total_actions = 0  # 总行动次数

    def is_alive(self) -> bool:
        """角色是否存活"""
        return self.health.is_alive()

    def can_perform_action(self, cost: Cost) -> bool:
        """检查是否可以执行动作（考虑消耗）"""
        return (
            self.health.current_hp >= cost.hp and
            self.mana.current_mp >= cost.mp and
            self.inventory.get_item_count("pill") >= cost.pills
        )

    def apply_cost(self, cost: Cost) -> bool:
        """应用动作消耗"""
        if not self.can_perform_action(cost):
            return False

        self.health.consume(cost.hp)
        self.mana.consume(cost.mp)
        self.inventory.consume_item("pill", cost.pills)
        self.total_actions += 1
        return True

    def get_status_summary(self) -> Dict[str, any]:
        """获取状态摘要"""
        return {
            "name": self.name,
            "hp": self.health.current_hp,
            "max_hp": self.health.max_hp,
            "mp": self.mana.current_mp,
            "max_mp": self.mana.max_mp,
            "realm": self.experience.current_realm.value,
            "exp": self.experience.current_level_experience,
            "exp_progress": self.experience.get_progress_percentage(),
            "total_exp": self.experience.total_experience,
            "talent": self.talent.base_talent,
            "pills": self.inventory.get_item_count("pill"),
            "meditation_streak": self.meditation_streak,
            "alive": self.is_alive()
        }


class GameLog:
    """游戏日志组件"""
    def __init__(self, max_entries: int = 100):
        self.entries = []
        self.max_entries = max_entries

    def add_entry(self, message: str):
        """添加日志条目"""
        self.entries.append(message)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_recent_entries(self, count: int = 8) -> List[str]:
        """获取最近的日志条目"""
        return self.entries[-count:] if self.entries else ["开始你的修仙之旅..."]