"""
极简修仙游戏动作系统
定义所有基础动作的接口和实现
"""

from abc import ABC, abstractmethod
from typing import Optional
from models import CharacterStats, ActionResult, Cost, GameLog


class Action(ABC):
    """动作基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def get_cost(self) -> Cost:
        """获取动作消耗"""
        pass

    @abstractmethod
    def can_execute(self, character: CharacterStats) -> bool:
        """检查是否可以执行动作"""
        pass

    @abstractmethod
    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        """执行动作"""
        pass

    def get_failure_message(self, character: CharacterStats) -> str:
        """获取失败消息"""
        return f"无法执行{self.name}"


class MeditateAction(Action):
    """打坐动作"""

    def __init__(self):
        super().__init__("打坐", "进入冥想状态，恢复仙力并获得少量经验")

    def get_cost(self) -> Cost:
        return Cost(hp=1, time=1)  # 微量消耗生命值

    def can_execute(self, character: CharacterStats) -> bool:
        return character.is_alive()

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 计算效果
        mp_recovery = int(character.talent.get_talent_bonus(8, "meditate"))
        exp_gain = int(character.talent.get_talent_bonus(3, "meditate"))

        # 应用效果
        actual_mp_recovery = character.mana.restore(mp_recovery)
        breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 更新连续打坐计数
        character.meditation_streak += 1

        # 检查连续奖励
        pill_bonus = 0
        if character.meditation_streak % 5 == 0:
            character.inventory.add_item("pill", 1)
            pill_bonus = 1

        # 构建消息
        messages = [f"你进入打坐修炼状态，恢复{actual_mp_recovery}点仙力，获得{exp_gain}点经验"]
        if breakthrough:
            messages.append(breakthrough_msg)
        if pill_bonus > 0:
            messages.append(f"连续打坐{character.meditation_streak}次，获得{pill_bonus}颗丹药！")

        # 记录日志
        log_message = "，".join(messages)
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {
            "mp_recovery": actual_mp_recovery,
            "exp_gain": exp_gain,
            "pill_bonus": pill_bonus
        }
        costs = {"hp": cost.hp, "time": cost.time}

        # 添加等级提升信息
        if breakthrough:
            effects["level_up"] = True
            effects["new_level"] = character.experience.current_realm.value

        return ActionResult(True, log_message, effects, costs)


class ConsumePillAction(Action):
    """服用丹药动作"""

    def __init__(self):
        super().__init__("吃丹药", "服用丹药快速恢复生命力和仙力")

    def get_cost(self) -> Cost:
        return Cost(pills=1)

    def can_execute(self, character: CharacterStats) -> bool:
        return (character.is_alive() and
                character.inventory.get_item_count("pill") >= 1)

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 计算效果（资质影响恢复效果）
        hp_recovery = int(character.talent.get_talent_bonus(15, "pill"))
        mp_recovery = int(character.talent.get_talent_bonus(15, "pill"))
        exp_gain = int(character.talent.get_talent_bonus(5, "pill"))

        # 应用效果
        actual_hp_recovery = character.health.restore(hp_recovery)
        actual_mp_recovery = character.mana.restore(mp_recovery)
        breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 重置连续打坐计数（吃丹药打断连续状态）
        character.meditation_streak = 0

        # 构建消息
        messages = [f"你服下一颗丹药，恢复{actual_hp_recovery}点生命和{actual_mp_recovery}点仙力"]
        if exp_gain > 0:
            messages.append(f"获得{exp_gain}点经验")
        if breakthrough:
            messages.append(breakthrough_msg)

        # 记录日志
        log_message = "，".join(messages) + "。"
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {
            "hp_recovery": actual_hp_recovery,
            "mp_recovery": actual_mp_recovery,
            "exp_gain": exp_gain
        }
        costs = {"pills": cost.pills}

        # 添加等级提升信息
        if breakthrough:
            effects["level_up"] = True
            effects["new_level"] = character.experience.current_realm.value

        return ActionResult(True, log_message, effects, costs)

    def get_failure_message(self, character: CharacterStats) -> str:
        if not character.is_alive():
            return "你已经无法行动"
        elif character.inventory.get_item_count("pill") < 1:
            return "没有丹药可用"
        return "无法服用丹药"


class CultivateAction(Action):
    """修炼功法动作"""

    def __init__(self):
        super().__init__("修炼", "运转心法，大量提升修为")

    def get_cost(self) -> Cost:
        return Cost(mp=20, time=2)  # 消耗仙力和时间

    def can_execute(self, character: CharacterStats) -> bool:
        return (character.is_alive() and
                character.mana.current_mp >= self.get_cost().mp)

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 计算效果（资质主要影响修炼效率）
        exp_gain = int(character.talent.get_talent_bonus(12, "cultivate"))

        # 应用效果
        breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 重置连续打坐计数
        character.meditation_streak = 0

        # 构建消息
        messages = [f"你运转心法，修为精进，获得{exp_gain}点经验"]
        if breakthrough:
            messages.append(breakthrough_msg)

        # 记录日志
        log_message = "，".join(messages) + "。"
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {"exp_gain": exp_gain}
        costs = {"mp": cost.mp, "time": cost.time}

        # 添加等级提升信息
        if breakthrough:
            effects["level_up"] = True
            effects["new_level"] = character.experience.current_realm.value

        return ActionResult(True, log_message, effects, costs)

    def get_failure_message(self, character: CharacterStats) -> str:
        if not character.is_alive():
            return "你已经无法行动"
        elif character.mana.current_mp < self.get_cost().mp:
            return "仙力不足，无法修炼"
        return "无法修炼"


class WaitAction(Action):
    """等待动作"""

    def __init__(self):
        super().__init__("等待", "静心养神，缓慢恢复状态")

    def get_cost(self) -> Cost:
        return Cost(hp=1, time=1)  # 等待也会消耗微量生命

    def can_execute(self, character: CharacterStats) -> bool:
        return character.is_alive()

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 等待的微弱效果
        hp_recovery = 2
        mp_recovery = 3

        # 应用效果
        actual_hp_recovery = character.health.restore(hp_recovery)
        actual_mp_recovery = character.mana.restore(mp_recovery)

        # 重置连续打坐计数
        character.meditation_streak = 0

        # 构建消息
        log_message = f"你静心等待，恢复{actual_hp_recovery}点生命和{actual_mp_recovery}点仙力。"
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {
            "hp_recovery": actual_hp_recovery,
            "mp_recovery": actual_mp_recovery
        }
        costs = {"hp": cost.hp, "time": cost.time}

        return ActionResult(True, log_message, effects, costs)


class ActionFactory:
    """动作工厂类"""

    @staticmethod
    def get_all_actions() -> list:
        """获取所有可用动作"""
        return [
            MeditateAction(),
            ConsumePillAction(),
            CultivateAction(),
            WaitAction()
        ]

    @staticmethod
    def get_action_by_name(action_name: str) -> Optional['Action']:
        """根据名称获取动作"""
        actions = ActionFactory.get_all_actions()
        for action in actions:
            if action.name == action_name:
                return action
        return None