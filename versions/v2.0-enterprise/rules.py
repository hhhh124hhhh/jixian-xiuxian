"""
极简修仙游戏规则引擎
定义所有数值计算规则和游戏平衡参数
"""

from typing import Dict, Any, Optional, Sequence
from models import CharacterStats, RealmLevel


# 吐纳连击（push-your-luck）平衡参数：连击是"贪一点"的主动押注，层数越高
# 收益越猛，但走火概率也越高。所有表按下标索引，下标即当前层数。
BREATH_COMBO_MAX = 6                              # 连击层数上限
BREATH_COMBO_MULTIPLIERS = (1.0, 1.5, 2.2, 3.2, 4.5, 6.0, 7.0)  # 层数 -> 修炼经验倍率
FIRE_DEVIATION_RATES = (0.0, 0.0, 0.03, 0.08, 0.15, 0.25, 0.40)  # 层数 -> 走火概率
FIRE_DEVIATION_DURATION = 3                      # 走火后气息紊乱的持续回合数
FIRE_DEVIATION_EXP_RATIO = 0.7                   # 紊乱期间修炼收益倍率
FIRE_DEVIATION_COST_RATIO = 1.2                  # 紊乱期间修炼仙力消耗倍率

# 渡劫（经验条满后「修炼」按钮临时变成的突破窗口）平衡参数：
# 成功率只跟本境界吃了几颗丹药有关，多吃丹药是唯一加概率的手段。
TRIBULATION_BASE_RATE = 0.50                     # 0 颗丹药时的基础成功率
TRIBULATION_PILL_RATE_STEP = 0.17                # 本境界每颗丹药 +17%（1→67%、2→84%、3→100% 封顶）
TRIBULATION_MAX_RATE = 1.0                       # 成功率封顶
TRIBULATION_EXP_LOSS_RATIO = 0.5                 # 失败扣除当前境界已攒经验的 50%
TRIBULATION_SURVIVAL_FAIL_LIMIT = 2              # 本局前 2 次失败给「劫后余生」
TRIBULATION_SURVIVAL_EXP = 10                    # 「劫后余生」小额经验补偿

# 境界配额：每个大境界固定配额，打坐/等待不占配额，只有渡劫成功才回满
PILLS_QUOTA_PER_REALM = 6                        # 每境界可吃丹药次数
CULTIVATE_QUOTA_PER_REALM = 12                   # 每境界可修炼次数
QUOTA_EXHAUSTED_MESSAGE = "配额已用完，渡劫后刷新"  # 配额耗尽时的统一提示

# 心魔转资源：走火不再只是纯 debuff，「破心魔」把紊乱换成短期加速
DEMON_CLEAR_BONUS_USES = 3                       # 破心魔后接下来 3 次修炼享受加成
DEMON_CLEAR_MULTIPLIER = 1.4                     # 破心魔期间的修炼收益倍率


