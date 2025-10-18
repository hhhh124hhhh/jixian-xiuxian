"""
Pygame界面渲染器 - 具体的UI实现
"""

import pygame
import sys
from typing import Dict, Any, Optional, List
from .interface import GameInterface, UIEvent, GameStateRenderer, InputHandler, UIComponent
from .layouts import default_layout
from .themes import theme_manager, font_manager


class PygameInputHandler(InputHandler):
    """Pygame输入处理器"""

    def __init__(self, layout):
        self.layout = layout
        self.shortcuts = {
            pygame.K_1: "meditate",
            pygame.K_2: "consume_pill",
            pygame.K_3: "cultivate",
            pygame.K_4: "wait",
            pygame.K_r: "restart",
            pygame.K_ESCAPE: "quit"
        }

    def handle_mouse_click(self, position: tuple) -> Optional[str]:
        """处理鼠标点击"""
        x, y = position

        # 检查动作按钮
        for button in self.layout.ACTION_BUTTONS:
            if button["rect"].collidepoint(x, y):
                return button["action"]

        # 检查状态栏按钮
        for button in self.layout.STATUS_BUTTONS:
            if button["rect"].collidepoint(x, y):
                return button["action"]

        return None

    def handle_key_press(self, key: int) -> Optional[str]:
        """处理键盘按键"""
        return self.shortcuts.get(key)

    def register_shortcut(self, key: int, action: str):
        """注册快捷键"""
        self.shortcuts[key] = action


class ProgressBar(UIComponent):
    """进度条组件"""

    def __init__(self, position: tuple, size: tuple,
                 current_value: int = 0, max_value: int = 100,
                 color=(0, 123, 255), bg_color=(200, 200, 200)):
        super().__init__(position, size)
        self.current_value = current_value
        self.max_value = max_value
        self.color = color
        self.bg_color = bg_color

    def update_values(self, current: int, maximum: int):
        """更新进度条数值"""
        self.current_value = current
        self.max_value = maximum

    def render(self, surface):
        """渲染进度条"""
        if not self.visible:
            return

        x, y, w, h = self.rect

        # 绘制背景
        pygame.draw.rect(surface, self.bg_color, (x, y, w, h))
        pygame.draw.rect(surface, (100, 100, 100), (x, y, w, h), 1)

        # 绘制进度
        if self.max_value > 0:
            progress_width = int((self.current_value / self.max_value) * w)
            progress_width = min(progress_width, w)
            if progress_width > 0:
                pygame.draw.rect(surface, self.color, (x, y, progress_width, h))

    def handle_event(self, event) -> bool:
        """进度条不处理事件"""
        return False


class Button(UIComponent):
    """按钮组件"""

    def __init__(self, position: tuple, size: tuple, text: str,
                 action: str, color=(0, 123, 255), text_color=(255, 255, 255)):
        super().__init__(position, size)
        self.text = text
        self.action = action
        self.color = color
        self.text_color = text_color
        self.hover_color = tuple(min(255, c + 20) for c in color)
        self.pressed_color = tuple(max(0, c - 20) for c in color)
        self.disabled_color = (200, 200, 200)
        self.is_hovered = False
        self.is_pressed = False
        self.on_click = None

    def render(self, surface):
        """渲染按钮"""
        if not self.visible:
            return

        x, y, w, h = self.rect
        theme = theme_manager.get_theme()

        # 选择颜色
        if not self.enabled:
            color = theme.BUTTON_DISABLED
            text_color = theme.TEXT_MUTED
        elif self.is_pressed:
            color = theme.get_button_color(self.text, "pressed")
            text_color = theme.BUTTON_TEXT
        elif self.is_hovered:
            color = theme.get_button_color(self.text, "hover")
            text_color = theme.BUTTON_TEXT
        else:
            color = theme.get_button_color(self.text)
            text_color = theme.BUTTON_TEXT

        # 绘制按钮背景
        pygame.draw.rect(surface, color, (x, y, w, h))
        pygame.draw.rect(surface, (100, 100, 100), (x, y, w, h), 2)

        # 绘制按钮文字
        font = font_manager.get_font("normal")
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + w // 2, y + h // 2))
        surface.blit(text_surface, text_rect)

    def handle_event(self, event) -> bool:
        """处理事件"""
        if not self.enabled or not self.visible:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.is_point_inside(event.pos)
            return self.is_hovered

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_point_inside(event.pos):
                self.is_pressed = True
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.is_point_inside(event.pos):
                self.is_pressed = False
                if self.on_click:
                    self.on_click(self.action)
                return True
            self.is_pressed = False

        return False


