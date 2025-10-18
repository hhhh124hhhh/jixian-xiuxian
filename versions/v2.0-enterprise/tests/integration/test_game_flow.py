"""
游戏流程集成测试
"""

import pytest
from core.game_core import GameCore
from application import GameApplication
from models import RealmLevel


@pytest.mark.integration
class TestGameFlowIntegration:
    """游戏流程集成测试"""

    def test_complete_game_session(self):
        """测试完整的游戏会话"""
        core = GameCore()

        # 初始化游戏
        assert core.initialize_game("集成测试角色", "normal") is True
        assert core.character.is_alive() is True
        assert core.character.experience.current_realm == RealmLevel.QI_REFINING

        # 执行一系列动作
        initial_hp = core.character.health.current_hp
        initial_mp = core.character.mana.current_mp
        initial_exp = core.character.experience.total_experience

        # 打坐几次
        for i in range(3):
            result = core.execute_action("meditate")
            assert result["success"] is True
            assert result["effects"]["mp_recovery"] > 0
            assert result["effects"]["exp_gain"] > 0

        # 应该有连续打坐奖励
        assert core.character.meditation_streak == 3

        # 服用丹药（如果有）
        if core.character.inventory.get_item_count("pill") > 0:
            result = core.execute_action("consume_pill")
            assert result["success"] is True
            assert result["effects"]["hp_recovery"] > 0
            assert result["effects"]["mp_recovery"] > 0

        # 修炼几次
        for i in range(2):
            if core.character.mana.current_mp >= 20:
                result = core.execute_action("cultivate")
                assert result["success"] is True
                assert result["effects"]["exp_gain"] > 0
                assert result["costs"]["mp"] == 20

        # 检查整体状态变化
        final_hp = core.character.health.current_hp
        final_mp = core.character.mana.current_mp
        final_exp = core.character.experience.total_experience

        # 经验应该增加
        assert final_exp > initial_exp

        # 检查统计信息
        stats = core.get_game_statistics()
        assert stats["total_actions"] > 0
        assert stats["current_realm"] == "炼气期" or stats["current_realm"] == "筑基期"

    def test_difficulty_impact(self):
        """测试不同难度对游戏的影响"""
        # 简单难度
        easy_core = GameCore()
        easy_core.initialize_game("简单难度角色", "easy")
        easy_initial_pills = easy_core.character.inventory.get_item_count("pill")

        # 普通难度
        normal_core = GameCore()
        normal_core.initialize_game("普通难度角色", "normal")
        normal_initial_pills = normal_core.character.inventory.get_item_count("pill")

        # 困难难度
        hard_core = GameCore()
        hard_core.initialize_game("困难难度角色", "hard")
        hard_initial_pills = hard_core.character.inventory.get_item_count("pill")

        # 验证初始资源差异
        assert easy_initial_pills >= normal_initial_pills >= hard_initial_pills

        # 执行相同动作，比较效果
        easy_result = easy_core.execute_action("meditate")
        normal_result = normal_core.execute_action("meditate")
        hard_result = hard_core.execute_action("meditate")

        # 所有难度的基础效果应该相同，但难度会影响后续的游戏体验
        assert easy_result["success"] is True
        assert normal_result["success"] is True
        assert hard_result["success"] is True

    def test_character_death_flow(self):
        """测试角色死亡流程"""
        core = GameCore()
        core.initialize_game("死亡测试角色", "normal")

        # 创建低生命值角色
        core.character.health.current_hp = 5
        core.character.mana.current_mp = 10
        core.character.inventory.items["pill"] = 0

        # 执行消耗生命的动作直到死亡
        death_action_count = 0
        while core.character.is_alive():
            result = core.execute_action("meditate")
            death_action_count += 1

            if death_action_count > 10:  # 防止无限循环
                break

        assert core.character.is_alive() is False
        assert core.is_game_over is True

        # 游戏结束后不能执行动作
        result = core.execute_action("meditate")
        assert result["success"] is False
        assert "游戏已结束" in result["message"]

    def test_level_breakthrough_flow(self):
        """测试境界突破流程"""
        core = GameCore()
        core.initialize_game("突破测试角色", "normal")

        initial_realm = core.character.experience.current_realm
        assert initial_realm == RealmLevel.QI_REFINING

        # 添加足够经验进行突破
        # 直接通过经验系统添加，避免大量重复动作
        core.character.experience.add_experience(150)  # 足够突破到筑基期

        # 检查是否突破
        new_realm = core.character.experience.current_realm
        assert new_realm == RealmLevel.FOUNDATION

        # 继续添加经验进行多次突破
        core.character.experience.add_experience(250)  # 应该突破到结丹期
        assert core.character.experience.current_realm == RealmLevel.CORE_FORMATION

    def test_resource_management_flow(self):
        """测试资源管理流程"""
        core = GameCore()
        core.initialize_game("资源管理角色", "normal")

        # 记录初始资源
        initial_hp = core.character.health.current_hp
        initial_mp = core.character.mana.current_mp
        initial_pills = core.character.inventory.get_item_count("pill")

        # 消耗仙力的动作
        if core.character.mana.current_mp >= 20:
            result = core.execute_action("cultivate")
            assert result["success"] is True
            assert core.character.mana.current_mp == initial_mp - 20

        # 恢复仙力的动作
        result = core.execute_action("meditate")
        assert result["success"] is True
        assert core.character.mana.current_mp > initial_mp - 20

        # 丹药管理
        # 先获得一些丹药（通过连续打坐）
        core.character.meditation_streak = 4
        core.execute_action("meditate")  # 应该获得丹药奖励
        pills_after_meditation = core.character.inventory.get_item_count("pill")

        # 使用丹药
        if pills_after_meditation > 0:
            result = core.execute_action("consume_pill")
            assert result["success"] is True
            assert core.character.inventory.get_item_count("pill") == pills_after_meditation - 1

    def test_action_sequence_optimization(self):
        """测试动作序列优化"""
        core = GameCore()
        core.initialize_game("优化测试角色", "normal")

        # 测试不同的动作序列
        sequences = [
            ["meditate", "meditate", "cultivate", "cultivate"],
            ["cultivate", "cultivate", "meditate", "meditate"],
            ["meditate", "cultivate", "meditate", "cultivate"]
        ]

        results = []

        for sequence in sequences:
            # 重置游戏状态
            core.reset_game("优化测试角色", "normal")

            # 设置一致的初始条件
            core.character.mana.current_mp = 60
            core.character.inventory.add_item("pill", 1)

            # 执行动作序列
            total_exp_gain = 0
            for action in sequence:
                result = core.execute_action(action)
                if result["success"]:
                    total_exp_gain += result["effects"].get("exp_gain", 0)

            results.append(total_exp_gain)

        # 不同序列应该有不同的效果
        assert len(set(results)) >= 2  # 至少有两种不同的结果

    def test_edge_case_scenarios(self):
        """测试边缘场景"""
        core = GameCore()
        core.initialize_game("边缘测试角色", "normal")

        # 场景1: 最小生命值
        core.character.health.current_hp = 1
        result = core.execute_action("meditate")
        assert result["success"] is True  # 应该还能执行，但会死亡
        assert core.character.health.current_hp == 0

        # 重置并继续测试
        core.reset_game("边缘测试角色", "normal")

        # 场景2: 最小仙力值
        core.character.mana.current_mp = 0
        result = core.execute_action("cultivate")
        assert result["success"] is False
        assert "仙力不足" in result["message"]

        # 场景3: 最大连续打坐
        core.character.meditation_streak = 100
        result = core.execute_action("meditate")
        assert result["success"] is True
        assert result["effects"]["pill_bonus"] >= 1  # 应该仍然有丹药奖励


