"""
游戏核心单元测试
"""

import pytest
from core.game_core import GameCore, GameStateManager
from models import CharacterStats, RealmLevel


@pytest.mark.unit
class TestGameCore:
    """游戏核心测试"""

    def test_initialization(self):
        """测试初始化"""
        core = GameCore()
        assert core.character is None
        assert core.game_log is None
        assert core.available_actions
        assert len(core.available_actions) == 4
        assert core.is_game_over is False
        assert core.difficulty == "normal"

    def test_initialize_game_success(self):
        """测试成功初始化游戏"""
        core = GameCore()

        result = core.initialize_game("测试角色", "normal")

        assert result is True
        assert core.character is not None
        assert core.game_log is not None
        assert core.character.name == "测试角色"
        assert core.character.is_alive() is True
        assert core.is_game_over is False
        assert core.difficulty == "normal"

        # 检查初始日志
        recent_logs = core.game_log.get_recent_entries(3)
        assert any("欢迎" in log for log in recent_logs)
        assert any("资质" in log for log in recent_logs)

    def test_initialize_game_default_name(self):
        """测试使用默认名称初始化"""
        core = GameCore()

        result = core.initialize_game(None, "normal")

        assert result is True
        assert core.character.name == "无名修士"

    def test_initialize_game_different_difficulties(self):
        """测试不同难度初始化"""
        core = GameCore()

        # 简单难度
        core.initialize_game("测试", "easy")
        assert core.character.inventory.get_item_count("pill") == 3

        # 普通难度
        core.initialize_game("测试", "normal")
        assert core.character.inventory.get_item_count("pill") == 1

        # 困难难度
        core.initialize_game("测试", "hard")
        assert core.character.inventory.get_item_count("pill") == 0

    def test_execute_action_success(self, game_core):
        """测试成功执行动作"""
        result = game_core.execute_action("meditate")

        assert result["success"] is True
        assert "打坐" in result["message"]
        assert result["effects"]["mp_recovery"] > 0
        assert result["effects"]["exp_gain"] > 0
        assert result["costs"]["hp"] == 1

        # 检查角色状态变化
        assert game_core.character.meditation_streak == 1

    def test_execute_action_not_found(self, game_core):
        """测试执行不存在的动作"""
        result = game_core.execute_action("不存在的动作")

        assert result["success"] is False
        assert "未找到动作" in result["message"]
        assert result["effects"] == {}
        assert result["costs"] == {}

    def test_execute_action_insufficient_resources(self, game_core):
        """测试资源不足时执行动作"""
        # 设置仙力不足
        game_core.character.mana.current_mp = 10

        result = game_core.execute_action("cultivate")

        assert result["success"] is False
        assert "仙力不足" in result["message"]
        assert result["effects"] == {}
        assert result["costs"] == {}

    def test_execute_action_game_over(self, game_core):
        """测试游戏结束时执行动作"""
        # 设置角色死亡
        game_core.character.health.current_hp = 0
        game_core.is_game_over = True

        result = game_core.execute_action("meditate")

        assert result["success"] is False
        assert "游戏已结束" in result["message"]

    def test_execute_action_without_character(self):
        """测试没有角色时执行动作"""
        core = GameCore()  # 未初始化

        result = core.execute_action("meditate")

        assert result["success"] is False
        assert "游戏已结束" in result["message"]

    def test_get_game_state(self, game_core):
        """测试获取游戏状态"""
        state = game_core.get_game_state()

        assert "character" in state
        assert "game_log" in state
        assert "actions" in state
        assert "is_game_over" in state
        assert "difficulty" in state
        assert "power_level" in state
        assert "recommendation" in state

        assert state["character"] is game_core.character
        assert state["game_log"] is game_core.game_log
        assert state["is_game_over"] is False
        assert state["difficulty"] == "normal"

    def test_get_game_state_copy(self, game_core):
        """测试获取游戏状态副本"""
        state1 = game_core.get_game_state()
        state2 = game_core.get_game_state()

        # 修改状态1不应该影响状态2
        state1["test_field"] = "test_value"
        assert "test_field" not in state2

    def test_reset_game(self, game_core):
        """测试重置游戏"""
        # 修改游戏状态
        game_core.character.health.current_hp = 50
        game_core.character.inventory.add_item("pill", 5)
        game_core.execute_action("meditate")

        # 重置游戏
        result = game_core.reset_game()

        assert result is True
        assert game_core.character.health.current_hp == 100  # 重置为初始值
        assert game_core.character.inventory.get_item_count("pill") == 1  # 普通难度初始值
        assert game_core.character.meditation_streak == 0  # 重置为初始值
        assert game_core.is_game_over is False

    def test_reset_game_with_new_parameters(self, game_core):
        """测试用新参数重置游戏"""
        result = game_core.reset_game("新角色", "easy")

        assert result is True
        assert game_core.character.name == "新角色"
        assert game_core.difficulty == "easy"
        assert game_core.character.inventory.get_item_count("pill") == 3  # 简单难度

    def test_get_game_statistics(self, game_core):
        """测试获取游戏统计信息"""
        stats = game_core.get_game_statistics()

        assert "total_actions" in stats
        assert "total_experience" in stats
        assert "current_realm" in stats
        assert "talent" in stats
        assert "pills_used" in stats
        assert "max_meditation_streak" in stats
        assert "power_level" in stats
        assert "difficulty" in stats

        assert stats["total_actions"] == 0
        assert stats["current_realm"] == "炼气期"
        assert stats["difficulty"] == "normal"

        # 执行一些动作后检查统计
        game_core.execute_action("meditate")
        game_core.execute_action("meditate")

        updated_stats = game_core.get_game_statistics()
        assert updated_stats["total_actions"] == 2

    def test_get_game_statistics_without_character(self):
        """测试没有角色时获取统计信息"""
        core = GameCore()  # 未初始化

        stats = core.get_game_statistics()
        assert stats == {}

    def test_get_available_actions(self, game_core):
        """测试获取可用动作"""
        actions = game_core.get_available_actions()

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "打坐" in actions
        assert "等待" in actions

        # 角色应该可以执行大部分动作
        assert len(actions) >= 3

    def test_get_available_actions_game_over(self, game_core):
        """测试游戏结束时获取可用动作"""
        game_core.character.health.current_hp = 0
        game_core.is_game_over = True

        actions = game_core.get_available_actions()
        assert actions == []

    def test_get_available_actions_without_character(self):
        """测试没有角色时获取可用动作"""
        core = GameCore()  # 未初始化

        actions = core.get_available_actions()
        assert actions == []

    def test_get_character_info(self, game_core):
        """测试获取角色信息"""
        info = game_core.get_character_info()

        assert "name" in info
        assert "hp" in info
        assert "mp" in info
        assert "realm" in info
        assert "talent" in info
        assert "pills" in info
        assert "alive" in info

        assert info["name"] == "测试角色"
        assert info["alive"] is True

    def test_is_action_available(self, game_core):
        """测试检查动作是否可用"""
        assert game_core.is_action_available("meditate") is True
        assert game_core.is_action_available("wait") is True

        # 需要资源的动作
        assert game_core.is_action_available("cultivate") is True  # 初始50MP，足够

        # 消耗丹药的动作
        game_core.character.inventory.add_item("pill", 1)
        assert game_core.is_action_available("consume_pill") is True

        game_core.character.inventory.items["pill"] = 0
        assert game_core.is_action_available("consume_pill") is False

    def test_is_action_available_invalid_action(self, game_core):
        """测试检查无效动作"""
        assert game_core.is_action_available("不存在的动作") is False

    def test_get_action_description(self, game_core):
        """测试获取动作描述"""
        desc = game_core.get_action_description("meditate")
        assert "冥想" in desc

        desc = game_core.get_action_description("consume_pill")
        assert "丹药" in desc

        desc = game_core.get_action_description("不存在的动作")
        assert desc == "未知动作"

    def test_get_action_cost(self, game_core):
        """测试获取动作消耗"""
        cost = game_core.get_action_cost("meditate")
        assert cost["hp"] == 1
        assert cost["mp"] == 0
        assert cost["pills"] == 0

        cost = game_core.get_action_cost("cultivate")
        assert cost["mp"] == 20

        cost = game_core.get_action_cost("consume_pill")
        assert cost["pills"] == 1

        cost = game_core.get_action_cost("不存在的动作")
        assert cost == {}

    def test_simulate_action(self, game_core):
        """测试模拟动作执行"""
        result = game_core.simulate_action("meditate")

        assert result["success"] is True
        assert "预期执行" in result["message"]
        assert result["costs"]["hp"] == 1
        assert result["costs"]["mp"] == 0
        assert result["costs"]["pills"] == 0

        # 模拟不应该实际改变角色状态
        original_hp = game_core.character.health.current_hp
        game_core.simulate_action("meditate")
        assert game_core.character.health.current_hp == original_hp

    def test_simulate_action_invalid(self, game_core):
        """测试模拟无效动作"""
        result = game_core.simulate_action("不存在的动作")

        assert result["success"] is False
        assert "未找到动作" in result["message"]

    def test_simulate_action_insufficient_resources(self, game_core):
        """测试模拟资源不足的动作"""
        game_core.character.mana.current_mp = 10

        result = game_core.simulate_action("cultivate")

        assert result["success"] is False
        assert "仙力不足" in result["message"]

    def test_game_over_detection(self, game_core):
        """测试游戏结束检测"""
        # 角色死亡
        game_core.character.health.current_hp = 0
        game_core.execute_action("meditate")  # 任何动作都会触发游戏结束检查

        assert game_core.is_game_over is True
        assert any("失败" in log for log in game_core.game_log.get_recent_entries(5))

    def test_victory_detection(self, game_core):
        """测试胜利检测"""
        # 添加大量经验直接到飞升
        game_core.character.experience.total_experience = 10000
        game_core.character.experience.current_realm = RealmLevel.ASCENSION

        game_core.execute_action("meditate")  # 任何动作都会检查游戏结束

        assert game_core.is_game_over is True
        assert any("飞升" in log for log in game_core.game_log.get_recent_entries(5))

    def test_save_and_load_not_implemented(self, game_core):
        """测试保存和加载功能（未实现）"""
        assert game_core.save_game() is False
        assert game_core.load_game() is False


