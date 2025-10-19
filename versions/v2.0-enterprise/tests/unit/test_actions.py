"""
动作系统单元测试
"""

import pytest
from actions import (
    MeditateAction, ConsumePillAction, CultivateAction, WaitAction,
    ActionFactory, ActionResult
)
from models import CharacterStats, GameLog


@pytest.mark.unit
class TestMeditateAction:
    """打坐动作测试"""

    def test_initialization(self):
        """测试初始化"""
        action = MeditateAction()
        assert action.name == "打坐"
        assert "冥想" in action.description

    def test_get_cost(self):
        """测试获取消耗"""
        action = MeditateAction()
        cost = action.get_cost()
        assert cost.hp == 1
        assert cost.mp == 0
        assert cost.pills == 0
        assert cost.time == 1

    def test_can_execute_alive_character(self, character):
        """测试存活角色可以执行"""
        action = MeditateAction()
        assert action.can_execute(character) is True

    def test_can_execute_dead_character(self, dead_character):
        """测试死亡角色不能执行"""
        action = MeditateAction()
        assert action.can_execute(dead_character) is False

    def test_execute_normal(self, character, game_log):
        """测试正常执行"""
        action = MeditateAction()
        initial_hp = character.health.current_hp
        initial_mp = character.mana.current_mp
        initial_exp = character.experience.total_experience

        result = action.execute(character, game_log)

        assert result.success is True
        assert "打坐" in result.message
        assert result.effects["mp_recovery"] > 0
        assert result.effects["exp_gain"] > 0
        assert result.costs["hp"] == 1

        # 检查状态变化
        assert character.health.current_hp == initial_hp - 1
        assert character.mana.current_mp > initial_mp
        assert character.experience.total_experience > initial_exp
        assert character.meditation_streak == 1

    def test_execute_with_pill_bonus(self, character, game_log):
        """测试连续打坐获得丹药奖励"""
        action = MeditateAction()

        # 设置连续4次
        character.meditation_streak = 4
        initial_pills = character.inventory.get_item_count("pill")

        result = action.execute(character, game_log)

        assert result.success is True
        assert result.effects["pill_bonus"] == 1
        assert character.inventory.get_item_count("pill") == initial_pills + 1
        assert character.meditation_streak == 5

    def test_execute_dead_character(self, dead_character, game_log):
        """测试死亡角色执行失败"""
        action = MeditateAction()

        result = action.execute(dead_character, game_log)

        assert result.success is False
        assert "无法执行" in result.message


@pytest.mark.unit
class TestConsumePillAction:
    """服用丹药动作测试"""

    def test_initialization(self):
        """测试初始化"""
        action = ConsumePillAction()
        assert action.name == "吃丹药"
        assert "丹药" in action.description

    def test_get_cost(self):
        """测试获取消耗"""
        action = ConsumePillAction()
        cost = action.get_cost()
        assert cost.hp == 0
        assert cost.mp == 0
        assert cost.pills == 1

    def test_can_execute_with_pills(self, character):
        """测试有丹药时可以执行"""
        action = ConsumePillAction()
        character.inventory.add_item("pill", 1)
        assert action.can_execute(character) is True

    def test_can_execute_without_pills(self, character):
        """测试无丹药时不能执行"""
        action = ConsumePillAction()
        assert action.can_execute(character) is False

    def test_can_execute_dead_character(self, dead_character):
        """测试死亡角色不能执行"""
        action = ConsumePillAction()
        dead_character.inventory.add_item("pill", 1)
        assert action.can_execute(dead_character) is False

    def test_execute_normal(self, character, game_log):
        """测试正常执行"""
        action = ConsumePillAction()
        character.inventory.add_item("pill", 1)

        initial_hp = character.health.current_hp
        initial_mp = character.mana.current_mp
        initial_exp = character.experience.total_experience
        initial_pills = character.inventory.get_item_count("pill")

        result = action.execute(character, game_log)

        assert result.success is True
        assert "丹药" in result.message
        assert result.effects["hp_recovery"] > 0
        assert result.effects["mp_recovery"] > 0
        assert result.effects["exp_gain"] > 0
        assert result.costs["pills"] == 1

        # 检查状态变化
        assert character.health.current_hp > initial_hp
        assert character.mana.current_mp > initial_mp
        assert character.experience.total_experience > initial_exp
        assert character.inventory.get_item_count("pill") == initial_pills - 1
        assert character.meditation_streak == 0  # 重置连续计数

    def test_execute_without_pills(self, character, game_log):
        """测试无丹药时执行失败"""
        action = ConsumePillAction()

        result = action.execute(character, game_log)

        assert result.success is False
        assert "没有丹药" in result.message


