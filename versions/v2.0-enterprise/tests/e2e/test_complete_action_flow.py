#!/usr/bin/env python3
"""
完整动作流端到端测试
测试从UI交互到动作执行的完整流程
"""

import sys
import os
import time
import pygame
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 简单测试框架
class SimpleTest:
    def __init__(self, test_name):
        self.test_name = test_name
        self.assertions = 0
        self.failures = []

    def assert_equal(self, actual, expected, msg=""):
        self.assertions += 1
        if actual != expected:
            error_msg = f"{msg}: 期望 {expected}, 实际 {actual}"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def assert_true(self, condition, msg=""):
        self.assertions += 1
        if not condition:
            error_msg = f"{msg}: 断言失败"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def assert_in(self, item, container, msg=""):
        self.assertions += 1
        if item not in container:
            error_msg = f"{msg}: {item} 不在 {container} 中"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def assert_greater(self, value, min_val, msg=""):
        self.assertions += 1
        if not value > min_val:
            error_msg = f"{msg}: {value} 不大于 {min_val}"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def finish(self):
        if self.failures:
            print(f"\n❌ {self.test_name} 失败: {len(self.failures)}/{self.assertions} 断言失败")
            for failure in self.failures:
                print(f"   - {failure}")
            return False
        else:
            print(f"✅ {self.test_name} 成功: {self.assertions} 个断言全部通过")
            return True


