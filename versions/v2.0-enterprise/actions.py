"""
极简修仙游戏动作系统
定义所有基础动作的接口和实现
"""

from abc import ABC, abstractmethod
from typing import Optional
from models import CharacterStats, ActionResult, Cost, GameLog
from rules import (
    QUOTA_EXHAUSTED_MESSAGE,
    breath_combo_rules,
    demon_clearing_rules,
    game_rules,
    realm_quota_rules,
    tribulation_rules,
)


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
        return f"无法执行{self.description}"


class MeditateAction(Action):
    """打坐动作

    正常时是收功（回仙力、吐纳连击清零、气息紊乱回合递减）；
    走火紊乱期间按钮变成「破心魔」：立刻清连击清紊乱，换来
    接下来 3 次修炼 ×1.4 的加速（心魔从纯惩罚变成可押注的资源）。
    """

    def __init__(self):
        super().__init__("meditate", "进入冥想状态，恢复仙力并获得少量经验")

    def get_cost(self) -> Cost:
        return Cost(hp=1, time=1)  # 微量消耗生命值

    def is_demon_clearing(self, character: CharacterStats) -> bool:
        """紊乱期是否走「破心魔」分支"""
        return breath_combo_rules.is_deviation_active(character.fire_deviation_turn)

    def get_label(self, character: CharacterStats) -> str:
        """按钮文字（破心魔 / 打坐）"""
        return "破心魔" if self.is_demon_clearing(character) else "打坐"

    def can_execute(self, character: CharacterStats) -> bool:
        return character.is_alive()

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 破心魔要在紊乱回合递减之前判定（打坐本身只减 1 回合）
        demon_cleared = self.is_demon_clearing(character)

        # 计算效果
        mp_recovery = game_rules.meditation_rules["base_mp_recovery"]
        exp_gain = int(character.talent.get_talent_bonus(
            game_rules.meditation_rules["base_exp_gain"], "meditate"
        ))
        # 经验条满时不再白给经验：等待玩家渡劫，避免绕过突破窗口
        # （满条时连 add_experience(0) 都会直接突破，所以整段跳过）
        exp_full = tribulation_rules.is_available(character)
        if exp_full:
            exp_gain = 0

        # 应用效果
        actual_mp_recovery = character.mana.restore(mp_recovery)
        if exp_full:
            breakthrough, breakthrough_msg = False, None
        else:
            breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 收功：吐纳连击清零，气息紊乱回合递减
        character.breath_combo = 0
        character.fire_deviation_turn = breath_combo_rules.tick_deviation(
            character.fire_deviation_turn
        )

        # 破心魔：紊乱当场清空，换 3 次修炼加速
        if demon_cleared:
            character.fire_deviation_turn = 0
            character.demon_cleared_bonus = demon_clearing_rules.grant()

        # 更新连续打坐计数
        character.meditation_streak += 1

        # 检查连续奖励
        pill_bonus = 0
        if character.meditation_streak % 5 == 0:
            character.inventory.add_item("pill", 1)
            pill_bonus = 1

        # 构建消息
        messages = [f"你进入打坐修炼状态，恢复{actual_mp_recovery}点仙力，获得{exp_gain}点经验"]
        if exp_full:
            messages.append("经验已满，修为暂存，等你渡劫")
        if demon_cleared:
            messages.append(
                f"破心魔！气息紊乱尽消，接下来{demon_clearing_rules.bonus_uses}次修炼"
                f"收益×{demon_clearing_rules.multiplier:g}"
            )
        elif character.fire_deviation_turn > 0:
            messages.append(f"气息紊乱尚余{character.fire_deviation_turn}回合")
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
            "pill_bonus": pill_bonus,
            "demon_cleared": demon_cleared,
            "demon_cleared_bonus": character.demon_cleared_bonus
        }
        costs = {"hp": cost.hp, "time": cost.time}

        # 添加等级提升信息
        if breakthrough:
            effects["level_up"] = True
            effects["new_level"] = character.experience.current_realm.value

        return ActionResult(True, log_message, effects, costs)


