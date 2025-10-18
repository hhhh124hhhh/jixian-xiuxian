"""
规则引擎单元测试
"""

import pytest
from rules import GameRule, DifficultySettings, game_rules, difficulty_settings
from models import CharacterStats, RealmLevel


@pytest.mark.unit
class TestGameRule:
    """游戏规则测试"""

    def test_initialization(self):
        """测试初始化"""
        rule = GameRule()
        assert rule.base_values["max_hp"] == 100
        assert rule.base_values["max_mp"] == 100
        assert rule.meditation_rules["hp_cost"] == 1
        assert rule.pill_rules["consume_cost"] == 1

    def test_calculate_talent_bonus(self):
        """测试资质加成计算"""
        rule = GameRule()

        # 测试打坐加成
        bonus = rule.calculate_talent_bonus(10, 5, "meditate")
        assert bonus == 10 + 5 * 0.8  # 10 + 4 = 14

        # 测试修炼加成
        bonus = rule.calculate_talent_bonus(10, 5, "cultivate")
        assert bonus == 10 + 5 * 1.5  # 10 + 7.5 = 17.5

        # 测试丹药加成
        bonus = rule.calculate_talent_bonus(10, 5, "pill")
        assert bonus == 10 + 5 * 1.0  # 10 + 5 = 15

        # 测试等待加成
        bonus = rule.calculate_talent_bonus(10, 5, "wait")
        assert bonus == 10 + 5 * 0.2  # 10 + 1 = 11

    def test_calculate_meditation_effects(self, character):
        """测试计算打坐效果"""
        rule = GameRule()
        effects = rule.calculate_meditation_effects(character)

        assert effects["hp_cost"] == 1
        assert effects["mp_recovery"] > 0
        assert effects["exp_gain"] > 0
        assert effects["time_cost"] == 1

        # 高资质角色应该有更好效果
        high_talent_character = CharacterStats("高资质")
        high_talent_character.talent.base_talent = 10
        high_effects = rule.calculate_meditation_effects(high_talent_character)

        assert high_effects["mp_recovery"] > effects["mp_recovery"]
        assert high_effects["exp_gain"] > effects["exp_gain"]

    def test_calculate_pill_effects(self, character):
        """测试计算丹药效果"""
        rule = GameRule()
        effects = rule.calculate_pill_effects(character)

        assert effects["hp_recovery"] > 0
        assert effects["mp_recovery"] > 0
        assert effects["exp_gain"] > 0
        assert effects["consume_cost"] == 1

    def test_calculate_cultivation_effects(self, character):
        """测试计算修炼效果"""
        rule = GameRule()
        effects = rule.calculate_cultivation_effects(character)

        assert effects["mp_cost"] == 20
        assert effects["exp_gain"] > 0
        assert effects["time_cost"] == 2

        # 高资质角色应该有更好效果
        high_talent_character = CharacterStats("高资质")
        high_talent_character.talent.base_talent = 10
        high_effects = rule.calculate_cultivation_effects(high_talent_character)

        assert high_effects["exp_gain"] > effects["exp_gain"]

    def test_calculate_wait_effects(self, character):
        """测试计算等待效果"""
        rule = GameRule()
        effects = rule.calculate_wait_effects(character)

        assert effects["hp_cost"] == 1
        assert effects["hp_recovery"] > 0
        assert effects["mp_recovery"] > 0
        assert effects["time_cost"] == 1

    def test_get_realm_threshold(self):
        """测试获取境界阈值"""
        rule = GameRule()

        assert rule.get_realm_threshold(RealmLevel.QI_REFINING) == 100
        assert rule.get_realm_threshold(RealmLevel.FOUNDATION) == 200
        assert rule.get_realm_threshold(RealmLevel.CORE_FORMATION) == 400
        assert rule.get_realm_threshold(RealmLevel.NASCENT_SOUL) == 800
        assert rule.get_realm_threshold(RealmLevel.SPIRITUAL_TRANSFORMATION) == 1600
        assert rule.get_realm_threshold(RealmLevel.ASCENSION) == float('inf')

    def test_get_next_realm(self):
        """测试获取下一境界"""
        rule = GameRule()

        assert rule.get_next_realm(RealmLevel.QI_REFINING) == RealmLevel.FOUNDATION
        assert rule.get_next_realm(RealmLevel.FOUNDATION) == RealmLevel.CORE_FORMATION
        assert rule.get_next_realm(RealmLevel.CORE_FORMATION) == RealmLevel.NASCENT_SOUL
        assert rule.get_next_realm(RealmLevel.NASCENT_SOUL) == RealmLevel.SPIRITUAL_TRANSFORMATION
        assert rule.get_next_realm(RealmLevel.SPIRITUAL_TRANSFORMATION) == RealmLevel.ASCENSION
        assert rule.get_next_realm(RealmLevel.ASCENSION) == RealmLevel.ASCENSION  # 已经是最高境界

    def test_can_breakthrough(self, character):
        """测试检查是否可以突破"""
        rule = GameRule()

        # 初始状态不能突破
        assert rule.can_breakthrough(character) is False

        # 添加足够经验后可以突破
        character.experience.add_experience(100)
        assert rule.can_breakthrough(character) is True

        # 突破后需要更多经验
        character.experience.add_experience(50)
        assert rule.can_breakthrough(character) is False  # 炼气期突破后重置，当前50经验

    def test_get_character_power_level(self, character):
        """测试计算角色实力评分"""
        rule = GameRule()

        power = rule.get_character_power_level(character)
        assert power > 0

        # 高境界角色实力更强
        character.experience.add_experience(300)  # 突破到结丹期
        higher_power = rule.get_character_power_level(character)
        assert higher_power > power

        # 死亡角色实力为0
        character.health.current_hp = 0
        dead_power = rule.get_character_power_level(character)
        assert dead_power == 0

    def test_get_action_recommendation(self, character):
        """测试获取动作推荐"""
        rule = GameRule()

        recommendation = rule.get_action_recommendation(character)
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0

        # 生命值低时的推荐
        character.health.current_hp = 20
        character.inventory.add_item("pill", 2)
        low_hp_recommendation = rule.get_action_recommendation(character)
        assert "丹药" in low_hp_recommendation or "危急" in low_hp_recommendation

        # 仙力值低时的推荐
        character.health.current_hp = 80
        character.mana.current_mp = 10
        low_mp_recommendation = rule.get_action_recommendation(character)
        assert "仙力不足" in low_mp_recommendation or "丹药" in low_mp_recommendation or "打坐" in low_mp_recommendation

        # 死亡角色的推荐
        character.health.current_hp = 0
        dead_recommendation = rule.get_action_recommendation(character)
        assert "失败" in dead_recommendation