class BreathComboRules:
    """吐纳连击规则：层数倍率、走火概率与走火期修正

    修炼（吐纳）成功一次叠一层，经验按当前层倍率结算；
    每次修炼前按当前层概率 roll 走火，走火则连击清零并进入气息紊乱，
    紊乱期间收益打折、仙力消耗上浮，靠打坐（收功）回复。
    """

    def __init__(
        self,
        max_combo: int = BREATH_COMBO_MAX,
        multipliers: Sequence[float] = BREATH_COMBO_MULTIPLIERS,
        fire_rates: Sequence[float] = FIRE_DEVIATION_RATES,
        deviation_duration: int = FIRE_DEVIATION_DURATION,
        deviation_exp_ratio: float = FIRE_DEVIATION_EXP_RATIO,
        deviation_cost_ratio: float = FIRE_DEVIATION_COST_RATIO,
    ):
        self.max_combo = max_combo
        self.multipliers = tuple(multipliers)
        self.fire_rates = tuple(fire_rates)
        self.deviation_duration = deviation_duration
        self.deviation_exp_ratio = deviation_exp_ratio
        self.deviation_cost_ratio = deviation_cost_ratio

    def clamp_combo(self, combo: int) -> int:
        """把连击层数收敛到 0~max_combo（存档缺字段/脏数据都不会越界）"""
        try:
            value = int(combo)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(self.max_combo, value))

    def _by_combo(self, table: Sequence[float], combo: int) -> float:
        index = min(self.clamp_combo(combo), len(table) - 1)
        return table[index]

    def get_multiplier(self, combo: int) -> float:
        """当前连击层数对应的修炼经验倍率"""
        return self._by_combo(self.multipliers, combo)

    def get_fire_rate(self, combo: int) -> float:
        """当前连击层数对应的走火概率"""
        return self._by_combo(self.fire_rates, combo)

    def is_deviation_active(self, fire_deviation_turn: int) -> bool:
        """是否处于走火后的气息紊乱期"""
        return self.clamp_turns(fire_deviation_turn) > 0

    def clamp_turns(self, fire_deviation_turn: int) -> int:
        """把走火剩余回合数收敛到 0~deviation_duration"""
        try:
            value = int(fire_deviation_turn)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(self.deviation_duration, value))

    def tick_deviation(self, fire_deviation_turn: int) -> int:
        """打坐收功：紊乱回合递减（最小 0）"""
        return max(0, self.clamp_turns(fire_deviation_turn) - 1)

    def advance_combo(self, combo: int) -> int:
        """修炼成功：层数 +1（上限 max_combo）"""
        return self.clamp_combo(self.clamp_combo(combo) + 1)

    def trigger_deviation(self) -> int:
        """走火：连击清零、紊乱回合刷满"""
        return self.deviation_duration

    def roll_fire_deviation(self, combo: int, roll: Optional[float] = None) -> bool:
        """按当前层概率 roll 一次走火；roll 缺省取随机数（测试可注入）"""
        rate = self.get_fire_rate(combo)
        if rate <= 0:
            return False
        if roll is None:
            import random
            roll = random.random()
        return roll < rate

    def calculate_cultivate_exp(
        self,
        base_exp: int,
        combo: int,
        fire_deviation_turn: int = 0,
        demon_cleared: int = 0
    ) -> int:
        """修炼实际经验 = 基础经验 × 连击倍率 ×（紊乱期打折）×（破心魔加成）"""
        exp = float(base_exp) * self.get_multiplier(combo)
        if self.is_deviation_active(fire_deviation_turn):
            exp *= self.deviation_exp_ratio
        if demon_clearing_rules.is_active(demon_cleared):
            exp *= demon_clearing_rules.get_multiplier(demon_cleared)
        return max(0, int(round(exp)))

    def calculate_cultivate_mp_cost(
        self,
        base_cost: int,
        fire_deviation_turn: int = 0
    ) -> int:
        """修炼实际仙力消耗 = 基础消耗 ×（紊乱期上浮）"""
        cost = float(base_cost)
        if self.is_deviation_active(fire_deviation_turn):
            cost *= self.deviation_cost_ratio
        return max(0, int(round(cost)))

    def format_status(self, combo: int, fire_deviation_turn: int) -> str:
        """状态栏文案（走火期优先显示紊乱提示）"""
        combo = self.clamp_combo(combo)
        turns = self.clamp_turns(fire_deviation_turn)
        if turns > 0:
            return f"气息紊乱（剩{turns}回合）"
        if combo <= 0:
            return ""
        return (
            f"连击{combo} · 收益×{self.get_multiplier(combo):g}"
            f" · 走火{self.get_fire_rate(combo) * 100:g}%"
        )


class DemonClearingRules:
    """破心魔规则：把走火的气息紊乱换成短期修炼加速

    紊乱期「打坐」按钮变成「破心魔」：立刻清连击、清紊乱，并获得
    demon_cleared_bonus 次修炼的额外倍率（默认 ×1.4）。
    「静心」（吃丹药）只清紊乱不给加速，玩家由此在赌与稳之间做选择。
    """

    def __init__(
        self,
        bonus_uses: int = DEMON_CLEAR_BONUS_USES,
        multiplier: float = DEMON_CLEAR_MULTIPLIER,
    ):
        self.bonus_uses = bonus_uses
        self.multiplier = multiplier

    def clamp_bonus(self, demon_cleared_bonus: int) -> int:
        """把破心魔剩余次数收敛到 0~bonus_uses（存档缺字段/脏数据都不越界）"""
        try:
            value = int(demon_cleared_bonus)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(self.bonus_uses, value))

    def is_active(self, demon_cleared_bonus: int) -> bool:
        """是否处于破心魔加速期"""
        return self.clamp_bonus(demon_cleared_bonus) > 0

    def get_multiplier(self, demon_cleared_bonus: int) -> float:
        """破心魔加速期的修炼收益倍率"""
        return self.multiplier if self.is_active(demon_cleared_bonus) else 1.0

    def grant(self) -> int:
        """破心魔成功：刷新剩余次数（重复破心魔不叠加，只补满）"""
        return self.bonus_uses

    def consume(self, demon_cleared_bonus: int) -> int:
        """一次有效修炼后消耗一层加速（没有加速时原样返回）"""
        return max(0, self.clamp_bonus(demon_cleared_bonus) - 1)

    def format_status(self, demon_cleared_bonus: int) -> str:
        """状态栏文案（无加速时返回空串）"""
        bonus = self.clamp_bonus(demon_cleared_bonus)
        if bonus <= 0:
            return ""
        return f"破心魔×{self.multiplier:g}（剩{bonus}次）"