class ConsumePillAction(Action):
    """服用丹药动作

    走火紊乱期间按钮变成「静心」：花一颗丹立刻买平安（清紊乱清连击），
    但没有破心魔的加速；每次服用都会扣 1 点本境界丹药配额并抬高渡劫成功率。
    """

    def __init__(self):
        super().__init__("consume_pill", "服用丹药快速恢复生命力和仙力")

    def get_cost(self) -> Cost:
        return Cost(pills=1)

    def is_calming(self, character: CharacterStats) -> bool:
        """紊乱期是否走「静心」分支"""
        return breath_combo_rules.is_deviation_active(character.fire_deviation_turn)

    def get_label(self, character: CharacterStats) -> str:
        """按钮文字（静心 / 吃丹药）"""
        return "静心" if self.is_calming(character) else "吃丹药"

    def can_execute(self, character: CharacterStats) -> bool:
        return (character.is_alive() and
                character.inventory.get_item_count("pill") >= 1 and
                realm_quota_rules.has_pills_quota(character))

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 静心要在消耗丹药之前判定
        calming = self.is_calming(character)

        # 应用消耗
        cost = self.get_cost()
        character.apply_cost(cost)

        # 计算效果（资质影响恢复效果）
        hp_recovery = int(character.talent.get_talent_bonus(15, "pill"))
        mp_recovery = int(character.talent.get_talent_bonus(15, "pill"))
        exp_gain = int(character.talent.get_talent_bonus(5, "pill"))
        # 经验条满时不再白给经验：等待玩家渡劫，避免绕过突破窗口
        exp_full = tribulation_rules.is_available(character)
        if exp_full:
            exp_gain = 0

        # 应用效果
        actual_hp_recovery = character.health.restore(hp_recovery)
        actual_mp_recovery = character.mana.restore(mp_recovery)
        if exp_full:
            breakthrough, breakthrough_msg = False, None
        else:
            breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 静心：只清紊乱清连击，不给加速
        if calming:
            character.breath_combo = 0
            character.fire_deviation_turn = 0

        # 境界配额：本境界吃丹药数 +1（渡劫成功率），丹药配额 -1
        pills_used = realm_quota_rules.record_pill_used(character)
        pills_left = realm_quota_rules.spend_pills(character)

        # 重置连续打坐计数（吃丹药打断连续状态）
        character.meditation_streak = 0

        # 构建消息
        action_label = "静心" if calming else "服用丹药"
        messages = [f"你{action_label}，服下一颗丹药，恢复{actual_hp_recovery}点生命和{actual_mp_recovery}点仙力"]
        if exp_gain > 0:
            messages.append(f"获得{exp_gain}点经验")
        if exp_full:
            messages.append("经验已满，修为暂存，等你渡劫")
        if calming:
            messages.append("气息紊乱已平，连击散去（无加速）")
        if breakthrough:
            messages.append(breakthrough_msg)
        messages.append(f"丹药 {pills_left}/{realm_quota_rules.pills_limit}")

        # 记录日志
        log_message = "，".join(messages) + "。"
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {
            "hp_recovery": actual_hp_recovery,
            "mp_recovery": actual_mp_recovery,
            "exp_gain": exp_gain,
            "pills_quota_left": pills_left,
            "pills_used_in_realm": pills_used,
            "calming": calming
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
        elif not realm_quota_rules.has_pills_quota(character):
            return QUOTA_EXHAUSTED_MESSAGE
        return "无法服用丹药"


class CultivateAction(Action):
    """修炼功法动作

    吐纳连击：成功叠层，修炼前按当前层概率 roll 走火；
    破心魔期间收益 ×1.4（消耗 1 层加速）；
    经验条满时本按钮临时变成「渡劫（成功率X%）」，走一次有概率的突破；
    非渡劫的每次修炼扣 1 点本境界修炼配额（渡劫不算修炼，不占配额）。
    """

    def __init__(self):
        super().__init__("cultivate", "运转心法，大量提升修为")

    def get_cost(self) -> Cost:
        cultivation_rules = game_rules.cultivation_rules
        return Cost(
            mp=cultivation_rules["mp_cost"],
            time=cultivation_rules["time_cost"]
        )  # 消耗仙力和时间

    def get_tribulation_cost(self) -> Cost:
        """渡劫消耗：只花时间，不要仙力（经验满时不该被仙力不足挡住）"""
        return Cost(time=game_rules.cultivation_rules["time_cost"])

    def get_cost_for(self, character: CharacterStats) -> Cost:
        """当前状态下的实际消耗（走火紊乱期仙力消耗上浮）"""
        base_cost = self.get_cost()
        return Cost(
            hp=base_cost.hp,
            mp=breath_combo_rules.calculate_cultivate_mp_cost(
                base_cost.mp, character.fire_deviation_turn
            ),
            pills=base_cost.pills,
            time=base_cost.time
        )

    def is_tribulation_ready(self, character: CharacterStats) -> bool:
        """经验条是否已满（此时按钮变为渡劫）"""
        return tribulation_rules.is_available(character)

    def get_label(self, character: CharacterStats) -> str:
        """按钮文字：渡劫（成功率X%）/ 修炼"""
        if self.is_tribulation_ready(character):
            return tribulation_rules.format_label(character.pills_used_in_realm)
        return "修炼"

    def can_execute(self, character: CharacterStats) -> bool:
        if not character.is_alive():
            return False
        # 渡劫窗口：不占修炼配额，也不看仙力
        if self.is_tribulation_ready(character):
            return True
        return (character.mana.current_mp >= self.get_cost_for(character).mp and
                realm_quota_rules.has_cultivate_quota(character))

    def execute(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        if not self.can_execute(character):
            return ActionResult(False, self.get_failure_message(character), {}, {})

        # 经验条满：修炼按钮临时变成渡劫
        if self.is_tribulation_ready(character):
            return self._execute_tribulation(character, game_log)

        # 消耗按本次行动开始前的紊乱状态计算
        cost = self.get_cost_for(character)
        character.apply_cost(cost)

        # 修炼前先 roll 走火：走火则本次无经验、连击清零并进入气息紊乱
        combo_before = character.breath_combo
        deviated = breath_combo_rules.roll_fire_deviation(combo_before)
        demon_bonus_active = demon_clearing_rules.is_active(character.demon_cleared_bonus)

        if deviated:
            character.breath_combo = 0
            character.fire_deviation_turn = breath_combo_rules.trigger_deviation()
            exp_gain = 0
            multiplier = breath_combo_rules.get_multiplier(combo_before)
        else:
            # 收益按本次修炼开始时的层数倍率结算，随后叠一层
            exp_gain = breath_combo_rules.calculate_cultivate_exp(
                game_rules.cultivation_rules["base_exp_gain"],
                combo_before,
                character.fire_deviation_turn,
                character.demon_cleared_bonus
            )
            multiplier = breath_combo_rules.get_multiplier(combo_before)
            character.breath_combo = breath_combo_rules.advance_combo(combo_before)
            # 有效收益才消耗一层破心魔加速
            if exp_gain > 0:
                character.demon_cleared_bonus = demon_clearing_rules.consume(
                    character.demon_cleared_bonus
                )

        # 应用效果
        breakthrough, breakthrough_msg = character.experience.add_experience(exp_gain)

        # 境界配额：非渡劫的修炼扣 1 点修炼配额
        cultivate_left = realm_quota_rules.spend_cultivate(character)

        # 重置连续打坐计数
        character.meditation_streak = 0

        # 构建消息
        if deviated:
            messages = [
                f"气息走火！你连吐纳的{multiplier:g}倍收益尽数散去，"
                f"进入气息紊乱（{character.fire_deviation_turn}回合）"
            ]
        else:
            messages = [
                f"你运转心法，修为精进，获得{exp_gain}点经验"
                f"（连击{combo_before}→{character.breath_combo}，收益×{multiplier:g}）"
            ]
            if breath_combo_rules.is_deviation_active(character.fire_deviation_turn):
                messages.append(
                    f"气息紊乱中，本次仙力消耗×{breath_combo_rules.deviation_cost_ratio:g}、"
                    f"收益×{breath_combo_rules.deviation_exp_ratio:g}"
                )
            if demon_bonus_active and exp_gain > 0:
                messages.append(
                    f"破心魔加持，收益×{demon_clearing_rules.multiplier:g}"
                    f"（剩{character.demon_cleared_bonus}次）"
                )
        messages.append(
            f"修炼 {cultivate_left}/{realm_quota_rules.cultivate_limit}"
        )
        if breakthrough:
            messages.append(breakthrough_msg)

        # 记录日志
        log_message = "，".join(messages) + "。"
        game_log.add_entry(log_message)

        # 构建返回结果
        effects = {
            "exp_gain": exp_gain,
            "breath_combo": character.breath_combo,
            "fire_deviation_turn": character.fire_deviation_turn,
            "fire_deviation": deviated,
            "demon_cleared_bonus": character.demon_cleared_bonus,
            "cultivate_quota_left": cultivate_left
        }
        costs = {"mp": cost.mp, "time": cost.time}

        # 添加等级提升信息
        if breakthrough:
            effects["level_up"] = True
            effects["new_level"] = character.experience.current_realm.value

        return ActionResult(True, log_message, effects, costs)

    def _execute_tribulation(self, character: CharacterStats, game_log: GameLog) -> ActionResult:
        """经验条满时的渡劫：突破 vs 折半"""
        pills_used = character.pills_used_in_realm
        rate = tribulation_rules.get_success_rate(pills_used)

        # 渡劫只花时间，不吃修炼配额
        cost = self.get_tribulation_cost()
        character.apply_cost(cost)

        character.meditation_streak = 0
        succeeded = tribulation_rules.roll(pills_used, roll=None)

        effects = {
            "tribulation": True,
            "tribulation_success": succeeded,
            "tribulation_rate": rate,
            "pills_used_in_realm": pills_used
        }
        messages = [f"天劫降临！以本境界{pills_used}颗丹药为凭，成功率{rate * 100:g}%"]

        if succeeded:
            previous_realm = character.experience.current_realm.value
            next_realm = game_rules.get_next_realm(character.experience.current_realm)
            character.experience.current_realm = next_realm
            character.experience.reset_realm_experience()
            # 只有渡劫成功才刷新配额
            realm_quota_rules.refresh(character)

            messages.append(f"雷劫加身，你自{previous_realm}突破至{next_realm.value}！")
            messages.append(f"境界配额已刷新（丹药 {character.pills_quota}/{realm_quota_rules.pills_limit}"
                            f" · 修炼 {character.cultivate_quota}/{realm_quota_rules.cultivate_limit}）")
            effects["level_up"] = True
            effects["new_level"] = next_realm.value
            effects["pills_quota_left"] = character.pills_quota
            effects["cultivate_quota_left"] = character.cultivate_quota
        else:
            penalty = tribulation_rules.calc_exp_penalty(
                character.experience.current_level_experience
            )
            lost = character.experience.spend_realm_experience(penalty)
            fails = tribulation_rules.record_failure(character)

            messages.append(f"雷劫加身，道基受损，损失{lost}点当前境界经验（-{tribulation_rules.exp_loss_ratio:.0%}）")

            # 本局前 2 次失败给「劫后余生」补偿，第 3 次起纯扣经验
            compensation = tribulation_rules.get_survival_exp(fails)
            if compensation > 0:
                character.experience.add_bonus_experience(compensation)
                messages.append(f"成就「劫后余生」（第{fails}次劫）：心有所悟，补回{compensation}点经验")

            effects["exp_lost"] = lost
            effects["tribulation_fails"] = fails
            effects["survival_achievement"] = compensation > 0
            effects["comp_exp"] = compensation
            effects["pills_quota_left"] = realm_quota_rules.get_pills_quota(character)
            effects["cultivate_quota_left"] = realm_quota_rules.get_cultivate_quota(character)

        log_message = "，".join(messages) + "。"
        game_log.add_entry(log_message)

        return ActionResult(True, log_message, effects, {"time": cost.time})

    def get_failure_message(self, character: CharacterStats) -> str:
        if not character.is_alive():
            return "你已经无法行动"
        elif character.mana.current_mp < self.get_cost_for(character).mp:
            return "仙力不足，无法修炼"
        elif not realm_quota_rules.has_cultivate_quota(character):
            return QUOTA_EXHAUSTED_MESSAGE
        return "无法修炼"


class WaitAction(Action):
    """等待动作"""

    def __init__(self):
        super().__init__("wait", "静心养神，缓慢恢复状态")

    def get_cost(self) -> Cost:
        return Cost(hp=1, time=1)  # 等待也会消耗微量生命

    def get_label(self, character: CharacterStats) -> str:
        """按钮文字（打坐/等待体系里等待固定叫「等待」）"""
        return "等待"

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