def test_ui_action_name_consistency():
    """测试UI层动作名称与后端动作定义的一致性"""
    test = SimpleTest("UI动作名称一致性测试")

    try:
        from ui.layouts import default_layout
        from ui.pygame_renderer import PygameInputHandler
        from actions import ActionFactory

        # 获取UI层定义的游戏动作名称（排除settings和restart）
        ui_actions = set()
        for button in default_layout.ACTION_BUTTONS:
            if button["action"] in ["meditate", "consume_pill", "cultivate", "wait"]:
                ui_actions.add(button["action"])

        # 获取快捷键映射的游戏动作名称
        renderer = PygameInputHandler(default_layout)
        shortcut_actions = set(renderer.shortcuts.values())
        # 只保留游戏动作，排除系统动作
        game_actions = {"meditate", "consume_pill", "cultivate", "wait"}
        shortcut_actions = shortcut_actions & game_actions

        # 获取后端定义的动作名称
        backend_actions = set()
        for action in ActionFactory.get_all_actions():
            backend_actions.add(action.name)

        # 验证一致性
        test.assert_equal(len(ui_actions), 4, "UI层定义4个游戏动作")
        test.assert_equal(len(shortcut_actions), 4, "快捷键映射4个游戏动作")
        test.assert_equal(len(backend_actions), 4, "后端定义4个游戏动作")

        # 验证动作名称完全匹配
        expected_actions = {"meditate", "consume_pill", "cultivate", "wait"}
        test.assert_equal(ui_actions, expected_actions, "UI层动作名称正确")
        test.assert_equal(shortcut_actions, expected_actions, "快捷键动作名称正确")
        test.assert_equal(backend_actions, expected_actions, "后端动作名称正确")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_action_execution_flow():
    """测试动作执行的完整流程"""
    test = SimpleTest("动作执行流程测试")

    try:
        from core.game_core import GameCore
        from application import GameApplication

        # 创建游戏核心
        game_core = GameCore()
        init_success = game_core.initialize_game("流程测试角色")
        test.assert_true(init_success, "游戏初始化成功")

        # 记录初始状态
        initial_hp = game_core.character.health.current_hp
        initial_mp = game_core.character.mana.current_mp
        initial_exp = game_core.character.experience.total_experience
        initial_actions = game_core.character.total_actions

        # 测试每个动作的执行流程
        actions_to_test = [
            ("meditate", "打坐动作"),
            ("wait", "等待动作"),
            ("cultivate", "修炼动作"),
        ]

        for action_name, action_desc in actions_to_test:
            print(f"\n🔍 测试 {action_desc} ({action_name})")

            # 执行动作前状态
            before_hp = game_core.character.health.current_hp
            before_mp = game_core.character.mana.current_mp
            before_exp = game_core.character.experience.total_experience
            before_actions = game_core.character.total_actions

            # 执行动作
            result = game_core.execute_action(action_name)
            test.assert_true(result["success"], f"{action_desc}执行成功")

            # 验证动作效果
            test.assert_in("effects", result, f"{action_desc}有效果字段")
            test.assert_in("costs", result, f"{action_desc}有消耗字段")

            # 验证状态确实发生了变化
            after_hp = game_core.character.health.current_hp
            after_mp = game_core.character.mana.current_mp
            after_exp = game_core.character.experience.total_experience
            after_actions = game_core.character.total_actions

            # 动作计数应该增加
            test.assert_equal(after_actions, before_actions + 1, f"{action_desc}增加动作计数")

            # 验证日志记录
            if game_core.game_log:
                recent_entries = game_core.game_log.get_recent_entries(3)
                test.assert_true(len(recent_entries) > 0, f"{action_desc}记录了日志")

        # 给角色添加丹药，测试吃丹药动作
        game_core.character.inventory.add_item("pill", 1)
        before_pills = game_core.character.inventory.get_item_count("pill")

        pill_result = game_core.execute_action("consume_pill")
        test.assert_true(pill_result["success"], "吃丹药动作执行成功")

        after_pills = game_core.character.inventory.get_item_count("pill")
        test.assert_equal(after_pills, before_pills - 1, "吃丹药减少丹药数量")

        # 验证最终状态与初始状态不同
        final_hp = game_core.character.health.current_hp
        final_mp = game_core.character.mana.current_mp
        final_exp = game_core.character.experience.total_experience
        final_actions = game_core.character.total_actions

        test.assert_greater(final_exp, initial_exp, "总经验值增加")
        test.assert_greater(final_actions, initial_actions, "总动作次数增加")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_game_state_consistency():
    """测试游戏状态的一致性"""
    test = SimpleTest("游戏状态一致性测试")

    try:
        from core.game_core import GameCore

        game_core = GameCore()
        game_core.initialize_game("状态测试角色")

        # 执行一系列动作
        action_sequence = ["meditate", "meditate", "wait", "cultivate"]

        for i, action in enumerate(action_sequence):
            result = game_core.execute_action(action)
            test.assert_true(result["success"], f"序列动作 {i+1} ({action}) 执行成功")

            # 获取游戏状态
            game_state = game_core.get_game_state()

            # 验证游戏状态的完整性
            required_fields = [
                'character', 'game_log', 'actions', 'is_game_over',
                'difficulty', 'power_level', 'recommendation'
            ]

            for field in required_fields:
                test.assert_in(field, game_state, f"游戏状态包含 {field}")

            # 验证角色状态可以获取摘要
            character = game_state['character']
            status = character.get_status_summary()
            test.assert_true(isinstance(status, dict), "角色状态为字典")
            test.assert_true(len(status) > 0, "角色状态非空")

            # 验证状态一致性
            test.assert_equal(
                status['total_actions'],
                i + 1,
                f"动作 {i+1} 后动作计数正确"
            )

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_keyboard_shortcut_integration():
    """测试键盘快捷键集成"""
    test = SimpleTest("键盘快捷键集成测试")

    try:
        from ui.pygame_renderer import PygameInputHandler
        from ui.layouts import default_layout
        from actions import ActionFactory

        renderer = PygameInputHandler(default_layout)

        # 测试所有快捷键映射
        expected_mappings = {
            'pygame.K_1': 'meditate',
            'pygame.K_2': 'consume_pill',
            'pygame.K_3': 'cultivate',
            'pygame.K_4': 'wait'
        }

        for key_str, expected_action in expected_mappings.items():
            # 获取对应的键码
            key_code = eval(key_str)
            actual_action = renderer.shortcuts.get(key_code)

            test.assert_equal(actual_action, expected_action, f"快捷键 {key_str} 映射正确")

            # 验证映射的动作在后端存在
            action = ActionFactory.get_action_by_name(actual_action)
            test.assert_true(action is not None, f"快捷键 {key_str} 对应的动作存在")

        # 测试无效快捷键
        invalid_action = renderer.handle_key_press(999)  # 不存在的键码
        test.assert_equal(invalid_action, None, "无效快捷键返回None")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_ui_button_integration():
    """测试UI按钮集成"""
    test = SimpleTest("UI按钮集成测试")

    try:
        from ui.layouts import default_layout
        from actions import ActionFactory

        # 测试所有动作按钮
        expected_buttons = [
            ("打坐", "meditate"),
            ("吃丹药", "consume_pill"),
            ("修炼", "cultivate"),
            ("等待", "wait")
        ]

        action_buttons = default_layout.ACTION_BUTTONS
        test.assert_equal(len(action_buttons), len(expected_buttons), "动作按钮数量正确")

        for i, (expected_name, expected_action) in enumerate(expected_buttons):
            if i < len(action_buttons):
                button = action_buttons[i]

                # 验证按钮名称
                test.assert_equal(button["name"], expected_name, f"按钮 {i} 名称正确")

                # 验证按钮动作
                test.assert_equal(button["action"], expected_action, f"按钮 {i} 动作正确")

                # 验证按钮有有效的矩形区域
                test.assert_true(hasattr(button["rect"], "x"), f"按钮 {i} 有有效的矩形区域")

                # 验证动作在后端存在
                action = ActionFactory.get_action_by_name(button["action"])
                test.assert_true(action is not None, f"按钮 {i} 对应的动作存在")

        # 测试点击检测（模拟点击）
        for button in action_buttons:
            # 点击按钮中心点
            click_x = button["rect"].x + button["rect"].width // 2
            click_y = button["rect"].y + button["rect"].height // 2

            # 这里我们只测试按钮配置，不测试实际的pygame点击处理
            test.assert_true(isinstance(click_x, int), "按钮点击坐标X为整数")
            test.assert_true(isinstance(click_y, int), "按钮点击坐标Y为整数")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_error_handling_integration():
    """测试错误处理的集成"""
    test = SimpleTest("错误处理集成测试")

    try:
        from core.game_core import GameCore

        game_core = GameCore()
        game_core.initialize_game("错误测试角色")

        # 测试无效动作名称
        invalid_result = game_core.execute_action("invalid_action")
        test.assert_true(not invalid_result["success"], "无效动作执行失败")
        test.assert_in("未找到动作", invalid_result["message"], "错误消息正确")

        # 测试资源不足的情况
        # 先消耗所有仙力
        while game_core.character.mana.current_mp >= 20:
            game_core.execute_action("cultivate")

        # 现在尝试修炼应该失败
        insufficient_mp_result = game_core.execute_action("cultivate")
        test.assert_true(not insufficient_mp_result["success"], "仙力不足时修炼失败")
        test.assert_in("仙力不足", insufficient_mp_result["message"], "错误消息提示仙力不足")

        # 测试没有丹药时吃丹药
        # 确保没有丹药
        current_pills = game_core.character.inventory.get_item_count("pill")
        if current_pills > 0:
            game_core.character.inventory.consume_item("pill", current_pills)

        no_pill_result = game_core.execute_action("consume_pill")
        test.assert_true(not no_pill_result["success"], "没有丹药时吃丹药失败")
        test.assert_in("没有丹药", no_pill_result["message"], "错误消息提示没有丹药")

        # 测试游戏结束后的动作
        # 强制角色死亡
        game_core.character.health.consume(game_core.character.health.current_hp)

        # 现在尝试任何动作都应该失败
        dead_result = game_core.execute_action("meditate")
        test.assert_true(not dead_result["success"], "角色死亡后动作失败")
        # 游戏结束的消息可能是"游戏已结束"或者来自动作本身
        game_over_messages = ["游戏已结束", "无法执行进入冥想状态，恢复仙力并获得少量经验"]
        test.assert_true(dead_result["message"] in game_over_messages, "错误消息提示游戏结束或无法执行")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def main():
    """主函数"""
    print("🚀 开始完整动作流端到端测试...")
    print("=" * 80)

    # 运行所有测试
    tests = [
        test_ui_action_name_consistency,
        test_action_execution_flow,
        test_game_state_consistency,
        test_keyboard_shortcut_integration,
        test_ui_button_integration,
        test_error_handling_integration
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        print(f"\n🔍 运行 {test_func.__name__}")
        print("-" * 60)

        if test_func():
            passed += 1

        print()

    print("=" * 80)
    print(f"📊 测试结果: {passed}/{total} 个测试通过")

    if passed == total:
        print("✅ 所有端到端测试通过！动作系统完全正常工作。")
        return 0
    else:
        print("❌ 部分端到端测试失败，需要进一步检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())