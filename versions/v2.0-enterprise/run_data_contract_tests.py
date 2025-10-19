#!/usr/bin/env python3
"""
数据契约测试运行器
不依赖pytest，独立运行数据契约测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SimpleTest:
    """简单测试框架"""
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

    def assert_is_instance(self, value, expected_type, msg=""):
        self.assertions += 1
        if not isinstance(value, expected_type):
            error_msg = f"{msg}: 期望类型 {expected_type}, 实际类型 {type(value)}"
            self.failures.append(error_msg)
            print(f"❌ {self.test_name}: {error_msg}")
        else:
            print(f"✅ {self.test_name}: {msg or 'Assertion passed'}")

    def assert_between(self, value, min_val, max_val, msg=""):
        self.assertions += 1
        if not (min_val <= value <= max_val):
            error_msg = f"{msg}: 值 {value} 不在范围 [{min_val}, {max_val}] 内"
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


def test_character_status_fields():
    """测试角色状态字段的一致性"""
    test = SimpleTest("角色状态字段一致性测试")

    try:
        from models import CharacterStats

        # 创建角色
        character = CharacterStats("契约测试角色")

        # 设置不同的状态值
        character.health.current_hp = 75
        character.mana.current_mp = 45
        character.talent.base_talent = 8
        character.experience.add_experience(30)
        character.inventory.add_item("pill", 5)
        character.meditation_streak = 3

        # 获取状态摘要
        status = character.get_status_summary()

        # 验证必需字段存在
        required_fields = [
            'name', 'hp', 'max_hp', 'mp', 'max_mp',
            'realm', 'exp', 'exp_progress', 'talent',
            'pills', 'meditation_streak', 'total_actions',
            'total_exp', 'alive'
        ]

        for field in required_fields:
            test.assert_in(field, status, f"必需字段 {field} 存在")
            test.assert_is_not_none(status[field], f"字段 {field} 值不为None")

        # 验证特定字段的类型
        test.assert_is_instance(status['name'], str, "name字段类型正确")
        test.assert_is_instance(status['hp'], int, "hp字段类型正确")
        test.assert_is_instance(status['talent'], int, "talent字段类型正确")
        test.assert_is_instance(status['exp_progress'], (int, float), "exp_progress字段类型正确")

        # 验证逻辑关系
        test.assert_true(status['hp'] <= status['max_hp'], "hp不超过max_hp")
        test.assert_true(status['mp'] <= status['max_mp'], "mp不超过max_mp")
        test.assert_between(status['exp_progress'], 0.0, 100.0, "exp_progress在0-100范围内")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_ui_character_display_info_contract():
    """测试UI角色显示信息的数据契约"""
    test = SimpleTest("UI角色显示信息契约测试")

    try:
        from ui.interface import GameStateRenderer
        from models import CharacterStats

        renderer = GameStateRenderer()
        character = CharacterStats("UI契约测试")

        # 设置状态
        character.health.current_hp = 85
        character.mana.current_mp = 70
        character.talent.base_talent = 6
        character.inventory.add_item("pill", 2)
        character.meditation_streak = 4

        # 获取格式化信息
        char_info = renderer.format_character_info(character)

        # 验证CharacterDisplayInfo契约
        from ui.interface import CharacterDisplayInfo
        test.assert_is_instance(char_info, CharacterDisplayInfo, "返回CharacterDisplayInfo实例")

        required_fields = [
            'name', 'talent', 'realm', 'exp', 'exp_threshold',
            'hp', 'max_hp', 'mp', 'max_mp', 'pills',
            'meditation_streak', 'hp_percentage', 'mp_percentage', 'exp_percentage'
        ]

        for field in required_fields:
            test.assert_true(hasattr(char_info, field), f"CharacterDisplayInfo有字段 {field}")
            value = getattr(char_info, field)
            test.assert_is_not_none(value, f"字段 {field} 值不为None")

        # 验证数据类型
        test.assert_is_instance(char_info.name, str, "name字段类型")
        test.assert_is_instance(char_info.talent, int, "talent字段类型")
        test.assert_is_instance(char_info.realm, str, "realm字段类型")
        test.assert_is_instance(char_info.exp, int, "exp字段类型")
        test.assert_is_instance(char_info.exp_threshold, int, "exp_threshold字段类型")

        # 验证百分比值
        test.assert_between(char_info.hp_percentage, 0.0, 1.0, "hp_percentage在0-1范围内")
        test.assert_between(char_info.mp_percentage, 0.0, 1.0, "mp_percentage在0-1范围内")
        test.assert_between(char_info.exp_percentage, 0.0, 1.0, "exp_percentage在0-1范围内")

        # 验证关键数据一致性
        test.assert_equal(char_info.name, "UI契约测试", "角色名称一致")
        test.assert_equal(char_info.hp, 85, "hp值一致")
        test.assert_equal(char_info.mp, 70, "mp值一致")
        test.assert_equal(char_info.pills, 2, "pills数量一致")
        test.assert_equal(char_info.meditation_streak, 4, "打坐连续数一致")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_exp_threshold_data_flow():
    """测试exp_threshold数据流的一致性"""
    test = SimpleTest("exp_threshold数据流测试")

    try:
        from ui.interface import GameStateRenderer
        from models import CharacterStats, RealmLevel

        renderer = GameStateRenderer()

        # 测试不同境界的exp_threshold
        test_cases = [
            (RealmLevel.QI_REFINING, 100),
            (RealmLevel.FOUNDATION, 200),
            (RealmLevel.CORE_FORMATION, 400),
            (RealmLevel.NASCENT_SOUL, 800),
            (RealmLevel.SPIRITUAL_TRANSFORMATION, 1600)
        ]

        for realm_level, expected_threshold in test_cases:
            character = CharacterStats(f"测试_{realm_level.value}")
            character.experience.current_realm = realm_level
            character.experience.current_level_experience = 50

            # 获取格式化信息
            char_info = renderer.format_character_info(character)

            # 验证exp_threshold正确性
            test.assert_equal(
                char_info.exp_threshold,
                expected_threshold,
                f"境界 {realm_level.value} 的exp_threshold正确"
            )

            # 验证境界名称一致性
            test.assert_equal(char_info.realm, realm_level.value, f"境界名称 {realm_level.value} 一致")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_template_formatting_contract():
    """测试模板格式化的数据契约"""
    test = SimpleTest("模板格式化契约测试")

    try:
        from ui.interface import GameStateRenderer
        from ui.layouts import default_layout
        from models import CharacterStats

        character = CharacterStats("模板测试角色")
        character.health.current_hp = 60
        character.mana.current_mp = 80
        character.talent.base_talent = 9
        character.inventory.add_item("pill", 1)

        # 获取角色信息
        renderer = GameStateRenderer()
        char_info = renderer.format_character_info(character)

        # 测试角色信息模板
        info_config = default_layout.CHARACTER_INFO_LINES
        name_template = info_config["name_line"]["template"]

        # 验证模板可以正确格式化
        try:
            formatted_name = name_template.format(
                name=char_info.name,
                talent=char_info.talent,
                realm=char_info.realm,
                exp=char_info.exp,
                exp_threshold=char_info.exp_threshold
            )
            test.assert_is_instance(formatted_name, str, "模板格式化结果为字符串")
            test.assert_true(len(formatted_name) > 0, "模板格式化结果非空")
        except KeyError as e:
            test.failures.append(f"模板格式化失败，缺少字段: {e}")
            print(f"❌ 模板格式化失败，缺少字段: {e}")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def test_game_core_state_contract():
    """测试游戏核心状态的数据契约"""
    test = SimpleTest("游戏核心状态契约测试")

    try:
        from core.game_core import GameCore

        game_core = GameCore()
        init_success = game_core.initialize_game("状态契约测试", "normal")
        test.assert_true(init_success, "游戏初始化成功")

        # 获取游戏状态
        game_state = game_core.get_game_state()

        # 验证游戏状态必需字段
        required_state_fields = [
            'character', 'game_log', 'actions', 'is_game_over',
            'difficulty', 'power_level', 'recommendation'
        ]

        for field in required_state_fields:
            test.assert_in(field, game_state, f"游戏状态包含字段 {field}")
            test.assert_is_not_none(game_state[field], f"游戏状态字段 {field} 不为None")

        # 验证角色状态契约
        character = game_state['character']
        test.assert_true(hasattr(character, 'get_status_summary'), "角色有get_status_summary方法")

        status = character.get_status_summary()
        test.assert_is_instance(status, dict, "角色状态为字典")
        test.assert_true(len(status) > 0, "角色状态非空")

    except Exception as e:
        test.failures.append(f"测试执行异常: {e}")
        print(f"❌ 测试执行异常: {e}")

    return test.finish()


def main():
    """主函数"""
    print("🧪 开始数据契约集成测试...")
    print("=" * 80)

    # 运行所有测试
    tests = [
        test_character_status_fields,
        test_ui_character_display_info_contract,
        test_exp_threshold_data_flow,
        test_template_formatting_contract,
        test_game_core_state_contract
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
        print("✅ 所有数据契约测试通过！")
        return 0
    else:
        print("❌ 部分数据契约测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())