class RealmQuotaRules:
    """境界配额规则：每个大境界固定额度，只有渡劫成功才回满

    吃丹药与修炼各有一份配额，打坐/等待不占配额；配额用完对应动作直接
    不可执行，提示玩家去渡劫刷新。
    """

    def __init__(
        self,
        pills_limit: int = PILLS_QUOTA_PER_REALM,
        cultivate_limit: int = CULTIVATE_QUOTA_PER_REALM,
    ):
        self.pills_limit = pills_limit
        self.cultivate_limit = cultivate_limit

    def clamp_pills(self, pills_quota: int) -> int:
        """把丹药剩余配额收敛到 0~pills_limit"""
        try:
            value = int(pills_quota)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(self.pills_limit, value))

    def clamp_cultivate(self, cultivate_quota: int) -> int:
        """把修炼剩余配额收敛到 0~cultivate_limit"""
        try:
            value = int(cultivate_quota)
        except (TypeError, ValueError):
            value = 0
        return max(0, min(self.cultivate_limit, value))

    def has_pills_quota(self, character) -> bool:
        """本境界是否还有吃丹药配额"""
        return self.get_pills_quota(character) > 0

    def has_cultivate_quota(self, character) -> bool:
        """本境界是否还有修炼配额"""
        return self.get_cultivate_quota(character) > 0

    def get_pills_quota(self, character) -> int:
        """读角色身上的丹药剩余配额（缺字段按满额处理）"""
        return self.clamp_pills(
            getattr(character, "pills_quota", self.pills_limit)
        )

    def get_cultivate_quota(self, character) -> int:
        """读角色身上的修炼剩余配额（缺字段按满额处理）"""
        return self.clamp_cultivate(
            getattr(character, "cultivate_quota", self.cultivate_limit)
        )

    def spend_pills(self, character) -> int:
        """消耗 1 次丹药配额，返回剩余配额"""
        character.pills_quota = max(0, self.get_pills_quota(character) - 1)
        return character.pills_quota

    def spend_cultivate(self, character) -> int:
        """消耗 1 次修炼配额，返回剩余配额"""
        character.cultivate_quota = max(0, self.get_cultivate_quota(character) - 1)
        return character.cultivate_quota

    def refresh(self, character) -> None:
        """渡劫成功：两份配额回满，本境界丹药计数也清零"""
        character.pills_quota = self.pills_limit
        character.cultivate_quota = self.cultivate_limit
        character.pills_used_in_realm = 0

    def record_pill_used(self, character) -> int:
        """记录本境界吃丹药数（渡劫成功率用），返回本境界累计"""
        try:
            used = int(getattr(character, "pills_used_in_realm", 0)) + 1
        except (TypeError, ValueError):
            used = 1
        character.pills_used_in_realm = max(0, used)
        return character.pills_used_in_realm

    def exhausted_action(self, character) -> Optional[str]:
        """返回被配额卡住的动作名（没有则 None），用于统一提示"""
        if not self.has_pills_quota(character):
            return "consume_pill"
        if not self.has_cultivate_quota(character):
            return "cultivate"
        return None

    def format_status(self, pills_quota: int, cultivate_quota: int) -> str:
        """配额文案（UI 显示在丹药数字旁）"""
        pills = self.clamp_pills(pills_quota)
        cultivate = self.clamp_cultivate(cultivate_quota)
        return (
            f"丹药 {pills}/{self.pills_limit}"
            f" · 修炼 {cultivate}/{self.cultivate_limit}"
        )

    def is_exhausted(self, character) -> bool:
        """是否有任意一份配额已用完"""
        return self.exhausted_action(character) is not None


