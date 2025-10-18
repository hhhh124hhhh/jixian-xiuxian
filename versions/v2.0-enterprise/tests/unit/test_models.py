"""
模型组件单元测试
"""

import pytest
from models import (
    CharacterStats, HealthComponent, ManaComponent,
    ExperienceComponent, TalentComponent, InventoryComponent,
    GameLog, RealmLevel, Cost, ActionResult
)


@pytest.mark.unit
class TestHealthComponent:
    """生命值组件测试"""

    def test_initialization(self):
        """测试初始化"""
        health = HealthComponent(100)
        assert health.max_hp == 100
        assert health.current_hp == 100
        assert health.recovery_rate == 1.0

    def test_restore(self):
        """测试恢复生命值"""
        health = HealthComponent(100)
        health.current_hp = 50

        # 正常恢复
        restored = health.restore(20)
        assert restored == 20
        assert health.current_hp == 70

        # 超过最大值
        restored = health.restore(50)
        assert restored == 30  # 只能恢复30到满血
        assert health.current_hp == 100

    def test_consume(self):
        """测试消耗生命值"""
        health = HealthComponent(100)
        health.current_hp = 80

        # 正常消耗
        consumed = health.consume(20)
        assert consumed == 20
        assert health.current_hp == 60

        # 消耗超过当前值
        consumed = health.consume(80)
        assert consumed == 60  # 只能消耗60
        assert health.current_hp == 0

    def test_is_alive(self):
        """测试存活状态"""
        health = HealthComponent(100)

        # 存活状态
        assert health.is_alive() is True

        # 死亡状态
        health.current_hp = 0
        assert health.is_alive() is False

    def test_get_hp_percentage(self):
        """测试生命值百分比"""
        health = HealthComponent(100)

        # 满血
        assert health.get_hp_percentage() == 1.0

        # 一半血量
        health.current_hp = 50
        assert health.get_hp_percentage() == 0.5

        # 空血
        health.current_hp = 0
        assert health.get_hp_percentage() == 0.0


@pytest.mark.unit
class TestManaComponent:
    """仙力值组件测试"""

    def test_initialization(self):
        """测试初始化"""
        mana = ManaComponent(100)
        assert mana.max_mp == 100
        assert mana.current_mp == 50  # 初始为一半
        assert mana.recovery_rate == 1.0

    def test_restore(self):
        """测试恢复仙力值"""
        mana = ManaComponent(100)
        mana.current_mp = 30

        restored = mana.restore(20)
        assert restored == 20
        assert mana.current_mp == 50

    def test_consume(self):
        """测试消耗仙力值"""
        mana = ManaComponent(100)
        mana.current_mp = 60

        # 成功消耗
        assert mana.consume(20) is True
        assert mana.current_mp == 40

        # 不足消耗
        assert mana.consume(50) is False
        assert mana.current_mp == 40  # 不变


@pytest.mark.unit
class TestExperienceComponent:
    """经验值组件测试"""

    def test_initialization(self):
        """测试初始化"""
        exp = ExperienceComponent()
        assert exp.total_experience == 0
        assert exp.current_level_experience == 0
        assert exp.current_realm == RealmLevel.QI_REFINING

    def test_add_experience_no_breakthrough(self):
        """测试添加经验但不突破"""
        exp = ExperienceComponent()

        # 添加少量经验
        breakthrough, msg = exp.add_experience(30)
        assert breakthrough is False
        assert msg is None
        assert exp.total_experience == 30
        assert exp.current_level_experience == 30

    def test_add_experience_with_breakthrough(self):
        """测试添加经验并突破"""
        exp = ExperienceComponent()

        # 添加足够经验突破
        breakthrough, msg = exp.add_experience(150)
        assert breakthrough is True
        assert "突破至" in msg
        assert exp.current_realm == RealmLevel.FOUNDATION
        assert exp.total_experience == 150
        assert exp.current_level_experience == 50  # 150 - 100

    def test_multiple_breakthroughs(self):
        """测试多次突破"""
        exp = ExperienceComponent()

        # 添加大量经验
        breakthrough, msg = exp.add_experience(300)
        assert breakthrough is True
        assert exp.current_realm == RealmLevel.CORE_FORMATION  # 炼气->筑基->结丹
        assert exp.current_level_experience == 0  # 300 - 100 - 200

    def test_get_progress_percentage(self):
        """测试获取进度百分比"""
        exp = ExperienceComponent()

        # 初始状态
        assert exp.get_progress_percentage() == 0.0

        # 添加50经验（阈值100）
        exp.add_experience(50)
        assert exp.get_progress_percentage() == 50.0

        # 突破后重置
        exp.add_experience(50)  # 总共100，应该突破
        assert exp.get_progress_percentage() == 0.0  # 新境界重新开始