@pytest.mark.integration
@pytest.mark.slow
class TestGameApplicationIntegration:
    """游戏应用程序集成测试"""

    def test_application_initialization(self):
        """测试应用程序初始化"""
        app = GameApplication()

        # 测试初始化（不涉及实际UI渲染）
        # 这里我们只测试游戏核心的初始化
        assert app.game_core.initialize_game("应用测试角色", "normal") is True
        assert app.game_core.character is not None
        assert app.game_core.character.name == "应用测试角色"

    def test_application_action_flow(self):
        """测试应用程序动作流程"""
        app = GameApplication()

        # 初始化游戏
        app.game_core.initialize_game("流程测试角色", "normal")

        # 模拟UI动作选择
        app._on_action_selected("meditate")
        assert app.total_actions == 1

        app._on_action_selected("cultivate")
        assert app.total_actions == 2

        # 检查游戏状态
        game_state = app.game_core.get_game_state()
        assert game_state["character"].health.current_hp < 100  # 被消耗了
        assert game_state["character"].experience.total_experience > 0  # 获得了经验

    def test_application_restart_flow(self):
        """测试应用程序重启流程"""
        app = GameApplication()

        # 初始化并执行一些动作
        app.game_core.initialize_game("重启测试角色", "normal")
        app.game_core.execute_action("meditate")
        app.total_actions = 5  # 模拟一些动作

        # 重启游戏
        app._restart_game()

        # 检查重启后的状态
        assert app.game_core.character.name == "重启测试角色"
        assert app.game_core.character.health.current_hp == 100
        assert app.game_core.character.meditation_streak == 0
        assert app.total_actions == 0

    def test_session_statistics_tracking(self):
        """测试会话统计跟踪"""
        app = GameApplication()

        # 初始化游戏
        app.game_core.initialize_game("统计测试角色", "normal")
        app.start_time = 0  # 设置固定时间用于测试

        # 执行一些动作
        for i in range(3):
            app._execute_action("meditate")

        # 保存会话统计
        app._save_session_statistics()

        # 检查统计信息
        stats = app.session_statistics
        assert "total_actions" in stats
        assert stats["total_actions"] == 3
        assert "final_stats" in stats
        assert stats["final_stats"]["total_experience"] > 0
        assert "achievements" in stats

    def test_game_over_handling(self):
        """测试游戏结束处理"""
        app = GameApplication()

        # 初始化并设置角色死亡
        app.game_core.initialize_game("结束测试角色", "normal")
        app.game_core.character.health.current_hp = 0
        app.game_core.is_game_over = True

        # 处理游戏结束
        app._handle_game_over()

        # 应该保存了统计信息
        assert app.session_statistics != {}

    def test_application_info(self):
        """测试应用程序信息"""
        app = GameApplication()

        info = app.get_application_info()
        assert "version" in info
        assert "name" in info
        assert "running" in info
        assert "ui_type" in info
        assert info["name"] == "极简修仙 MVP"
        assert info["version"] == "1.0.0"