class TribulationRules:
    """渡劫规则：经验条满后把「修炼」变成一次有概率的突破

    成功率 = 50% + 本境界已吃丹药数 × 17%（100% 封顶）；
    成功则突破并回满配额、炼气期（当前境界）经验清零重计，
    失败则扣掉当前境界已攒经验的 50%，前两次失败额外触发「劫后余生」补偿。
    """

    def __init__(
        self,
        base_rate: float = TRIBULATION_BASE_RATE,
        pill_rate_step: float = TRIBULATION_PILL_RATE_STEP,
        max_rate: float = TRIBULATION_MAX_RATE,
        exp_loss_ratio: float = TRIBULATION_EXP_LOSS_RATIO,
        survival_fail_limit: int = TRIBULATION_SURVIVAL_FAIL_LIMIT,
        survival_exp: int = TRIBULATION_SURVIVAL_EXP,
    ):
        self.base_rate = base_rate
        self.pill_rate_step = pill_rate_step
        self.max_rate = max_rate
        self.exp_loss_ratio = exp_loss_ratio
        self.survival_fail_limit = survival_fail_limit
        self.survival_exp = survival_exp

    def get_success_rate(self, pills_used_in_realm: int) -> float:
        """本境界吃丹药数对应的渡劫成功率（0→50%、1→67%、2→84%、3→100% 封顶）"""
        try:
            pills = max(0, int(pills_used_in_realm))
        except (TypeError, ValueError):
            pills = 0
        rate = self.base_rate + self.pill_rate_step * pills
        return round(min(self.max_rate, rate), 2)

    def format_rate(self, pills_used_in_realm: int) -> str:
        """成功率文案（按钮上给玩家看概率再决策）"""
        return f"{self.get_success_rate(pills_used_in_realm) * 100:g}%"

    def format_label(self, pills_used_in_realm: int) -> str:
        """「渡劫」按钮文字：渡劫（成功率X%）"""
        return f"渡劫（成功率{self.format_rate(pills_used_in_realm)}）"

    def roll(self, pills_used_in_realm: int, roll: Optional[float] = None) -> bool:
        """按成功率 roll 一次渡劫；roll 缺省取随机数（测试可注入）"""
        rate = self.get_success_rate(pills_used_in_realm)
        if roll is None:
            import random
            roll = random.random()
        return roll < rate

    def is_available(self, character) -> bool:
        """经验条是否已满（渡劫窗口打开）"""
        return character.experience.is_exp_full()

    def calc_exp_penalty(self, current_level_experience: int) -> int:
        """渡劫失败扣掉的当前境界经验（50%）"""
        try:
            exp = max(0, int(current_level_experience))
        except (TypeError, ValueError):
            exp = 0
        return int(exp * self.exp_loss_ratio)

    def record_failure(self, character) -> int:
        """记录一次渡劫失败，返回累计失败次数"""
        try:
            fails = int(character.tribulation_fails) + 1
        except (TypeError, ValueError):
            fails = 1
        character.tribulation_fails = max(0, fails)
        return character.tribulation_fails

    def get_survival_exp(self, tribulation_fails: int) -> int:
        """「劫后余生」补偿经验：前 2 次失败有，第 3 次起为 0"""
        try:
            fails = int(tribulation_fails)
        except (TypeError, ValueError):
            fails = 0
        return self.survival_exp if fails <= self.survival_fail_limit else 0