@pytest.mark.unit
class TestGameStateManager:
    """游戏状态管理器测试"""

    def test_initialization(self):
        """测试初始化"""
        manager = GameStateManager()
        assert manager.current_state == {}
        assert manager.state_history == []
        assert manager.max_history_size == 50

    def test_update_state(self):
        """测试更新状态"""
        manager = GameStateManager()
        state1 = {"test": "value1"}
        state2 = {"test": "value2"}

        manager.update_state(state1)
        assert manager.current_state == state1
        assert len(manager.state_history) == 0  # 第一次更新没有历史

        manager.update_state(state2)
        assert manager.current_state == state2
        assert len(manager.state_history) == 1
        assert manager.state_history[0]["state"] == state1

    def test_get_current_state(self):
        """测试获取当前状态"""
        manager = GameStateManager()
        state = {"test": "value"}

        manager.update_state(state)
        current = manager.get_current_state()

        assert current == state
        # 应该是副本，不是引用
        current["new_field"] = "new_value"
        assert "new_field" not in manager.current_state

    def test_get_previous_state(self):
        """测试获取之前状态"""
        manager = GameStateManager()
        state1 = {"test": "value1"}
        state2 = {"test": "value2"}
        state3 = {"test": "value3"}

        manager.update_state(state1)
        manager.update_state(state2)
        manager.update_state(state3)

        # 获取前一个状态
        prev1 = manager.get_previous_state(1)
        assert prev1 == state2

        # 获取前两个状态
        prev2 = manager.get_previous_state(2)
        assert prev2 == state1

        # 获取超出范围的状态
        prev3 = manager.get_previous_state(5)
        assert prev3 is None

    def test_rollback_state(self):
        """测试回滚状态"""
        manager = GameStateManager()
        state1 = {"test": "value1"}
        state2 = {"test": "value2"}
        state3 = {"test": "value3"}

        manager.update_state(state1)
        manager.update_state(state2)
        manager.update_state(state3)

        # 回滚一步
        success = manager.rollback_state(1)
        assert success is True
        assert manager.current_state == state2
        assert len(manager.state_history) == 1  # 历史记录被清理

        # 回滚两步（现在只有一步历史）
        success = manager.rollback_state(2)
        assert success is False  # 不能回滚那么多步

    def test_clear_history(self):
        """测试清空历史"""
        manager = GameStateManager()
        state1 = {"test": "value1"}
        state2 = {"test": "value2"}

        manager.update_state(state1)
        manager.update_state(state2)

        assert len(manager.state_history) == 1

        manager.clear_history()
        assert len(manager.state_history) == 0
        assert manager.current_state == state2  # 当前状态不受影响

    def test_history_size_limit(self):
        """测试历史大小限制"""
        manager = GameStateManager()
        manager.max_history_size = 3

        # 添加超过限制的状态
        for i in range(5):
            manager.update_state({"test": f"value{i}"})

        # 历史大小应该被限制
        assert len(manager.state_history) == 3
        # 应该保留最新的状态
        assert manager.state_history[-1]["state"]["test"] == "value3"