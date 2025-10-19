"""
数据契约集成测试
专门测试各层之间的数据契约一致性
"""

# 简单的测试框架，避免依赖pytest
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

    def finish(self):
        if self.failures:
            print(f"\n❌ {self.test_name} 失败: {len(self.failures)}/{self.assertions} 断言失败")
            for failure in self.failures:
                print(f"   - {failure}")
            return False
        else:
            print(f"✅ {self.test_name} 成功: {self.assertions} 个断言全部通过")
            return True
from ui.interface import GameStateRenderer, CharacterDisplayInfo, ButtonState
from ui.layouts import default_layout
from ui.themes import theme_manager, font_manager
from models import CharacterStats, GameLog, RealmLevel
from rules import game_rules
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.mark.integration
@pytest.mark.data_contract
class TestDataContractIntegration:
    """数据契约集成测试"""

    def test_character_status_fields_consistency(self):
        """测试角色状态字段的一致性"""
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
            assert field in status, f"缺失必需字段: {field}"
            assert status[field] is not None, f"字段 {field} 值为None"

    def test_ui_character_display_info_contract(self):
        """测试UI角色显示信息的数据契约"""
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
        assert isinstance(char_info, CharacterDisplayInfo)

        required_fields = [
            'name', 'talent', 'realm', 'exp', 'exp_threshold',
            'hp', 'max_hp', 'mp', 'max_mp', 'pills',
            'meditation_streak', 'hp_percentage', 'mp_percentage', 'exp_percentage'
        ]

        for field in required_fields:
            assert hasattr(char_info, field), f"CharacterDisplayInfo缺失字段: {field}"
            value = getattr(char_info, field)
            assert value is not None, f"字段 {field} 值为None"

        # 验证数据类型
        assert isinstance(char_info.name, str)
        assert isinstance(char_info.talent, int)
        assert isinstance(char_info.realm, str)
        assert isinstance(char_info.exp, int)
        assert isinstance(char_info.exp_threshold, int)
        assert isinstance(char_info.hp, int)
        assert isinstance(char_info.max_hp, int)
        assert isinstance(char_info.mp, int)
        assert isinstance(char_info.max_mp, int)
        assert isinstance(char_info.pills, int)
        assert isinstance(char_info.meditation_streak, int)

        # 验证百分比值
        assert 0 <= char_info.hp_percentage <= 1
        assert 0 <= char_info.mp_percentage <= 1
        assert 0 <= char_info.exp_percentage <= 1

    def test_exp_threshold_data_flow(self):
        """测试exp_threshold数据流的一致性"""
        character = CharacterStats("阈值测试角色")
        renderer = GameStateRenderer()

        # 测试不同境界的exp_threshold
        realms_to_test = [
            (RealmLevel.QI_REFINING, 100),
            (RealmLevel.FOUNDATION, 200),
            (RealmLevel.CORE_FORMATION, 400),
            (RealmLevel.NASCENT_SOUL, 800),
            (RealmLevel.SPIRITUAL_TRANSFORMATION, 1600)
        ]

        for realm_level, expected_threshold in realms_to_test:
            # 设置角色境界
            character.experience.current_realm = realm_level
            character.experience.current_level_experience = 50

            # 获取格式化信息
            char_info = renderer.format_character_info(character)

            # 验证exp_threshold正确性
            assert char_info.exp_threshold == expected_threshold, \
                f"境界 {realm_level.value} 的exp_threshold应为 {expected_threshold}，实际为 {char_info.exp_threshold}"

            # 验证境界名称一致性
            assert char_info.realm == realm_level.value

    def test_template_formatting_contract(self):
        """测试模板格式化的数据契约"""
        from ui.layouts import default_layout

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
            assert isinstance(formatted_name, str)
            assert len(formatted_name) > 0
        except KeyError as e:
            pytest.fail(f"模板格式化失败，缺少字段: {e}")

    def test_game_core_state_contract(self):
        """测试游戏核心状态的数据契约"""
        from core.game_core import GameCore

        game_core = GameCore()
        game_core.initialize_game("状态契约测试", "normal")

        # 获取游戏状态
        game_state = game_core.get_game_state()

        # 验证游戏状态必需字段
        required_state_fields = [
            'character', 'game_log', 'actions', 'is_game_over',
            'difficulty', 'power_level', 'recommendation'
        ]

        for field in required_state_fields:
            assert field in game_state, f"游戏状态缺失字段: {field}"
            assert game_state[field] is not None, f"游戏状态字段 {field} 值为None"

        # 验证角色状态契约
        character = game_state['character']
        assert hasattr(character, 'get_status_summary')

        status = character.get_status_summary()
        assert isinstance(status, dict)
        assert len(status) > 0

    def test_action_result_contract(self):
        """测试动作执行结果的数据契约"""
        from models import ActionResult, Cost

        # 测试ActionResult契约
        result = ActionResult(
            success=True,
            message="测试动作执行成功",
            effects={"exp_gain": 10, "hp_recovery": 5},
            costs={"mp": 20, "time": 1}
        )

        assert isinstance(result.success, bool)
        assert isinstance(result.message, str)
        assert isinstance(result.effects, dict)
        assert isinstance(result.costs, dict)

        # 测试Cost契约
        cost = Cost(hp=10, mp=20, pills=1, time=2)

        assert isinstance(cost.hp, int)
        assert isinstance(cost.mp, int)
        assert isinstance(cost.pills, int)
        assert isinstance(cost.time, int)

    def test_button_state_contract(self):
        """测试按钮状态的数据契约"""
        from ui.interface import ButtonState

        # 创建按钮状态
        button_state = ButtonState(
            text="测试按钮",
            enabled=True,
            visible=True,
            hotkey="1"
        )

        # 验证字段
        assert hasattr(button_state, 'text')
        assert hasattr(button_state, 'enabled')
        assert hasattr(button_state, 'visible')
        assert hasattr(button_state, 'hotkey')

        # 验证数据类型
        assert isinstance(button_state.text, str)
        assert isinstance(button_state.enabled, bool)
        assert isinstance(button_state.visible, bool)
        assert isinstance(button_state.hotkey, str)

    def test_error_handling_data_contract(self):
        """测试错误处理时的数据契约"""
        renderer = GameStateRenderer()

        # 创建死亡角色
        dead_character = CharacterStats("死亡测试角色")
        dead_character.health.current_hp = 0

        # 即使角色死亡，格式化也应该返回有效的CharacterDisplayInfo
        char_info = renderer.format_character_info(dead_character)

        assert isinstance(char_info, CharacterDisplayInfo)
        assert char_info.name == "死亡测试角色"
        assert char_info.hp == 0
        assert char_info.hp_percentage == 0.0

    def test_save_load_data_contract(self):
        """测试存档加载的数据契约"""
        from core.game_core import GameCore

        game_core = GameCore()
        game_core.initialize_game("存档契约测试", "normal")

        # 设置一些状态
        game_core.character.health.current_hp = 85
        game_core.character.mana.current_mp = 65
        game_core.character.inventory.add_item("pill", 3)

        # 保存游戏
        save_success = game_core.save_game(999)  # 使用特殊槽位避免覆盖
        assert save_success, "保存游戏应该成功"

        # 重新初始化
        new_game_core = GameCore()
        load_success = new_game_core.load_game(999)
        assert load_success, "加载游戏应该成功"

        # 验证加载后的状态
        assert new_game_core.character.name == "存档契约测试"
        assert new_game_core.character.health.current_hp == 85
        assert new_game_core.character.mana.current_mp == 65
        assert new_game_core.character.inventory.get_item_count("pill") == 3