@pytest.mark.unit
class TestTalentComponent:
    """资质组件测试"""

    def test_initialization(self):
        """测试初始化"""
        talent = TalentComponent(5)
        assert talent.base_talent == 5

    def test_random_initialization(self):
        """测试随机初始化"""
        talent = TalentComponent()
        assert 1 <= talent.base_talent <= 10

    def test_get_talent_bonus(self):
        """测试资质加成计算"""
        talent = TalentComponent(5)

        # 不同动作类型的加成
        meditate_bonus = talent.get_talent_bonus(10, "meditate")
        assert meditate_bonus == 10 + 5 * 0.8  # 10 + 4 = 14

        cultivate_bonus = talent.get_talent_bonus(10, "cultivate")
        assert cultivate_bonus == 10 + 5 * 1.5  # 10 + 7.5 = 17.5

        pill_bonus = talent.get_talent_bonus(10, "pill")
        assert pill_bonus == 10 + 5 * 1.0  # 10 + 5 = 15


@pytest.mark.unit
class TestInventoryComponent:
    """物品栏组件测试"""

    def test_initialization(self):
        """测试初始化"""
        inventory = InventoryComponent()
        assert inventory.get_item_count("pill") == 0

    def test_add_item(self):
        """测试添加物品"""
        inventory = InventoryComponent()

        # 添加物品
        assert inventory.add_item("pill", 3) is True
        assert inventory.get_item_count("pill") == 3

        # 继续添加
        assert inventory.add_item("pill", 2) is True
        assert inventory.get_item_count("pill") == 5

        # 添加不存在的物品
        assert inventory.add_item("unknown", 1) is False

    def test_consume_item(self):
        """测试消耗物品"""
        inventory = InventoryComponent()

        # 先添加物品
        inventory.add_item("pill", 5)

        # 成功消耗
        assert inventory.consume_item("pill", 2) is True
        assert inventory.get_item_count("pill") == 3

        # 不足消耗
        assert inventory.consume_item("pill", 5) is False
        assert inventory.get_item_count("pill") == 3  # 不变

        # 消耗不存在的物品
        assert inventory.consume_item("unknown", 1) is False


@pytest.mark.unit
class TestCharacterStats:
    """角色状态测试"""

    def test_initialization(self):
        """测试初始化"""
        character = CharacterStats("测试角色")
        assert character.name == "测试角色"
        assert character.is_alive() is True
        assert character.total_actions == 0
        assert character.meditation_streak == 0

    def test_can_perform_action(self):
        """测试检查是否可执行动作"""
        character = CharacterStats("测试角色")
        character.inventory.add_item("pill", 1)

        # 足够的消耗
        cost = Cost(hp=10, mp=20, pills=1)
        assert character.can_perform_action(cost) is True

        # 生命值不足
        character.health.current_hp = 5
        assert character.can_perform_action(cost) is False

        # 仙力不足
        character.health.current_hp = 50
        character.mana.current_mp = 10
        assert character.can_perform_action(cost) is False

        # 丹药不足
        character.mana.current_mp = 50
        character.inventory.items["pill"] = 0
        assert character.can_perform_action(cost) is False

    def test_apply_cost(self):
        """测试应用消耗"""
        character = CharacterStats("测试角色")
        character.inventory.add_item("pill", 2)

        cost = Cost(hp=5, mp=10, pills=1)

        # 成功应用消耗
        assert character.apply_cost(cost) is True
        assert character.health.current_hp == 95
        assert character.mana.current_mp == 40
        assert character.inventory.get_item_count("pill") == 1
        assert character.total_actions == 1

    def test_get_status_summary(self):
        """测试获取状态摘要"""
        character = CharacterStats("测试角色")
        summary = character.get_status_summary()

        assert summary["name"] == "测试角色"
        assert summary["hp"] == 100
        assert summary["max_hp"] == 100
        assert summary["mp"] == 50
        assert summary["max_mp"] == 100
        assert summary["realm"] == "炼气期"
        assert summary["talent"] >= 1 and summary["talent"] <= 10
        assert summary["pills"] == 0
        assert summary["alive"] is True


@pytest.mark.unit
class TestGameLog:
    """游戏日志测试"""

    def test_initialization(self):
        """测试初始化"""
        log = GameLog(5)
        assert log.max_entries == 5
        assert len(log.entries) == 0

    def test_add_entry(self):
        """测试添加日志条目"""
        log = GameLog(3)

        # 添加条目
        log.add_entry("第一条消息")
        assert len(log.entries) == 1
        assert log.entries[0] == "第一条消息"

        log.add_entry("第二条消息")
        assert len(log.entries) == 2

        log.add_entry("第三条消息")
        assert len(log.entries) == 3

        # 超过最大条目数
        log.add_entry("第四条消息")
        assert len(log.entries) == 3  # 保持最大数量
        assert log.entries[-1] == "第四条消息"  # 最新消息
        assert "第一条消息" not in log.entries  # 最早消息被移除

    def test_get_recent_entries(self):
        """测试获取最近条目"""
        log = GameLog()

        for i in range(5):
            log.add_entry(f"消息{i+1}")

        # 获取最近3条
        recent = log.get_recent_entries(3)
        assert len(recent) == 3
        assert recent == ["消息3", "消息4", "消息5"]

        # 获取超过总数的条目
        all_recent = log.get_recent_entries(10)
        assert len(all_recent) == 5
        assert all_recent == ["消息1", "消息2", "消息3", "消息4", "消息5"]

        # 空日志
        empty_log = GameLog()
        empty_recent = empty_log.get_recent_entries()
        assert empty_recent == ["开始你的修仙之旅..."]