@pytest.mark.unit
class TestCultivateAction:
    """修炼动作测试"""

    def test_initialization(self):
        """测试初始化"""
        action = CultivateAction()
        assert action.name == "修炼"
        assert "心法" in action.description

    def test_get_cost(self):
        """测试获取消耗"""
        action = CultivateAction()
        cost = action.get_cost()
        assert cost.hp == 0
        assert cost.mp == 20
        assert cost.pills == 0
        assert cost.time == 2

    def test_can_execute_with_mp(self, character):
        """测试有足够仙力时可以执行"""
        action = CultivateAction()
        character.mana.current_mp = 50
        assert action.can_execute(character) is True

    def test_can_execute_without_mp(self, character):
        """测试仙力不足时不能执行"""
        action = CultivateAction()
        character.mana.current_mp = 10
        assert action.can_execute(character) is False

    def test_can_execute_dead_character(self, dead_character):
        """测试死亡角色不能执行"""
        action = CultivateAction()
        dead_character.mana.current_mp = 50
        assert action.can_execute(dead_character) is False

    def test_execute_normal(self, character, game_log):
        """测试正常执行"""
        action = CultivateAction()
        character.mana.current_mp = 50

        initial_mp = character.mana.current_mp
        initial_exp = character.experience.total_experience

        result = action.execute(character, game_log)

        assert result.success is True
        assert "修炼" in result.message
        assert result.effects["exp_gain"] > 0
        assert result.costs["mp"] == 20

        # 检查状态变化
        assert character.mana.current_mp == initial_mp - 20
        assert character.experience.total_experience > initial_exp
        assert character.meditation_streak == 0  # 重置连续计数

    def test_execute_insufficient_mp(self, character, game_log):
        """测试仙力不足时执行失败"""
        action = CultivateAction()
        character.mana.current_mp = 10

        result = action.execute(character, game_log)

        assert result.success is False
        assert "仙力不足" in result.message


@pytest.mark.unit
class TestWaitAction:
    """等待动作测试"""

    def test_initialization(self):
        """测试初始化"""
        action = WaitAction()
        assert action.name == "等待"
        assert "养神" in action.description

    def test_get_cost(self):
        """测试获取消耗"""
        action = WaitAction()
        cost = action.get_cost()
        assert cost.hp == 1
        assert cost.mp == 0
        assert cost.pills == 0
        assert cost.time == 1

    def test_can_execute_alive_character(self, character):
        """测试存活角色可以执行"""
        action = WaitAction()
        assert action.can_execute(character) is True

    def test_can_execute_dead_character(self, dead_character):
        """测试死亡角色不能执行"""
        action = WaitAction()
        assert action.can_execute(dead_character) is False

    def test_execute_normal(self, character, game_log):
        """测试正常执行"""
        action = WaitAction()

        initial_hp = character.health.current_hp
        initial_mp = character.mana.current_mp

        result = action.execute(character, game_log)

        assert result.success is True
        assert "等待" in result.message
        assert result.effects["hp_recovery"] > 0
        assert result.effects["mp_recovery"] > 0
        assert result.costs["hp"] == 1

        # 检查状态变化
        assert character.health.current_hp > initial_hp - 1  # 恢复可能大于消耗
        assert character.mana.current_mp > initial_mp
        assert character.meditation_streak == 0  # 重置连续计数


@pytest.mark.unit
class TestActionFactory:
    """动作工厂测试"""

    def test_get_all_actions(self):
        """测试获取所有动作"""
        actions = ActionFactory.get_all_actions()
        assert len(actions) == 4

        action_names = [action.name for action in actions]
        assert "meditate" in action_names
        assert "consume_pill" in action_names
        assert "cultivate" in action_names
        assert "wait" in action_names

    def test_get_action_by_name(self):
        """测试根据名称获取动作"""
        meditate = ActionFactory.get_action_by_name("meditate")
        assert meditate is not None
        assert isinstance(meditate, MeditateAction)

        consume_pill = ActionFactory.get_action_by_name("consume_pill")
        assert consume_pill is not None
        assert isinstance(consume_pill, ConsumePillAction)

        cultivate = ActionFactory.get_action_by_name("cultivate")
        assert cultivate is not None
        assert isinstance(cultivate, CultivateAction)

        wait = ActionFactory.get_action_by_name("wait")
        assert wait is not None
        assert isinstance(wait, WaitAction)

    def test_get_action_by_name_not_found(self):
        """测试获取不存在的动作"""
        action = ActionFactory.get_action_by_name("不存在的动作")
        assert action is None

    def test_action_consistency(self, all_actions):
        """测试动作的一致性"""
        for action in all_actions:
            # 检查基本属性
            assert hasattr(action, 'name')
            assert hasattr(action, 'description')
            assert hasattr(action, 'get_cost')
            assert hasattr(action, 'can_execute')
            assert hasattr(action, 'execute')

            # 检查名称不为空
            assert action.name
            assert len(action.name) > 0

            # 检查描述不为空
            assert action.description
            assert len(action.description) > 0

            # 检查消耗方法返回有效结果
            cost = action.get_cost()
            assert hasattr(cost, 'hp')
            assert hasattr(cost, 'mp')
            assert hasattr(cost, 'pills')
            assert hasattr(cost, 'time')


@pytest.mark.unit
class TestActionResult:
    """动作结果测试"""

    def test_action_result_creation(self):
        """测试动作结果创建"""
        result = ActionResult(
            success=True,
            message="成功执行",
            effects={"hp_recovery": 10},
            costs={"mp": 5}
        )

        assert result.success is True
        assert result.message == "成功执行"
        assert result.effects["hp_recovery"] == 10
        assert result.costs["mp"] == 5

    def test_action_result_with_empty_data(self):
        """测试空数据的动作结果"""
        result = ActionResult(False, "失败", {}, {})

        assert result.success is False
        assert result.message == "失败"
        assert result.effects == {}
        assert result.costs == {}