@pytest.mark.integration
@pytest.mark.data_contract
class TestEventDataContract:
    """事件数据契约测试"""

    def test_event_data_structure(self):
        """测试事件数据结构的一致性"""
        from core.event_handler import GameEvent, EventType

        # 创建事件
        event = GameEvent(
            event_type=EventType.ACTION_EXECUTED,
            data={"action": "打坐", "success": True, "effects": {"exp_gain": 5}},
            timestamp=1234567890.0,
            source="test"
        )

        # 验证事件结构
        assert isinstance(event.event_type, EventType)
        assert isinstance(event.data, dict)
        assert isinstance(event.timestamp, float)
        assert isinstance(event.source, str)

        # 验证必需数据字段
        assert "action" in event.data
        assert "success" in event.data
        assert "effects" in event.data

    def test_character_state_in_events(self):
        """测试事件中角色状态的数据契约"""
        from core.game_core import GameCore
        from core.event_handler import event_handler, EventType

        # 监听事件
        received_events = []

        def event_listener(event):
            received_events.append(event)

        event_handler.register_listener(EventType.ACTION_EXECUTED, event_listener)

        try:
            # 执行动作
            game_core = GameCore()
            game_core.initialize_game("事件契约测试")
            result = game_core.execute_action("meditate")

            # 验证事件中的角色状态
            assert len(received_events) > 0

            for event in received_events:
                if "character_state" in event.data:
                    character_state = event.data["character_state"]
                    assert isinstance(character_state, dict)

                    # 验证角色状态必需字段
                    required_fields = ["name", "hp", "mp", "realm", "talent", "pills"]
                    for field in required_fields:
                        assert field in character_state, f"事件中的角色状态缺失字段: {field}"

        finally:
            # 清理
            event_handler.remove_all_listeners()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])