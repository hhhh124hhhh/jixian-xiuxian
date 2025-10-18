"""
UI与逻辑交互集成测试
"""

import pytest
from unittest.mock import Mock, patch
from ui.interface import GameStateRenderer, CharacterDisplayInfo, ButtonState
from ui.layouts import default_layout
from ui.themes import theme_manager, font_manager
from models import CharacterStats, GameLog, RealmLevel


@pytest.mark.integration
@pytest.mark.ui
class TestGameStateRenderer:
    """游戏状态渲染器测试"""

    def test_format_character_info(self):
        """测试格式化角色信息"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")

        # 设置一些状态
        character.health.current_hp = 80
        character.mana.current_mp = 60
        character.talent.base_talent = 7
        character.experience.add_experience(25)
        character.inventory.add_item("pill", 3)
        character.meditation_streak = 5

        char_info = renderer.format_character_info(character)

        assert isinstance(char_info, CharacterDisplayInfo)
        assert char_info.name == "测试角色"
        assert char_info.talent == 7
        assert char_info.realm == "炼气期"
        assert char_info.hp == 80
        assert char_info.max_hp == 100
        assert char_info.mp == 60
        assert char_info.max_mp == 100
        assert char_info.pills == 3
        assert char_info.meditation_streak == 5
        assert char_info.hp_percentage == 0.8
        assert char_info.mp_percentage == 0.6

    def test_format_character_info_different_realms(self):
        """测试不同境界的角色信息格式化"""
        renderer = GameStateRenderer()
        character = CharacterStats("高境界角色")

        # 设置为高境界
        character.experience.total_experience = 500
        character.experience.current_level_experience = 100
        character.experience.current_realm = RealmLevel.CORE_FORMATION

        char_info = renderer.format_character_info(character)

        assert char_info.realm == "结丹期"
        assert char_info.exp == 100
        # 注意：阈值计算需要根据实际实现调整

    def test_format_action_buttons(self):
        """测试格式化操作按钮"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")
        actions = []  # 空动作列表用于测试

        buttons = renderer.format_action_buttons(character, actions)

        assert isinstance(buttons, list)
        # 空动作列表应该返回空按钮列表
        assert len(buttons) == 0

    def test_format_action_buttons_with_actions(self):
        """测试有动作时的按钮格式化"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")

        # 创建模拟动作
        mock_action = Mock()
        mock_action.name = "测试动作"
        mock_action.can_execute.return_value = True
        mock_action.description = "测试描述"

        actions = [mock_action]
        buttons = renderer.format_action_buttons(character, actions)

        assert len(buttons) == 1
        assert isinstance(buttons[0], ButtonState)
        assert buttons[0].name == "测试动作"
        assert buttons[0].enabled is True
        assert buttons[0].visible is True

    def test_format_action_buttons_disabled(self):
        """测试禁用状态的按钮格式化"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")

        # 创建不能执行的动作
        mock_action = Mock()
        mock_action.name = "禁用动作"
        mock_action.can_execute.return_value = False
        mock_action.description = "无法执行"

        actions = [mock_action]
        buttons = renderer.format_action_buttons(character, actions)

        assert len(buttons) == 1
        assert buttons[0].enabled is False
        assert buttons[0].tooltip == "无法执行"

    def test_format_game_log(self):
        """测试格式化游戏日志"""
        renderer = GameStateRenderer()
        log_entries = [
            "第一条日志",
            "第二条日志",
            "第三条日志"
        ]

        formatted = renderer.format_game_log(log_entries, max_entries=2)

        assert len(formatted) == 2
        assert formatted[0] == "> 第二条日志"
        assert formatted[1] == "> 第三条日志"

    def test_format_game_log_empty(self):
        """测试空日志格式化"""
        renderer = GameStateRenderer()

        formatted = renderer.format_game_log([])

        assert len(formatted) == 1
        assert formatted[0] == "> 开始你的修仙之旅..."

    def test_format_status_recommendation(self):
        """测试状态推荐格式化"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")

        recommendation = renderer.format_status_recommendation(character)

        assert isinstance(recommendation, str)
        assert len(recommendation) > 0

    def test_format_progress_bar(self):
        """测试进度条格式化"""
        renderer = GameStateRenderer()

        # 测试不同进度
        bar_0 = renderer.format_progress_bar(0, 100, 10)
        assert bar_0 == "░" * 10

        bar_50 = renderer.format_progress_bar(50, 100, 10)
        assert bar_50 == "█████" + "░" * 5

        bar_100 = renderer.format_progress_bar(100, 100, 10)
        assert bar_100 == "█" * 10

    def test_format_exp_display(self):
        """测试经验显示格式化"""
        renderer = GameStateRenderer()
        character = CharacterStats("测试角色")
        character.experience.add_experience(30)

        exp_display = renderer.format_exp_display(character)

        assert isinstance(exp_display, str)
        assert "/" in exp_display  # 应该包含当前/最大格式


@pytest.mark.integration
@pytest.mark.ui
class TestUILayoutIntegration:
    """UI布局集成测试"""

    def test_layout_dimensions(self):
        """测试布局尺寸"""
        layout = default_layout

        assert layout.SCREEN_WIDTH == 800
        assert layout.SCREEN_HEIGHT == 600
        assert layout.HEADER_HEIGHT == 50
        assert layout.INFO_HEIGHT == 120
        assert layout.BUTTON_HEIGHT == 100
        assert layout.LOG_HEIGHT == 320
        assert layout.STATUS_HEIGHT == 40

    def test_layout_rects(self):
        """测试布局矩形区域"""
        layout = default_layout

        # 检查各个区域是否正确定义
        assert layout.HEADER_RECT.width > 0
        assert layout.HEADER_RECT.height > 0
        assert layout.INFO_RECT.width > 0
        assert layout.INFO_RECT.height > 0
        assert layout.BUTTON_AREA_RECT.width > 0
        assert layout.BUTTON_AREA_RECT.height > 0
        assert layout.LOG_RECT.width > 0
        assert layout.LOG_RECT.height > 0
        assert layout.STATUS_RECT.width > 0
        assert layout.STATUS_RECT.height > 0

        # 检查区域是否不重叠
        assert layout.HEADER_RECT.bottom < layout.INFO_RECT.top
        assert layout.INFO_RECT.bottom < layout.BUTTON_AREA_RECT.top
        assert layout.BUTTON_AREA_RECT.bottom < layout.LOG_RECT.top
        assert layout.LOG_RECT.bottom < layout.STATUS_RECT.top

    def test_action_buttons_layout(self):
        """测试操作按钮布局"""
        layout = default_layout
        buttons = layout.ACTION_BUTTONS

        assert len(buttons) == 4

        for button in buttons:
            assert "name" in button
            assert "action" in button
            assert "rect" in button
            assert "description" in button

            # 检查按钮尺寸
            assert button["rect"].width > 0
            assert button["rect"].height > 0

        # 检查按钮名称
        button_names = [btn["name"] for btn in buttons]
        assert "打坐" in button_names
        assert "吃丹药" in button_names
        assert "修炼" in button_names
        assert "等待" in button_names

    def test_status_buttons_layout(self):
        """测试状态栏按钮布局"""
        layout = default_layout
        buttons = layout.STATUS_BUTTONS

        assert len(buttons) == 2

        for button in buttons:
            assert "name" in button
            assert "action" in button
            assert "rect" in button

            # 检查按钮是否在状态栏内
            assert layout.STATUS_RECT.collidepoint(button["rect"].center)

    def test_character_info_layout(self):
        """测试角色信息布局"""
        layout = default_layout
        info_lines = layout.CHARACTER_INFO_LINES

        assert "name_line" in info_lines
        assert "hp_line" in info_lines
        assert "mp_line" in info_lines
        assert "stats_line" in info_lines

        for line_name, line_config in info_lines.items():
            assert "pos" in line_config
            assert "template" in line_config

            # 检查位置是否在信息区域内
            pos = line_config["pos"]
            assert layout.INFO_RECT.collidepoint(pos)

    def test_log_config(self):
        """测试日志配置"""
        layout = default_layout
        log_config = layout.LOG_CONFIG

        assert "max_entries" in log_config
        assert "line_height" in log_config
        assert "start_pos" in log_config
        assert "max_width" in log_config

        assert log_config["max_entries"] > 0
        assert log_config["line_height"] > 0
        assert log_config["max_width"] > 0

        # 检查起始位置是否在日志区域内
        start_pos = log_config["start_pos"]
        assert layout.LOG_RECT.collidepoint(start_pos)

    def test_progress_bar_calculation(self):
        """测试进度条计算"""
        layout = default_layout

        # 测试不同百分比的宽度计算
        width_0 = layout.get_progress_bar_width(0, 100, 200)
        assert width_0 == 0

        width_50 = layout.get_progress_bar_width(50, 100, 200)
        assert width_50 == 100

        width_100 = layout.get_progress_bar_width(100, 100, 200)
        assert width_100 == 200

        # 测试边界情况
        width_negative = layout.get_progress_bar_width(-10, 100, 200)
        assert width_negative == 0

        width_over = layout.get_progress_bar_width(150, 100, 200)
        assert width_over == 200

    def test_progress_bar_blocks(self):
        """测试进度条块计算"""
        layout = default_layout

        # 测试不同百分比的块数
        blocks_0 = layout.get_progress_bar_blocks(0, 100, 10)
        assert blocks_0 == "░" * 10

        blocks_50 = layout.get_progress_bar_blocks(50, 100, 10)
        assert blocks_50 == "█████" + "░" * 5

        blocks_100 = layout.get_progress_bar_blocks(100, 100, 10)
        assert blocks_100 == "█" * 10


@pytest.mark.integration
@pytest.mark.ui
class TestThemeIntegration:
    """主题系统集成测试"""

    def test_theme_colors(self):
        """测试主题颜色"""
        theme = theme_manager.get_theme()

        # 检查基础颜色
        assert hasattr(theme, 'BACKGROUND')
        assert hasattr(theme, 'PANEL_BACKGROUND')
        assert hasattr(theme, 'BORDER')
        assert hasattr(theme, 'TEXT_PRIMARY')

        # 检查状态颜色
        assert hasattr(theme, 'HP_COLOR')
        assert hasattr(theme, 'MP_COLOR')
        assert hasattr(theme, 'EXP_COLOR')

        # 检查按钮颜色
        assert hasattr(theme, 'BUTTON_NORMAL')
        assert hasattr(theme, 'BUTTON_HOVER')
        assert hasattr(theme, 'BUTTON_DISABLED')

        # 颜色应该是RGB元组
        assert isinstance(theme.HP_COLOR, tuple)
        assert len(theme.HP_COLOR) == 3
        assert all(0 <= c <= 255 for c in theme.HP_COLOR)

    def test_hp_color_by_percentage(self):
        """测试根据生命值百分比获取颜色"""
        theme = theme_manager.get_theme()

        # 高生命值
        color_high = theme.get_hp_color(0.8)
        assert color_high == theme.HP_COLOR

        # 中等生命值
        color_medium = theme.get_hp_color(0.5)
        assert color_medium == (255, 193, 7)  # 黄色警告

        # 低生命值
        color_low = theme.get_hp_color(0.1)
        assert color_low == (200, 35, 51)  # 深红色危险

    def test_button_color_states(self):
        """测试按钮颜色状态"""
        theme = theme_manager.get_theme()

        # 正常状态
        normal_color = theme.get_button_color("打坐", "normal")
        assert normal_color == theme.ACTION_BUTTONS["打坐"]

        # 悬停状态
        hover_color = theme.get_button_color("打坐", "hover")
        assert hover_color != normal_color
        # 悬停颜色应该更亮
        assert hover_color[0] >= normal_color[0]

        # 按下状态
        pressed_color = theme.get_button_color("打坐", "pressed")
        assert pressed_color != normal_color
        # 按下颜色应该更暗
        assert pressed_color[0] <= normal_color[0]

        # 禁用状态
        disabled_color = theme.get_button_color("打坐", "disabled")
        assert disabled_color == theme.BUTTON_DISABLED

    def test_theme_switching(self):
        """测试主题切换"""
        # 获取默认主题
        default_theme = theme_manager.get_theme()
        initial_theme = theme_manager.current_theme

        # 切换到深色主题
        theme_manager.set_theme("dark")
        dark_theme = theme_manager.get_theme()

        assert theme_manager.current_theme == "dark"
        assert dark_theme.BACKGROUND != default_theme.BACKGROUND

        # 切换回默认主题
        theme_manager.set_theme("default")
        restored_theme = theme_manager.get_theme()

        assert theme_manager.current_theme == "default"
        assert restored_theme.BACKGROUND == default_theme.BACKGROUND

    def test_available_themes(self):
        """测试可用主题列表"""
        themes = theme_manager.get_available_themes()

        assert isinstance(themes, list)
        assert len(themes) >= 1
        assert "default" in themes

    def test_gradient_colors(self):
        """测试渐变颜色"""
        theme = theme_manager.get_theme()

        # 测试渐变
        start_color = (255, 0, 0)
        end_color = (0, 255, 0)

        # 开始位置
        color_start = theme.get_gradient_color(start_color, end_color, 0.0)
        assert color_start == start_color

        # 结束位置
        color_end = theme.get_gradient_color(start_color, end_color, 1.0)
        assert color_end == end_color

        # 中间位置
        color_middle = theme.get_gradient_color(start_color, end_color, 0.5)
        assert color_middle == (127, 127, 127)  # 中间色

        # 边界情况
        color_negative = theme.get_gradient_color(start_color, end_color, -0.5)
        assert color_negative == start_color

        color_over = theme.get_gradient_color(start_color, end_color, 1.5)
        assert color_over == end_color


@pytest.mark.integration
@pytest.mark.ui
class TestFontIntegration:
    """字体系统集成测试"""

    def test_font_creation(self):
        """测试字体创建"""
        # 测试不同大小的字体
        small_font = font_manager.get_font("small")
        normal_font = font_manager.get_font("normal")
        large_font = font_manager.get_font("large")
        title_font = font_manager.get_font("title")

        assert small_font is not None
        assert normal_font is not None
        assert large_font is not None
        assert title_font is not None

        # 检查字体大小递增
        theme = theme_manager.get_theme()
        assert small_font.get_height() <= normal_font.get_height()
        assert normal_font.get_height() <= large_font.get_height()
        assert large_font.get_height() <= title_font.get_height()

    def test_font_with_custom_size(self):
        """测试自定义大小字体"""
        custom_font = font_manager.get_font_with_size(24)
        assert custom_font is not None

        # 相同大小应该返回相同的字体实例
        custom_font2 = font_manager.get_font_with_size(24)
        assert custom_font is custom_font2

    def test_font_caching(self):
        """测试字体缓存"""
        # 第一次获取
        font1 = font_manager.get_font("normal")

        # 第二次获取应该返回相同的实例
        font2 = font_manager.get_font("normal")
        assert font1 is font2

        # 不同大小的字体应该不同
        font3 = font_manager.get_font_with_size(20)
        assert font1 is not font3

    @patch('pygame.font.SysFont')
    def test_font_fallback(self, mock_sysfont):
        """测试字体回退机制"""
        # 模拟字体加载失败
        mock_sysfont.side_effect = Exception("Font not found")

        # 应该回退到默认字体
        fallback_font = font_manager.get_font("normal")
        assert fallback_font is not None

        # 验证使用了默认字体
        mock_sysfont.assert_called_with("simhei", 16)
        mock_sysfont.assert_called_with(None, 16)  # 第二次调用使用默认字体


@pytest.mark.integration
@pytest.mark.ui
class TestUIComponentInteraction:
    """UI组件交互测试"""

    def test_button_state_properties(self):
        """测试按钮状态属性"""
        button = ButtonState(
            name="测试按钮",
            action="test_action",
            enabled=True,
            visible=True,
            tooltip="测试提示"
        )

        assert button.name == "测试按钮"
        assert button.action == "test_action"
        assert button.enabled is True
        assert button.visible is True
        assert button.tooltip == "测试提示"

    def test_character_display_info_properties(self):
        """测试角色显示信息属性"""
        char_info = CharacterDisplayInfo(
            name="测试角色",
            talent=7,
            realm="炼气期",
            exp=25,
            exp_threshold=100,
            hp=80,
            max_hp=100,
            mp=60,
            max_mp=100,
            pills=3,
            meditation_streak=5,
            hp_percentage=0.8,
            mp_percentage=0.6
        )

        assert char_info.name == "测试角色"
        assert char_info.talent == 7
        assert char_info.hp_percentage == 0.8
        assert char_info.mp_percentage == 0.6

    def test_ui_data_flow(self):
        """测试UI数据流"""
        # 创建角色
        character = CharacterStats("数据流测试")
        character.health.current_hp = 75
        character.mana.current_mp = 55
        character.talent.base_talent = 6

        # 创建日志
        game_log = GameLog()
        game_log.add_entry("测试日志条目")

        # 创建渲染器
        renderer = GameStateRenderer()

        # 格式化数据
        char_info = renderer.format_character_info(character)
        log_entries = renderer.format_game_log(game_log.get_recent_entries())
        recommendation = renderer.format_status_recommendation(character)

        # 验证数据流
        assert char_info.hp == 75
        assert char_info.mp == 55
        assert len(log_entries) >= 1
        assert isinstance(recommendation, str)

        # 模拟UI更新数据
        character.health.current_hp = 50
        new_char_info = renderer.format_character_info(character)
        assert new_char_info.hp == 50
        assert new_char_info.hp_percentage == 0.5