class GameRule:
    """游戏规则引擎"""

    def __init__(self):
        # 基础数值配置
        self.base_values = {
            "max_hp": 100,
            "max_mp": 100,
            "starting_mp_ratio": 0.5,  # 初始仙力比例
        }

        # 打坐规则（打坐即收功：回仙力、给少量经验，吐纳连击清零）
        self.meditation_rules = {
            "hp_cost": 1,
            "base_mp_recovery": 30,
            "base_exp_gain": 3,
            "time_cost": 1,
            "consecutive_bonus_interval": 5,  # 连续奖励间隔
            "consecutive_pill_bonus": 1,
        }

        # 丹药规则
        self.pill_rules = {
            "base_hp_recovery": 15,
            "base_mp_recovery": 15,
            "base_exp_gain": 5,
            "consume_cost": 1,
        }

        # 修炼规则（经验受吐纳连击倍率影响，见 BreathComboRules）
        self.cultivation_rules = {
            "mp_cost": 20,
            "base_exp_gain": 10,
            "time_cost": 2,
        }

        # 等待规则
        self.wait_rules = {
            "hp_cost": 1,
            "hp_recovery": 2,
            "mp_recovery": 3,
            "time_cost": 1,
        }

        # 资质影响规则
        self.talent_multipliers = {
            "meditate": 0.8,
            "cultivate": 1.5,
            "pill": 1.0,
            "wait": 0.2,
        }

        # 境界系统规则
        self.realm_thresholds = {
            RealmLevel.QI_REFINING: 100,
            RealmLevel.FOUNDATION: 200,
            RealmLevel.CORE_FORMATION: 400,
            RealmLevel.NASCENT_SOUL: 800,
            RealmLevel.SPIRITUAL_TRANSFORMATION: 1600,
            RealmLevel.ASCENSION: float('inf'),
        }

    def calculate_talent_bonus(self, base_value: float, talent: int, action_type: str) -> int:
        """计算资质加成"""
        multiplier = self.talent_multipliers.get(action_type, 1.0)
        bonus = talent * multiplier
        return int(base_value + bonus)

    def calculate_meditation_effects(self, character: CharacterStats) -> Dict[str, int]:
        """计算打坐效果"""
        talent = character.talent.base_talent

        mp_recovery = self.calculate_talent_bonus(
            self.meditation_rules["base_mp_recovery"],
            talent,
            "meditate"
        )

        exp_gain = self.calculate_talent_bonus(
            self.meditation_rules["base_exp_gain"],
            talent,
            "meditate"
        )

        return {
            "hp_cost": self.meditation_rules["hp_cost"],
            "mp_recovery": mp_recovery,
            "exp_gain": exp_gain,
            "time_cost": self.meditation_rules["time_cost"],
        }

    def calculate_pill_effects(self, character: CharacterStats) -> Dict[str, int]:
        """计算丹药效果"""
        talent = character.talent.base_talent

        hp_recovery = self.calculate_talent_bonus(
            self.pill_rules["base_hp_recovery"],
            talent,
            "pill"
        )

        mp_recovery = self.calculate_talent_bonus(
            self.pill_rules["base_mp_recovery"],
            talent,
            "pill"
        )

        exp_gain = self.calculate_talent_bonus(
            self.pill_rules["base_exp_gain"],
            talent,
            "pill"
        )

        return {
            "hp_recovery": hp_recovery,
            "mp_recovery": mp_recovery,
            "exp_gain": exp_gain,
            "consume_cost": self.pill_rules["consume_cost"],
        }

    def calculate_cultivation_effects(self, character: CharacterStats) -> Dict[str, int]:
        """计算修炼效果"""
        talent = character.talent.base_talent

        exp_gain = self.calculate_talent_bonus(
            self.cultivation_rules["base_exp_gain"],
            talent,
            "cultivate"
        )

        return {
            "mp_cost": self.cultivation_rules["mp_cost"],
            "exp_gain": exp_gain,
            "time_cost": self.cultivation_rules["time_cost"],
        }

    def calculate_wait_effects(self, character: CharacterStats) -> Dict[str, int]:
        """计算等待效果"""
        talent = character.talent.base_talent

        hp_recovery = self.calculate_talent_bonus(
            self.wait_rules["hp_recovery"],
            talent,
            "wait"
        )

        mp_recovery = self.calculate_talent_bonus(
            self.wait_rules["mp_recovery"],
            talent,
            "wait"
        )

        return {
            "hp_cost": self.wait_rules["hp_cost"],
            "hp_recovery": hp_recovery,
            "mp_recovery": mp_recovery,
            "time_cost": self.wait_rules["time_cost"],
        }

    def get_realm_threshold(self, realm: RealmLevel) -> int:
        """获取境界所需经验"""
        return self.realm_thresholds.get(realm, float('inf'))

    def get_next_realm(self, current_realm: RealmLevel) -> RealmLevel:
        """获取下一境界"""
        realms = list(RealmLevel)
        current_index = realms.index(current_realm)
        if current_index < len(realms) - 1:
            return realms[current_index + 1]
        return current_realm

    def can_breakthrough(self, character: CharacterStats) -> bool:
        """检查是否可以突破"""
        current_threshold = self.get_realm_threshold(character.experience.current_realm)
        return character.experience.current_level_experience >= current_threshold

    def get_character_power_level(self, character: CharacterStats) -> int:
        """计算角色综合实力评分"""
        if not character.is_alive():
            return 0

        # 基础分数
        base_score = (
            character.health.current_hp * 0.3 +
            character.mana.current_mp * 0.3 +
            character.experience.total_experience * 0.2 +
            character.talent.base_talent * 10 +
            character.inventory.get_item_count("pill") * 5
        )

        # 境界加成
        realm_multipliers = {
            RealmLevel.QI_REFINING: 1.0,
            RealmLevel.FOUNDATION: 1.5,
            RealmLevel.CORE_FORMATION: 2.5,
            RealmLevel.NASCENT_SOUL: 4.0,
            RealmLevel.SPIRITUAL_TRANSFORMATION: 6.0,
            RealmLevel.ASCENSION: 10.0,
        }

        realm_multiplier = realm_multipliers.get(character.experience.current_realm, 1.0)

        return int(base_score * realm_multiplier)

    def get_action_recommendation(self, character: CharacterStats) -> str:
        """根据角色状态推荐行动"""
        if not character.is_alive():
            return "修炼失败，请重新开始"

        # 配额卡住时先提示刷新条件（只有渡劫成功才回满）
        exhausted = realm_quota_rules.exhausted_action(character)
        if exhausted is not None:
            if tribulation_rules.is_available(character):
                return f"经验已满，点击渡劫（成功率{tribulation_rules.format_rate(character.pills_used_in_realm)}）突破"
            return QUOTA_EXHAUSTED_MESSAGE

        hp_percent = character.health.get_hp_percentage()
        mp_percent = character.mana.get_mp_percentage()
        pill_count = character.inventory.get_item_count("pill")

        # 危急状态推荐
        if hp_percent < 0.3:
            if pill_count > 0:
                return "生命垂危，建议立即服用丹药"
            else:
                return "生命垂危且无丹药，建议等待恢复"

        # 仙力不足推荐
        if mp_percent < 0.3:
            if pill_count > 0:
                return "仙力不足，建议服用丹药恢复"
            else:
                return "仙力不足，建议打坐恢复"

        # 正常状态推荐
        if mp_percent > 0.8 and pill_count > 2:
            return "状态良好，建议全力修炼"
        elif pill_count == 0:
            return "缺少丹药，建议多打坐积累"
        else:
            return "状态适中，可以根据需要选择修炼或恢复"