class Panel(UIComponent):
    """面板组件"""

    def __init__(self, position: tuple, size: tuple,
                 background_color=(255, 255, 255), border_color=(200, 200, 200)):
        super().__init__(position, size)
        self.background_color = background_color
        self.border_color = border_color
        self.components = []

    def add_component(self, component: UIComponent):
        """添加子组件"""
        component.parent = self
        self.components.append(component)

    def render(self, surface):
        """渲染面板"""
        if not self.visible:
            return

        x, y, w, h = self.rect

        # 绘制背景
        pygame.draw.rect(surface, self.background_color, (x, y, w, h))

        # 绘制边框
        pygame.draw.rect(surface, self.border_color, (x, y, w, h), 2)

        # 渲染子组件
        for component in self.components:
            component.render(surface)

    def handle_event(self, event) -> bool:
        """处理事件，传递给子组件"""
        if not self.enabled or not self.visible:
            return False

        # 反向遍历，让上层组件优先处理事件
        for component in reversed(self.components):
            if component.handle_event(event):
                return True

        return False


class PygameGameInterface(GameInterface):
    """Pygame游戏界面实现"""

    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.screen = None
        self.clock = None
        self.running = False
        self.layout = default_layout

        # 渲染器和输入处理器
        self.renderer = GameStateRenderer()
        self.input_handler = PygameInputHandler(self.layout)

        # UI组件
        self.buttons = []
        self.progress_bars = {}
        self.panels = {}

        # 事件回调
        self.on_action_selected = None
        self.on_restart_requested = None
        self.on_settings_requested = None

    def initialize(self) -> bool:
        """初始化Pygame界面"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("极简修仙 MVP")
            self.clock = pygame.time.Clock()
            self.running = True

            # 初始化UI组件
            self._init_ui_components()

            return True
        except Exception as e:
            print(f"初始化失败: {e}")
            return False

    def _init_ui_components(self):
        """初始化UI组件"""
        theme = theme_manager.get_theme()

        # 创建信息面板
        info_panel = Panel(
            (self.layout.INFO_RECT.x, self.layout.INFO_RECT.y),
            (self.layout.INFO_RECT.width, self.layout.INFO_RECT.height),
            theme.PANEL_BACKGROUND,
            theme.BORDER
        )
        self.panels["info"] = info_panel

        # 创建进度条
        self.progress_bars["hp"] = ProgressBar(
            (self.layout.CHARACTER_INFO_LINES["hp_line"]["bar_rect"].x,
             self.layout.CHARACTER_INFO_LINES["hp_line"]["bar_rect"].y),
            (self.layout.CHARACTER_INFO_LINES["hp_line"]["bar_rect"].width,
             self.layout.CHARACTER_INFO_LINES["hp_line"]["bar_rect"].height),
            color=theme.HP_COLOR,
            bg_color=theme.HP_BACKGROUND
        )

        self.progress_bars["mp"] = ProgressBar(
            (self.layout.CHARACTER_INFO_LINES["mp_line"]["bar_rect"].x,
             self.layout.CHARACTER_INFO_LINES["mp_line"]["bar_rect"].y),
            (self.layout.CHARACTER_INFO_LINES["mp_line"]["bar_rect"].width,
             self.layout.CHARACTER_INFO_LINES["mp_line"]["bar_rect"].height),
            color=theme.MP_COLOR,
            bg_color=theme.MP_BACKGROUND
        )

        # 创建操作按钮
        for button_config in self.layout.ACTION_BUTTONS:
            button = Button(
                (button_config["rect"].x, button_config["rect"].y),
                (button_config["rect"].width, button_config["rect"].height),
                button_config["name"],
                button_config["action"]
            )
            button.on_click = self._on_button_click
            self.buttons.append(button)

        # 创建状态栏按钮
        for button_config in self.layout.STATUS_BUTTONS:
            button = Button(
                (button_config["rect"].x, button_config["rect"].y),
                (button_config["rect"].width, button_config["rect"].height),
                button_config["name"],
                button_config["action"]
            )
            button.on_click = self._on_button_click
            self.buttons.append(button)

    def _on_button_click(self, action: str):
        """按钮点击回调"""
        if action == "restart":
            if self.on_restart_requested:
                self.on_restart_requested()
        elif action == "settings":
            if self.on_settings_requested:
                self.on_settings_requested()
        elif self.on_action_selected:
            self.on_action_selected(action)

    def render(self, game_state: Dict[str, Any]) -> None:
        """渲染游戏状态"""
        if not self.screen:
            return

        theme = theme_manager.get_theme()
        font_title = font_manager.get_font("title")
        font_normal = font_manager.get_font("normal")

        # 清屏
        self.screen.fill(theme.BACKGROUND)

        # 渲染标题
        title_text = font_title.render("极简修仙 MVP", True, theme.TEXT_PRIMARY)
        title_rect = title_text.get_rect(centerx=self.width // 2, y=10)
        self.screen.blit(title_text, title_rect)

        # 渲染角色信息
        self._render_character_info(game_state)

        # 渲染按钮
        self._render_buttons(game_state)

        # 渲染游戏日志
        self._render_game_log(game_state)

        # 渲染状态栏
        self._render_status_bar(game_state)

        # 更新显示
        pygame.display.flip()

    def _render_character_info(self, game_state: Dict[str, Any]):
        """渲染角色信息"""
        character = game_state.get("character")
        if not character:
            return

        theme = theme_manager.get_theme()
        font = font_manager.get_font("normal")

        # 格式化角色信息
        char_info = self.renderer.format_character_info(character)

        # 渲染角色基本信息
        info_config = self.layout.CHARACTER_INFO_LINES

        # 姓名行
        name_line = info_config["name_line"]["template"].format(
            name=char_info.name,
            talent=char_info.talent,
            realm=char_info.realm,
            exp=self.renderer.format_exp_display(character)
        )
        name_surface = font.render(name_line, True, theme.TEXT_PRIMARY)
        self.screen.blit(name_surface, info_config["name_line"]["pos"])

        # 生命值进度条和文字
        hp_bar = self.progress_bars["hp"]
        hp_bar.update_values(char_info.hp, char_info.max_hp)
        hp_bar.render(self.screen)

        hp_text = info_config["hp_line"]["template"].format(
            progress_bar="",
            current=char_info.hp,
            max=char_info.max_hp
        )
        hp_surface = font.render(hp_text, True, theme.HP_COLOR)
        self.screen.blit(hp_surface, info_config["hp_line"]["pos"])

        # 仙力值进度条和文字
        mp_bar = self.progress_bars["mp"]
        mp_bar.update_values(char_info.mp, char_info.max_mp)
        mp_bar.render(self.screen)

        mp_text = info_config["mp_line"]["template"].format(
            progress_bar="",
            current=char_info.mp,
            max=char_info.max_mp
        )
        mp_surface = font.render(mp_text, True, theme.MP_COLOR)
        self.screen.blit(mp_surface, info_config["mp_line"]["pos"])

        # 统计信息
        stats_text = info_config["stats_line"]["template"].format(
            pills=char_info.pills,
            streak=char_info.meditation_streak
        )
        stats_surface = font.render(stats_text, True, theme.TEXT_SECONDARY)
        self.screen.blit(stats_surface, info_config["stats_line"]["pos"])

    def _render_buttons(self, game_state: Dict[str, Any]):
        """渲染按钮"""
        character = game_state.get("character")
        actions = game_state.get("actions", [])

        if character and actions:
            # 更新按钮状态
            button_states = self.renderer.format_action_buttons(character, actions)

            for i, button in enumerate(self.buttons):
                if i < len(button_states):
                    button_state = button_states[i]
                    button.enabled = button_state.enabled
                    button.visible = button_state.visible

        # 渲染所有按钮
        for button in self.buttons:
            button.render(self.screen)

    def _render_game_log(self, game_state: Dict[str, Any]):
        """渲染游戏日志"""
        game_log = game_state.get("game_log")
        if not game_log:
            return

        theme = theme_manager.get_theme()
        font = font_manager.get_font("small")

        # 格式化日志
        log_entries = self.renderer.format_game_log(
            game_log.get_recent_entries(),
            self.layout.LOG_CONFIG["max_entries"]
        )

        # 渲染日志背景
        pygame.draw.rect(self.screen, theme.PANEL_BACKGROUND, self.layout.LOG_RECT)
        pygame.draw.rect(self.screen, theme.BORDER, self.layout.LOG_RECT, 2)

        # 渲染日志条目
        start_x, start_y = self.layout.LOG_CONFIG["start_pos"]
        line_height = self.layout.LOG_CONFIG["line_height"]

        for i, entry in enumerate(log_entries):
            y_pos = start_y + i * line_height
            if y_pos + line_height > self.layout.LOG_RECT.bottom:
                break

            # 根据日志类型选择颜色
            color = theme.TEXT_PRIMARY
            if "突破" in entry:
                color = theme.STATUS_COLORS["success"]
            elif "警告" in entry or "不足" in entry:
                color = theme.STATUS_COLORS["warning"]
            elif "失败" in entry or "死亡" in entry:
                color = theme.STATUS_COLORS["danger"]

            text_surface = font.render(entry, True, color)
            self.screen.blit(text_surface, (start_x, y_pos))

    def _render_status_bar(self, game_state: Dict[str, Any]):
        """渲染状态栏"""
        character = game_state.get("character")
        if not character:
            return

        theme = theme_manager.get_theme()
        font = font_manager.get_font("normal")

        # 渲染推荐信息
        recommendation = self.renderer.format_status_recommendation(character)
        status_config = self.layout.STATUS_CONFIG

        status_text = status_config["recommendation_template"].format(
            recommendation=recommendation
        )
        status_surface = font.render(status_text, True, theme.TEXT_SECONDARY)
        self.screen.blit(status_surface, status_config["recommendation_pos"])

        # 渲染状态栏按钮
        for button in self.buttons[-2:]:  # 只渲染状态栏按钮
            button.render(self.screen)

    def handle_input(self) -> Optional[UIEvent]:
        """处理用户输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return UIEvent("quit", {}, pygame.time.get_ticks())

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return UIEvent("quit", {}, pygame.time.get_ticks())

                # 处理快捷键
                action = self.input_handler.handle_key_press(event.key)
                if action:
                    return UIEvent("action", {"action": action}, pygame.time.get_ticks())

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 处理鼠标点击
                action = self.input_handler.handle_mouse_click(event.pos)
                if action:
                    return UIEvent("action", {"action": action}, pygame.time.get_ticks())

                # 处理按钮事件
                for button in self.buttons:
                    if button.handle_event(event):
                        break

            elif event.type == pygame.MOUSEMOTION:
                # 处理鼠标移动事件
                for button in self.buttons:
                    button.handle_event(event)

        return None

    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """显示消息对话框"""
        # 简单实现：打印到控制台
        print(f"[{message_type.upper()}] {title}: {message}")

    def get_character_name(self) -> Optional[str]:
        """获取角色名称输入"""
        # 简单实现：返回默认名称
        return "无名修士"

    def show_confirmation(self, title: str, message: str) -> bool:
        """显示确认对话框"""
        # 简单实现：总是返回True
        print(f"[确认] {title}: {message}")
        return True

    def update_display(self) -> None:
        """更新显示"""
        pygame.display.flip()

    def shutdown(self) -> None:
        """关闭界面"""
        self.running = False
        pygame.quit()

    def is_running(self) -> bool:
        """检查界面是否正在运行"""
        return self.running