@pytest.mark.unit
class TestDifficultySettings:
    """难度设置测试"""

    def test_initialization(self):
        """测试初始化"""
        settings = DifficultySettings()
        assert "easy" in settings.difficulties
        assert "normal" in settings.difficulties
        assert "hard" in settings.difficulties

    def test_get_difficulty_settings(self):
        """测试获取难度设置"""
        settings = DifficultySettings()

        easy_settings = settings.get_difficulty_settings("easy")
        assert easy_settings["talent_range"] == (5, 10)
        assert easy_settings["starting_pills"] == 3
        assert easy_settings["exp_multiplier"] == 1.2

        normal_settings = settings.get_difficulty_settings("normal")
        assert normal_settings["talent_range"] == (1, 10)
        assert normal_settings["starting_pills"] == 1
        assert normal_settings["exp_multiplier"] == 1.0

        hard_settings = settings.get_difficulty_settings("hard")
        assert hard_settings["talent_range"] == (1, 6)
        assert hard_settings["starting_pills"] == 0
        assert hard_settings["exp_multiplier"] == 0.8

    def test_get_difficulty_settings_invalid(self):
        """测试获取不存在的难度设置"""
        settings = DifficultySettings()

        invalid_settings = settings.get_difficulty_settings("invalid")
        # 应该返回默认设置
        assert invalid_settings["talent_range"] == (1, 10)
        assert invalid_settings["starting_pills"] == 1

    def test_apply_difficulty_to_character(self):
        """测试应用难度设置到角色"""
        settings = DifficultySettings()
        character = CharacterStats("测试角色")

        # 应用简单难度
        settings.apply_difficulty_to_character(character, "easy")
        assert character.inventory.get_item_count("pill") == 3

        # 应用困难难度
        character.inventory.items["pill"] = 0  # 重置
        settings.apply_difficulty_to_character(character, "hard")
        assert character.inventory.get_item_count("pill") == 0

        # 应用普通难度
        character.inventory.items["pill"] = 0  # 重置
        settings.apply_difficulty_to_character(character, "normal")
        assert character.inventory.get_item_count("pill") == 1


@pytest.mark.unit
class TestGlobalInstances:
    """全局实例测试"""

    def test_game_rules_global_instance(self):
        """测试全局规则实例"""
        assert game_rules is not None
        assert isinstance(game_rules, GameRule)

        # 测试基本功能
        assert game_rules.get_realm_threshold(RealmLevel.QI_REFINING) == 100

    def test_difficulty_settings_global_instance(self):
        """测试全局难度设置实例"""
        assert difficulty_settings is not None
        assert isinstance(difficulty_settings, DifficultySettings)

        # 测试基本功能
        normal_settings = difficulty_settings.get_difficulty_settings("normal")
        assert normal_settings["starting_pills"] == 1


@pytest.mark.unit
class TestRuleEdgeCases:
    """规则引擎边界情况测试"""

    def test_zero_talent_character(self):
        """测试资质为0的角色（不应该出现，但需要健壮性）"""
        rule = GameRule()
        character = CharacterStats("测试")
        character.talent.base_talent = 0

        # 应该能正常计算
        bonus = rule.calculate_talent_bonus(10, 0, "meditate")
        assert bonus == 10  # 没有加成

        effects = rule.calculate_meditation_effects(character)
        assert effects["mp_recovery"] == 8  # 基础值
        assert effects["exp_gain"] == 3    # 基础值

    def test_extreme_talent_character(self):
        """测试极端资质角色"""
        rule = GameRule()
        character = CharacterStats("测试")
        character.talent.base_talent = 20  # 超出正常范围

        # 应该能正常计算
        bonus = rule.calculate_talent_bonus(10, 20, "cultivate")
        assert bonus == 10 + 20 * 1.5  # 40

    def test_max_stats_character(self):
        """测试满状态角色"""
        character = CharacterStats("测试")
        character.health.current_hp = 100
        character.mana.current_mp = 100
        character.inventory.add_item("pill", 99)

        rule = GameRule()
        power = rule.get_character_power_level(character)
        assert power > 0

        recommendation = rule.get_action_recommendation(character)
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0

    def test_empty_character_stats(self):
        """测试空角色状态"""
        rule = GameRule()

        # 测试空角色的推荐
        character = CharacterStats("测试")
        character.health.current_hp = 1
        character.mana.current_mp = 0
        character.inventory.add_item("pill", 0)

        recommendation = rule.get_action_recommendation(character)
        assert "危急" in recommendation or "不足" in recommendation