class DifficultySettings:
    """难度设置管理"""

    def __init__(self):
        self.difficulties = {
            "easy": {
                "talent_range": (5, 10),
                "starting_pills": 3,
                "exp_multiplier": 1.2,
                "recovery_multiplier": 1.3,
            },
            "normal": {
                "talent_range": (1, 10),
                "starting_pills": 1,
                "exp_multiplier": 1.0,
                "recovery_multiplier": 1.0,
            },
            "hard": {
                "talent_range": (1, 6),
                "starting_pills": 0,
                "exp_multiplier": 0.8,
                "recovery_multiplier": 0.7,
            }
        }

    def get_difficulty_settings(self, difficulty: str) -> Dict[str, Any]:
        """获取难度设置"""
        return self.difficulties.get(difficulty, self.difficulties["normal"])

    def apply_difficulty_to_character(self, character: CharacterStats, difficulty: str):
        """应用难度设置到角色"""
        settings = self.get_difficulty_settings(difficulty)

        # 设置初始丹药
        character.inventory.add_item("pill", settings["starting_pills"])

        # 注意：资质在角色创建时已设定，这里不修改
        # 难度主要影响后续的收益计算


# 全局规则实例
game_rules = GameRule()
difficulty_settings = DifficultySettings()
breath_combo_rules = BreathComboRules()
demon_clearing_rules = DemonClearingRules()
realm_quota_rules = RealmQuotaRules()
tribulation_rules = TribulationRules()