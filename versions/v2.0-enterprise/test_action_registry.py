#!/usr/bin/env python3
"""
动作注册机制测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
            error_msg = f"{msg}: {item} 不在容器中"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def assert_is_not_none(self, value, msg=""):
        self.assertions += 1
        if value is None:
            error_msg = f"{msg}: 值不应为None"
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


def test_action_registry_basic():
    """测试动作注册机制基本功能"""
    test = SimpleTest("动作注册机制基本功能测试")

    try:
        from core.action_registry import ActionRegistry, ActionInfo
        from actions import MeditateAction

        # 创建注册中心
        registry = ActionRegistry()

        # 测试初始状态
        test.assert_equal(len(registry.get_all_action_ids()), 0, "初始状态下没有动作")
        test.assert_equal(len(registry.get_actions_by_category("game")), 0, "初始状态下游戏分类没有动作")

        # 注册一个动作
        success = registry.register_action(
            "test_meditate", MeditateAction,
            display_name="测试打坐",
            description="测试用的打坐动作",
            category="test",
            hotkey="T",
            sort_order=1
        )
        test.assert_true(success, "注册动作成功")

        # 验证动作已注册
        test.assert_equal(len(registry.get_all_action_ids()), 1, "注册后有1个动作")
        test.assert_in("test_meditate", registry.get_all_action_ids(), "动作ID在列表中")

        # 验证动作实例
        action = registry.get_action("test_meditate")
        test.assert_is_not_none(action, "可以获取动作实例")

        # 验证动作信息
        info = registry.get_action_info("test_meditate")
        test.assert_is_not_none(info, "可以获取动作信息")
        test.assert_equal(info.display_name, "测试打坐", "动作显示名称正确")
        test.assert_equal(info.category, "test", "动作分类正确")
        test.assert_equal(info.hotkey, "T", "快捷键正确")

        # 验证分类功能
        test_actions = registry.get_actions_by_category("test")
        test.assert_equal(len(test_actions), 1, "测试分类有1个动作")
        test.assert_in("test_meditate", test_actions, "动作在测试分类中")

        # 测试取消注册
        unregister_success = registry.unregister_action("test_meditate")
        test.assert_true(unregister_success, "取消注册成功")

        # 验证动作已移除
        test.assert_equal(len(registry.get_all_action_ids()), 0, "取消注册后没有动作")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_action_registry_advanced():
    """测试动作注册机制高级功能"""
    test = SimpleTest("动作注册机制高级功能测试")

    try:
        from core.action_registry import ActionRegistry
        from actions import MeditateAction, WaitAction

        registry = ActionRegistry()

        # 注册多个动作
        registry.register_action("meditate", MeditateAction, display_name="打坐", category="game", sort_order=2)
        registry.register_action("wait", WaitAction, display_name="等待", category="game", sort_order=1)
        registry.register_action("disabled_action", WaitAction, display_name="禁用动作", category="game", enabled=False)

        # 测试排序（只包括启用的动作）
        game_actions = registry.get_actions_by_category("game")
        test.assert_equal(len(game_actions), 2, "游戏分类有2个启用动作")
        test.assert_equal(game_actions[0], "wait", "按sort_order排序，wait在前")
        test.assert_equal(game_actions[1], "meditate", "按sort_order排序，meditate在后")

        # 测试启用/禁用
        test.assert_true(registry.is_action_enabled("meditate"), "meditate默认启用")
        test.assert_true(registry.is_action_enabled("wait"), "wait默认启用")
        test.assert_true(not registry.is_action_enabled("disabled_action"), "disabled_action默认禁用")

        # 禁用动作
        registry.disable_action("wait")
        test.assert_true(not registry.is_action_enabled("wait"), "wait已禁用")

        # 启用动作
        registry.enable_action("wait")
        test.assert_true(registry.is_action_enabled("wait"), "wait重新启用")

        # 测试搜索功能
        search_results = registry.search_actions("打坐")
        test.assert_in("meditate", search_results, "搜索功能找到meditate")

        # 测试统计信息
        stats = registry.get_registry_stats()
        test.assert_equal(stats["total_actions"], 3, "总动作数正确")
        test.assert_equal(stats["enabled_actions"], 2, "启用动作数正确")
        test.assert_equal(stats["disabled_actions"], 1, "禁用动作数正确")

        # 测试导出功能（只包括启用的动作）
        export_info = registry.export_registry_info()
        test.assert_in("game", export_info, "导出信息包含game分类")
        test.assert_equal(len(export_info["game"]), 2, "导出的game分类有2个启用动作")

        # 测试验证功能
        issues = registry.validate_registry()
        test.assert_equal(len(issues), 0, "注册中心验证通过，没有问题")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_game_actions_initialization():
    """测试游戏动作初始化"""
    test = SimpleTest("游戏动作初始化测试")

    try:
        from core.action_registry import action_registry, initialize_game_actions

        # 初始化游戏动作
        initialize_game_actions()

        # 验证动作数量
        game_actions = action_registry.get_actions_by_category("game")
        test.assert_equal(len(game_actions), 4, "初始化4个游戏动作")

        # 验证具体动作
        expected_actions = ["meditate", "consume_pill", "cultivate", "wait"]
        for action_id in expected_actions:
            test.assert_in(action_id, game_actions, f"包含动作 {action_id}")

            # 验证动作实例
            action = action_registry.get_action(action_id)
            test.assert_is_not_none(action, f"动作 {action_id} 实例存在")

            # 验证动作信息
            info = action_registry.get_action_info(action_id)
            test.assert_is_not_none(info, f"动作 {action_id} 信息存在")
            test.assert_equal(info.category, "game", f"动作 {action_id} 分类正确")
            test.assert_is_not_none(info.display_name, f"动作 {action_id} 有显示名称")
            test.assert_is_not_none(info.hotkey, f"动作 {action_id} 有快捷键")

        # 验证快捷键
        hotkeys = {}
        for action_id in game_actions:
            info = action_registry.get_action_info(action_id)
            if info.hotkey:
                hotkeys[info.hotkey] = action_id

        expected_hotkeys = {"1": "meditate", "2": "consume_pill", "3": "cultivate", "4": "wait"}
        for hotkey, expected_action in expected_hotkeys.items():
            test.assert_in(hotkey, hotkeys, f"快捷键 {hotkey} 存在")
            test.assert_equal(hotkeys[hotkey], expected_action, f"快捷键 {hotkey} 映射正确")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_action_execution():
    """测试动作执行"""
    test = SimpleTest("动作执行测试")

    try:
        from core.action_registry import action_registry, initialize_game_actions, execute_action_safely
        from models import CharacterStats, GameLog

        # 初始化动作
        initialize_game_actions()

        # 创建角色和日志
        character = CharacterStats("测试角色")
        game_log = GameLog()

        # 记录初始状态
        initial_hp = character.health.current_hp
        initial_mp = character.mana.current_mp
        initial_exp = character.experience.total_experience

        # 测试安全执行meditate
        result = execute_action_safely("meditate", character, game_log)
        test.assert_true(result["success"], "meditate执行成功")
        test.assert_in("effects", result, "返回结果包含effects")
        test.assert_in("costs", result, "返回结果包含costs")

        # 验证状态变化
        test.assert_true(character.health.current_hp < initial_hp, "HP减少")
        test.assert_true(character.mana.current_mp > initial_mp, "MP增加")
        test.assert_true(character.experience.total_experience > initial_exp, "经验增加")

        # 测试无效动作
        invalid_result = execute_action_safely("invalid_action", character, game_log)
        test.assert_true(not invalid_result["success"], "无效动作执行失败")
        test.assert_in("未找到动作", invalid_result["message"], "错误消息正确")

        # 测试禁用动作
        action_registry.disable_action("wait")
        disabled_result = execute_action_safely("wait", character, game_log)
        test.assert_true(not disabled_result["success"], "禁用动作执行失败")
        test.assert_in("动作已禁用", disabled_result["message"], "错误消息正确")

        # 重新启用
        action_registry.enable_action("wait")
        enabled_result = execute_action_safely("wait", character, game_log)
        test.assert_true(enabled_result["success"], "重新启用后动作执行成功")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def main():
    """主函数"""
    print("🔧 开始动作注册机制测试...")
    print("=" * 80)

    # 运行所有测试
    tests = [
        test_action_registry_basic,
        test_action_registry_advanced,
        test_game_actions_initialization,
        test_action_execution
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
        print("✅ 所有动作注册机制测试通过！")
        return 0
    else:
        print("❌ 部分动作注册机制测试失败。")
        return 1


if __name__ == "__main__":
    sys.exit(main())