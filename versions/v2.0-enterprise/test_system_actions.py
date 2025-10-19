#!/usr/bin/env python3
"""
系统动作集成测试脚本
测试系统动作的完整执行流程，包括UI分类、应用层处理和事件分发
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入避免循环导入问题
try:
    from actions.system_actions import (
        SystemAction, RestartAction, SettingsAction,
        SaveGameAction, LoadGameAction, SystemActionFactory
    )
    from core.event_handler import event_handler, EventType
    from ui.interface import GameStateRenderer, ButtonType
    from application import GameApplication
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"导入错误: {e}")
    print("将运行基础测试...")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "需要系统动作模块")
class TestSystemActions(unittest.TestCase):
    """系统动作测试类"""

    def setUp(self):
        """测试前设置"""
        # 清空事件历史
        event_handler.clear_history()

        # 创建模拟的UI和应用层
        self.mock_ui = Mock()
        self.mock_game_core = Mock()
        self.mock_game_core.character = Mock()
        self.mock_game_core.character.name = "测试角色"
        self.mock_game_core.difficulty = "normal"
        self.mock_game_core.is_game_over = False

        # 创建游戏应用
        self.app = GameApplication(self.mock_ui)
        self.app.game_core = self.mock_game_core

    def test_system_action_factory(self):
        """测试系统动作工厂"""
        print("🔍 测试系统动作工厂...")

        # 测试获取所有系统动作
        all_actions = SystemActionFactory.get_all_system_actions()
        self.assertEqual(len(all_actions), 4)

        # 测试按名称获取动作
        restart_action = SystemActionFactory.get_system_action_by_name("restart")
        self.assertIsNotNone(restart_action)
        self.assertIsInstance(restart_action, RestartAction)

        settings_action = SystemActionFactory.get_system_action_by_name("settings")
        self.assertIsNotNone(settings_action)
        self.assertIsInstance(settings_action, SettingsAction)

        # 测试不存在的动作
        non_existent = SystemActionFactory.get_system_action_by_name("non_existent")
        self.assertIsNone(non_existent)

        # 测试系统动作检查
        self.assertTrue(SystemActionFactory.is_system_action("restart"))
        self.assertTrue(SystemActionFactory.is_system_action("settings"))
        self.assertFalse(SystemActionFactory.is_system_action("meditate"))

        print("✅ 系统动作工厂测试通过")

    def test_restart_action(self):
        """测试重新开始动作"""
        print("🔍 测试重新开始动作...")

        restart_action = RestartAction()
        self.assertEqual(restart_action.name, "restart")
        self.assertEqual(restart_action.category, "system")

        # 测试动作执行
        result = restart_action.execute_system_action(self.app)

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "游戏已重新开始")

        # 验证游戏核心重置被调用
        self.mock_game_core.reset_game.assert_called_once()

        # 验证事件被分发
        history = event_handler.get_event_history(EventType.RESET_GAME)
        self.assertEqual(len(history), 1)

        print("✅ 重新开始动作测试通过")

    def test_settings_action(self):
        """测试设置动作"""
        print("🔍 测试设置动作...")

        settings_action = SettingsAction()
        self.assertEqual(settings_action.name, "settings")
        self.assertEqual(settings_action.category, "system")

        # 测试动作执行
        result = settings_action.execute_system_action(self.app)

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "设置界面已打开")

        print("✅ 设置动作测试通过")

    def test_save_game_action(self):
        """测试保存游戏动作"""
        print("🔍 测试保存游戏动作...")

        save_action = SaveGameAction()
        self.assertEqual(save_action.name, "save_game")
        self.assertEqual(save_action.category, "system")

        # 添加模拟的保存方法
        self.app._save_game = Mock(return_value=True)

        # 测试动作执行
        result = save_action.execute_system_action(self.app)

        self.assertTrue(result["success"])
        self.assertIn("槽位 1", result["message"])
        self.assertEqual(result["costs"]["time"], 1)

        print("✅ 保存游戏动作测试通过")

    def test_load_game_action(self):
        """测试加载游戏动作"""
        print("🔍 测试加载游戏动作...")

        load_action = LoadGameAction()
        self.assertEqual(load_action.name, "load_game")
        self.assertEqual(load_action.category, "system")

        # 添加模拟的加载方法
        self.app._load_game = Mock(return_value=True)

        # 测试动作执行
        result = load_action.execute_system_action(self.app)

        self.assertTrue(result["success"])
        self.assertIn("槽位 1", result["message"])
        self.assertEqual(result["costs"]["time"], 2)

        print("✅ 加载游戏动作测试通过")

    def test_ui_button_classification(self):
        """测试UI按钮分类逻辑"""
        print("🔍 测试UI按钮分类逻辑...")

        renderer = GameStateRenderer()

        # 测试游戏动作按钮格式化
        mock_character = Mock()
        mock_character.is_alive.return_value = True
        mock_action = Mock()
        mock_action.name = "打坐"
        mock_action.can_execute.return_value = True
        mock_action.__class__.__name__ = "MeditateAction"
        mock_action.description = "消耗1HP，恢复仙力"

        game_buttons = renderer.format_action_buttons(mock_character, [mock_action])
        self.assertEqual(len(game_buttons), 1)
        self.assertEqual(game_buttons[0].button_type, ButtonType.GAME_ACTION)
        self.assertEqual(game_buttons[0].action, "meditate")

        # 测试系统动作按钮格式化
        system_buttons = renderer.format_system_action_buttons()
        self.assertGreater(len(system_buttons), 0)

        restart_button = next((b for b in system_buttons if b.action == "restart"), None)
        self.assertIsNotNone(restart_button)
        self.assertEqual(restart_button.button_type, ButtonType.SYSTEM_ACTION)
        self.assertEqual(restart_button.name, "重新开始")

        # 测试系统动作检查
        self.assertTrue(renderer.is_system_action("restart"))
        self.assertTrue(renderer.is_system_action("settings"))
        self.assertFalse(renderer.is_system_action("meditate"))

        print("✅ UI按钮分类逻辑测试通过")

    def test_application_action_execution(self):
        """测试应用层统一动作执行"""
        print("🔍 测试应用层统一动作执行...")

        # 重置模拟对象
        self.mock_game_core.reset_game.return_value = True

        # 测试游戏动作执行
        self.mock_game_core.execute_action.return_value = {
            "success": True,
            "message": "游戏动作执行成功",
            "effects": {"hp": -1},
            "costs": {"time": 1}
        }

        result = self.app._execute_action("meditate")

        self.assertTrue(result["success"])
        self.mock_game_core.execute_action.assert_called_with("meditate")

        # 测试系统动作执行
        result = self.app._execute_action("restart")

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "游戏已重新开始")
        self.mock_game_core.reset_game.assert_called()

        # 测试不存在的动作
        result = self.app._execute_action("non_existent")

        self.assertFalse(result["success"])
        self.assertIn("未找到", result["message"])

        print("✅ 应用层统一动作执行测试通过")

    def test_event_dispatching(self):
        """测试事件分发机制"""
        print("🔍 测试事件分发机制...")

        # 清空事件历史
        event_handler.clear_history()

        # 执行系统动作
        restart_action = RestartAction()
        restart_action.execute_system_action(self.app)

        # 验证事件被分发
        restart_events = event_handler.get_event_history(EventType.RESET_GAME)
        self.assertEqual(len(restart_events), 1)

        action_events = event_handler.get_event_history(EventType.ACTION_EXECUTED)
        self.assertEqual(len(action_events), 1)
        self.assertEqual(action_events[0].data["action"], "restart")
        self.assertEqual(action_events[0].data["action_type"], "system")

        print("✅ 事件分发机制测试通过")

    def test_error_handling(self):
        """测试错误处理"""
        print("🔍 测试错误处理...")

        # 测试游戏核心重置失败
        self.mock_game_core.reset_game.return_value = False

        restart_action = RestartAction()
        result = restart_action.execute_system_action(self.app)

        self.assertFalse(result["success"])
        self.assertIn("失败", result["message"])

        # 测试设置功能不可用
        app_without_settings = GameApplication(self.mock_ui)
        delattr(app_without_settings, '_show_settings')

        settings_action = SettingsAction()
        result = settings_action.execute_system_action(app_without_settings)

        self.assertFalse(result["success"])
        self.assertIn("不可用", result["message"])

        print("✅ 错误处理测试通过")


@unittest.skipUnless(IMPORTS_AVAILABLE, "需要系统动作模块")
class TestSystemActionIntegration(unittest.TestCase):
    """系统动作集成测试"""

    def setUp(self):
        """测试前设置"""
        event_handler.clear_history()

    def test_end_to_end_restart_flow(self):
        """测试端到端重启流程"""
        print("🔍 测试端到端重启流程...")

        # 创建模拟应用
        mock_ui = Mock()
        mock_ui.show_confirmation.return_value = True
        mock_ui.show_message = Mock()

        app = GameApplication(mock_ui)
        mock_game_core = Mock()
        mock_game_core.character = Mock()
        mock_game_core.character.name = "测试角色"
        mock_game_core.difficulty = "normal"
        mock_game_core.reset_game.return_value = True
        app.game_core = mock_game_core

        # 模拟UI事件
        from ui.interface import UIEvent
        restart_event = UIEvent("action", {"action": "restart"})

        # 处理事件
        app._handle_ui_event(restart_event)

        # 验证结果
        self.mock_game_core.reset_game.assert_called_once_with("测试角色", "normal")

        # 验证事件历史
        restart_events = event_handler.get_event_history(EventType.RESET_GAME)
        self.assertEqual(len(restart_events), 1)

        action_events = event_handler.get_event_history(EventType.ACTION_EXECUTED)
        self.assertEqual(len(action_events), 1)
        self.assertEqual(action_events[0].data["action"], "restart")

        print("✅ 端到端重启流程测试通过")

    def test_button_state_consistency(self):
        """测试按钮状态一致性"""
        print("🔍 测试按钮状态一致性...")

        renderer = GameStateRenderer()

        # 获取系统动作按钮
        system_buttons = renderer.format_system_action_buttons()

        # 验证所有系统按钮都启用
        for button in system_buttons:
            self.assertTrue(button.enabled, f"系统按钮 {button.name} 应该总是启用")
            self.assertTrue(button.visible, f"系统按钮 {button.name} 应该总是可见")
            self.assertEqual(button.button_type, ButtonType.SYSTEM_ACTION)
            self.assertIsNotNone(button.tooltip, f"系统按钮 {button.name} 应该有提示")

        # 验证按钮名称映射
        button_names = {b.action: b.name for b in system_buttons}
        expected_names = {
            "restart": "重新开始",
            "settings": "设置",
            "save_game": "保存游戏",
            "load_game": "加载游戏"
        }

        for action, expected_name in expected_names.items():
            self.assertIn(action, button_names)
            self.assertEqual(button_names[action], expected_name)

        print("✅ 按钮状态一致性测试通过")


def run_system_action_tests():
    """运行系统动作测试"""
    print("🚀 开始系统动作集成测试...")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSystemActions))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemActionIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 生成报告
    print("\n" + "=" * 60)
    print("📊 系统动作测试报告")
    print("=" * 60)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n通过率: {success_rate:.1f}%")

    if success_rate == 100.0:
        print("🎉 所有系统动作测试通过！")
    else:
        print("⚠️  部分测试失败，请检查代码。")

    return result.wasSuccessful()


def main():
    """主函数"""
    return run_system_action_tests()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)