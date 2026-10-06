"""
Pygame界面渲染器 - 具体的UI实现
"""

import pygame
import sys
from typing import Dict, Any, Optional, List
from .interface import GameInterface, UIEvent, GameStateRenderer, InputHandler, UIComponent
from .layouts import (
    default_layout,
    BUTTON_STYLE_JADE_PLATE,
    BUTTON_STYLE_SOLID,
    HUD_BACKDROP,
    HUD_TEXT_HP,
    HUD_TEXT_MP,
    HUD_TEXT_PRIMARY,
    HUD_TEXT_SECONDARY,
    IVORY_TEXT,
    JADE_BORDER,
    JADE_BORDER_BRIGHT,
    JADE_BORDER_DIM,
    JADE_PLATE,
    JADE_PLATE_HOVER,
    JADE_PLATE_PRESSED,
    JADE_SUBTEXT,
    JADE_TITLE,
    TOAST_FADE_IN_MS,
    TOAST_FADE_OUT_MS,
    TOAST_TOTAL_MS,
)
from .themes import theme_manager, font_manager

# 通知横幅的垂直内边距（使单行内容刚好撑满 TOAST_SLOT_HEIGHT）
TOAST_BANNER_VERTICAL_PADDING = 13
# 通知横幅左侧的色调标记宽度，用来区分灵气潮汐的增益/减益
TOAST_TONE_MARK_WIDTH = 3
# 文本被横幅宽度裁切时保留的省略号宽度余量
TOAST_ELLIPSIS_RESERVE = 12


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
            pygame.K_s: "settings",  # 添加设置快捷键
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
                 action: str, color=(0, 123, 255), text_color=(255, 255, 255),
                 style: str = BUTTON_STYLE_SOLID):
        super().__init__(position, size)
        self.text = text
        self.action = action
        self.image = None  # 圆形图标 Surface，有图时替代矩形绘制
        self.color = color
        self.text_color = text_color
        self.style = style
        self.hover_color = tuple(min(255, c + 20) for c in color)
        self.pressed_color = tuple(max(0, c - 20) for c in color)
        self.disabled_color = (200, 200, 200)
        self.is_hovered = False
        self.is_pressed = False
        self.on_click = None

    def _jade_plate_palette(self) -> dict:
        """仙侠玉牌按钮在当前交互状态下的配色"""
        if not self.enabled:
            return {
                "plate": JADE_PLATE,
                "border": JADE_BORDER_DIM,
                "text": HUD_TEXT_SECONDARY,
            }

        if self.is_pressed:
            return {
                "plate": JADE_PLATE_PRESSED,
                "border": JADE_BORDER,
                "text": IVORY_TEXT,
            }

        if self.is_hovered:
            return {
                "plate": JADE_PLATE_HOVER,
                "border": JADE_BORDER_BRIGHT,
                "text": IVORY_TEXT,
            }

        return {
            "plate": JADE_PLATE,
            "border": JADE_BORDER,
            "text": IVORY_TEXT,
        }

    def _render_jade_plate(self, surface):
        """绘制仙侠玉牌按钮：黑玉半透明底 + 青玉细线 1px 边框 + 米白文字"""
        x, y, w, h = self.rect
        palette = self._jade_plate_palette()
        radius = min(6, w // 4, h // 4)

        plate = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(plate, palette["plate"], plate.get_rect(),
                         border_radius=radius)
        pygame.draw.rect(plate, palette["border"], plate.get_rect(), 1,
                         border_radius=radius)
        surface.blit(plate, (x, y))

        font = font_manager.get_font("normal")
        text_surface = font.render(self.text, True, palette["text"])
        surface.blit(text_surface, text_surface.get_rect(center=(x + w // 2, y + h // 2)))

    def render(self, surface):
        """渲染按钮"""
        if not self.visible:
            return

        x, y, w, h = self.rect
        theme = theme_manager.get_theme()

        # 仙侠玉牌风格（右下系统按钮等无图标矩形按钮）
        if self.image is None and self.style == BUTTON_STYLE_JADE_PLATE:
            self._render_jade_plate(surface)
            return

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

        # 有图标时绘制圆形图标按钮（图标+下方文字，文字不能丢）
        if self.image is not None:
            img = self.image
            if not self.enabled:
                img = img.copy()
                img.fill((160, 160, 160, 120), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(img, (x, y))
            if self.is_hovered and self.enabled:
                pygame.draw.circle(surface, (255, 235, 180),
                                   (x + w // 2, y + h // 2), w // 2 + 3, 2)
            # 图标按钮的文字压在图标底部内部（不占布局外空间，避免被日志面板盖住）
            font = font_manager.get_font("small")
            text_surface = font.render(self.text, True, (255, 250, 235))
            text_rect = text_surface.get_rect(center=(x + w // 2, y + h - 14))
            pad = 4
            bg = pygame.Rect(text_rect.x - pad, text_rect.y - 2,
                             text_rect.width + pad * 2, text_rect.height + 4)
            bg_surf = pygame.Surface(bg.size, pygame.SRCALPHA)
            bg_surf.fill((10, 20, 25, 170))
            surface.blit(bg_surf, bg.topleft)
            surface.blit(text_surface, text_rect)
            return

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

        # GPT 生成的 UI 美术资产（文件名 -> Surface，缺失则为 None）
        self.ui_assets = {}

        # 非阻断 toast 队列
        self.toasts = []

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

            # 加载 GPT 生成的 UI 美术资产（缺失不阻塞）
            self._load_ui_assets()

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

        # 创建操作按钮（游戏动作）
        for button_config in self.layout.ACTION_BUTTONS:
            button = Button(
                (button_config["rect"].x, button_config["rect"].y),
                (button_config["rect"].width, button_config["rect"].height),
                button_config["name"],
                button_config["action"]
            )
            button.on_click = self._on_button_click
            self.buttons.append(button)

        # 创建状态栏按钮（系统动作）
        for button_config in self.layout.STATUS_BUTTONS:
            button = Button(
                (button_config["rect"].x, button_config["rect"].y),
                (button_config["rect"].width, button_config["rect"].height),
                button_config["name"],
                button_config["action"],
                style=button_config.get("style", BUTTON_STYLE_SOLID)
            )
            button.on_click = self._on_button_click
            self.buttons.append(button)

    def _load_ui_assets(self):
        """加载 assets/ui 下的美术资源，单个缺失不影响其他"""
        import os
        asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "assets", "ui")
        files = {
            "bg": "bg_main.png",
            "banner": "banner_title.png",
            "statusbar": "bar_status.png",
            "dialog": "panel_dialog.png",
            "btn_meditate": "btn_meditate.png",
            "btn_cultivate": "btn_cultivate.png",
            "btn_pill": "btn_pill.png",
            "btn_wait": "btn_wait.png",
            "tide_buff": "icon_tide_buff.png",
            "tide_debuff": "icon_tide_debuff.png",
        }
        for key, fname in files.items():
            path = os.path.join(asset_dir, fname)
            try:
                if key == "bg":
                    img = pygame.image.load(path).convert()
                else:
                    img = pygame.image.load(path).convert_alpha()
                self.ui_assets[key] = img
            except Exception as e:
                self.ui_assets[key] = None
                print(f"UI资产加载失败 {fname}: {e}")

        # 把图标赋给对应的动作按钮，并把点击区域改成正方形
        action_to_asset = {
            "meditate": "btn_meditate",
            "cultivate": "btn_cultivate",
            "consume_pill": "btn_pill",
            "wait": "btn_wait",
        }
        for button in self.buttons:
            asset_key = action_to_asset.get(button.action)
            img = self.ui_assets.get(asset_key) if asset_key else None
            if img is not None:
                # 尺寸取自布局，保证图标外框与点击区域一致
                size = self.layout.ACTION_BUTTON_ICON_SIZE
                button.image = pygame.transform.smoothscale(img, (size, size))
                rx, ry, rw, rh = button.rect
                button.position = (rx + rw // 2 - size // 2,
                                   ry + rh // 2 - size // 2)
                button.size = (size, size)

    def _on_button_click(self, action: str):
        """按钮点击回调"""
        # 检查是否为系统动作
        if self.renderer.is_system_action(action):
            if action == "restart" and self.on_restart_requested:
                self.on_restart_requested()
            elif action == "settings" and self.on_settings_requested:
                self.on_settings_requested()
            elif self.on_action_selected:  # 统一处理所有系统动作
                self.on_action_selected(action)
        elif self.on_action_selected:  # 游戏动作
            self.on_action_selected(action)

    def render(self, game_state: Dict[str, Any]) -> None:
        """渲染游戏状态"""
        if not self.screen:
            return

        theme = theme_manager.get_theme()
        font_title = font_manager.get_font("title")
        font_normal = font_manager.get_font("normal")

        # 背景：有美术资产用图，无图回退纯色
        bg = self.ui_assets.get("bg")
        if bg is not None:
            self.screen.blit(pygame.transform.smoothscale(bg, (self.width, self.height)), (0, 0))
        else:
            self.screen.fill(theme.BACKGROUND)

        # 标题横幅（有图用图，无图用文字）
        banner = self.ui_assets.get("banner")
        if banner is not None:
            bw, bh = 420, 140
            scaled = pygame.transform.smoothscale(banner, (bw, bh))
            self.screen.blit(scaled, (self.width // 2 - bw // 2, 4))
        else:
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

        # 非阻断 toast（灵气潮汐等）
        self.update_toasts()
        self.draw_toasts()

        # 更新显示
        pygame.display.flip()

    def _draw_character_backdrop(self):
        """绘制角色状态文字底板（黑玉半透明，约 70% 不透明）

        底板与文字分离：文字画在深色底板之上，保证白色云海背景下依然清晰。
        """
        backdrop_rect = self.layout.CHARACTER_INFO_BACKDROP_RECT
        backdrop = pygame.Surface(backdrop_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            backdrop,
            HUD_BACKDROP,
            backdrop.get_rect(),
            border_radius=8,
        )
        self.screen.blit(backdrop, backdrop_rect.topleft)

    def _render_character_info(self, game_state: Dict[str, Any]):
        """渲染角色信息"""
        character = game_state.get("character")
        if not character:
            return

        self._draw_character_backdrop()

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
            exp=char_info.exp,
            exp_threshold=char_info.exp_threshold
        )
        name_surface = font.render(name_line, True, HUD_TEXT_PRIMARY)
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
        hp_surface = font.render(hp_text, True, HUD_TEXT_HP)
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
        mp_surface = font.render(mp_text, True, HUD_TEXT_MP)
        self.screen.blit(mp_surface, info_config["mp_line"]["pos"])

        # 统计信息
        stats_text = info_config["stats_line"]["template"].format(
            pills=char_info.pills,
            streak=char_info.meditation_streak
        )
        stats_surface = font.render(stats_text, True, HUD_TEXT_SECONDARY)
        self.screen.blit(stats_surface, info_config["stats_line"]["pos"])

    def _render_buttons(self, game_state: Dict[str, Any]):
        """渲染按钮"""
        character = game_state.get("character")
        actions = game_state.get("actions", [])

        system_buttons = self.buttons[len(self.layout.ACTION_BUTTONS):]
        # 整体左移，避开状态栏背景图中的手形装饰。
        # UIComponent.rect 是只读 property，由 position/size 派生，改 position 即可。
        if not getattr(self, "_system_buttons_offset_applied", False):
            for button in system_buttons:
                px, py = button.position
                button.position = (px + self.layout.SYSTEM_BUTTONS_X_OFFSET, py)
            self._system_buttons_offset_applied = True

        # 更新游戏动作按钮状态
        if character and actions:
            # 只更新游戏动作按钮（前4个按钮）
            game_button_states = self.renderer.format_action_buttons(character, actions)

            # 分离游戏动作按钮和系统动作按钮
            game_buttons = self.buttons[:len(self.layout.ACTION_BUTTONS)]

            # 更新游戏动作按钮状态
            for i, button in enumerate(game_buttons):
                if i < len(game_button_states):
                    button_state = game_button_states[i]
                    button.enabled = button_state.enabled
                    button.visible = button_state.visible

            # 更新系统动作按钮状态
            system_button_states = self.renderer.format_system_action_buttons()
            for i, button in enumerate(system_buttons):
                if i < len(system_button_states):
                    button_state = system_button_states[i]
                    button.enabled = button_state.enabled
                    button.visible = button_state.visible

        # 只渲染游戏动作按钮；系统按钮由 _render_status_bar 在状态栏底图之上绘制
        for button in self.buttons[:len(self.layout.ACTION_BUTTONS)]:
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
        start_x = self.layout.LOG_RECT.left + self.layout.LOG_TEXT_PADDING_X
        text_right = self.layout.LOG_RECT.right - self.layout.LOG_TEXT_PADDING_X
        text_bottom = self.layout.LOG_RECT.bottom - self.layout.LOG_TEXT_PADDING_BOTTOM
        text_clip = pygame.Rect(start_x, start_y, text_right - start_x, text_bottom - start_y)
        self.screen.set_clip(text_clip)

        for i, entry in enumerate(log_entries):
            y_pos = start_y + i * line_height
            if y_pos + line_height > text_bottom:
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

        self.screen.set_clip(None)

    def _render_status_bar(self, game_state: Dict[str, Any]):
        """渲染状态栏"""
        character = game_state.get("character")
        if not character:
            return

        theme = theme_manager.get_theme()
        font = font_manager.get_font("normal")

        # 状态栏背景图
        statusbar = self.ui_assets.get("statusbar")
        if statusbar is not None:
            rect = self.layout.STATUS_RECT
            self.screen.blit(
                pygame.transform.smoothscale(statusbar, (rect.width, rect.height)),
                (rect.x, rect.y))

        # 灵气潮汐待生效图标
        tide_effect = game_state.get("tide_effect")
        if tide_effect:
            tone = tide_effect.get("tone", "buff")
            icon = self.ui_assets.get("tide_buff" if tone == "buff" else "tide_debuff")
            if icon is not None:
                rect = self.layout.STATUS_RECT
                size = 40
                scaled = pygame.transform.smoothscale(icon, (size, size))
                self.screen.blit(scaled, (rect.right - size - 6,
                                          rect.y + (rect.height - size) // 2))

        # 渲染推荐信息
        recommendation = self.renderer.format_status_recommendation(character)
        status_config = self.layout.STATUS_CONFIG

        status_text = status_config["recommendation_template"].format(
            recommendation=recommendation
        )
        status_surface = font.render(status_text, True, theme.TEXT_PRIMARY)
        rec_pos = (
            self.layout.STATUS_RECT.left + self.layout.LOG_TEXT_PADDING_X,
            self.layout.STATUS_RECT.bottom
            - self.layout.LOG_TEXT_PADDING_BOTTOM
            - status_surface.get_height(),
        )
        self.screen.blit(status_surface, rec_pos)

        # 吐纳连击小字（连击层数 / 收益倍率 / 下次走火概率），与推荐语同一行、靠状态栏按钮左侧
        combo_status = str(game_state.get("breath_combo_status") or "")
        if combo_status:
            small_font = font_manager.get_font("small")
            combo_color = (
                theme.STATUS_COLORS["warning"]
                if game_state.get("fire_deviation_turn")
                else HUD_TEXT_SECONDARY
            )

            # 右边界避开状态栏按钮，左边界避开推荐语，太窄就不画
            status_buttons = self.layout.STATUS_BUTTONS
            right_edge = min(
                (button["rect"].left for button in status_buttons),
                default=self.layout.STATUS_RECT.right
            ) - self.layout.LOG_TEXT_PADDING_X
            available_width = (
                right_edge - (rec_pos[0] + status_surface.get_width()) - 8
            )

            combo_text = self._fit_text(combo_status, small_font, available_width)
            if combo_text:
                combo_surface = small_font.render(combo_text, True, combo_color)
                self.screen.blit(
                    combo_surface,
                    (
                        right_edge - combo_surface.get_width(),
                        rec_pos[1]
                        + (status_surface.get_height() - combo_surface.get_height()) // 2,
                    )
                )

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

    def show_toast(self, title, sub_message="", tone="info",
                   duration_ms=TOAST_TOTAL_MS):
        """显示屏幕提示（顶部通知槽）"""
        if tone not in ("buff", "debuff", "info"):
            tone = "info"

        self.toasts.append({
            "title": title,
            "sub_message": sub_message,
            "tone": tone,
            "duration_ms": duration_ms,
            "created_ms": pygame.time.get_ticks()
        })

        # 最多保留三条提示，超出时丢弃最早的提示
        while len(self.toasts) > 3:
            self.toasts.pop(0)

    def update_toasts(self):
        """移除已经过期的屏幕提示"""
        now = pygame.time.get_ticks()
        self.toasts = [
            toast for toast in self.toasts
            if toast["created_ms"] + toast["duration_ms"] >= now
        ]

    def _get_toast_alpha(self, toast, now: int) -> int:
        """计算提示不透明度：200ms 淡入 -> 停留 -> 300ms 淡出"""
        duration = max(1, int(toast.get("duration_ms", TOAST_TOTAL_MS)))
        age = now - toast["created_ms"]

        if age <= 0:
            return 0

        if age < TOAST_FADE_IN_MS:
            ratio = age / TOAST_FADE_IN_MS
        elif age >= duration - TOAST_FADE_OUT_MS:
            ratio = max(0, (duration - age) / TOAST_FADE_OUT_MS)
        else:
            return 255

        return max(0, min(255, int(ratio * 255)))

    @staticmethod
    def _fit_text(text: str, font, max_width: int) -> str:
        """按可用宽度裁切文本并补省略号，避免横幅溢出固定宽度"""
        if max_width <= 0 or not text:
            return ""

        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "…"
        ellipsis_width = font.size(ellipsis)[0]
        clipped = text
        while clipped and font.size(clipped)[0] + ellipsis_width > max_width:
            clipped = clipped[:-1]

        return clipped + ellipsis

    def draw_toasts(self):
        """在顶部通知槽绘制动态细横幅

        方案D：横幅固定落在「顶部状态HUD底板」与「四个圆形操作按钮」之间的
        通知槽内，宽 400~500、高 45~60、水平居中，绝不覆盖圆形操作按钮。
        """
        if self.screen is None or not self.toasts:
            return

        layout = self.layout
        theme = theme_manager.get_theme()
        title_font = font_manager.get_font("normal")
        sub_font = font_manager.get_font("small")
        now = pygame.time.get_ticks()

        padding_x = layout.TOAST_BANNER_PADDING_X
        padding_y = TOAST_BANNER_VERTICAL_PADDING
        tone_mark = TOAST_TONE_MARK_WIDTH

        # 通知槽只有一格，按入队顺序依次播报，每条都拿满自己的停留时长
        toast = self.toasts[0]
        title = str(toast.get("title", ""))
        sub_message = str(toast.get("sub_message", ""))

        line_height = max(
            title_font.get_linesize(),
            sub_font.get_linesize() if sub_message else 0
        )

        # 横幅按内容在 400~500 / 45~60 之间自适应，超长内容再按宽度裁切
        natural_width = padding_x * 2 + tone_mark + title_font.size(title)[0]
        if sub_message:
            natural_width += (
                layout.TOAST_BANNER_TITLE_GAP
                + sub_font.size(sub_message)[0]
            )

        banner_rect = layout.get_toast_banner_rect(
            content_width=natural_width,
            content_height=line_height + padding_y * 2
        )

        # 内容超出横幅宽度时，先裁副文本，标题优先完整保留
        available_width = banner_rect.width - padding_x * 2 - tone_mark
        title_text = self._fit_text(title, title_font, available_width)
        sub_text = ""
        if sub_message:
            sub_room = (
                available_width
                - title_font.size(title_text)[0]
                - layout.TOAST_BANNER_TITLE_GAP
            )
            sub_text = self._fit_text(sub_message, sub_font, sub_room)

        # 黑玉半透明底板
        toast_surface = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
        toast_surface.fill(JADE_PLATE)

        # 青玉色 1px 细线边框
        pygame.draw.rect(
            toast_surface,
            JADE_BORDER,
            toast_surface.get_rect(),
            1
        )

        # 左侧色调标记，保留灵气潮汐的增益/减益语义
        tone = toast.get("tone", "info")
        if tone == "buff":
            tone_color = getattr(theme, "TIDE_BUFF", (32, 201, 151))
        elif tone == "debuff":
            tone_color = getattr(theme, "TIDE_DEBUFF", (253, 126, 20))
        else:
            tone_color = JADE_SUBTEXT
        pygame.draw.rect(
            toast_surface,
            tone_color,
            pygame.Rect(1, 1, tone_mark, banner_rect.height - 2)
        )

        text_left = tone_mark + padding_x
        # 注意：toast_surface 是独立 surface，用局部坐标（banner_rect.centery 是屏幕坐标，会把字画飞）
        center_y = toast_surface.get_rect().centery

        # 标题：玉绿色（画在带透明通道的横幅上，淡入淡出才会整体生效）
        if title_text:
            title_surface = title_font.render(title_text, True, JADE_TITLE)
            toast_surface.blit(
                title_surface,
                title_surface.get_rect(
                    midleft=(text_left, center_y)
                )
            )

        # 副文本：灰白
        if sub_text:
            sub_surface = sub_font.render(sub_text, True, JADE_SUBTEXT)
            toast_surface.blit(
                sub_surface,
                sub_surface.get_rect(
                    midleft=(
                        text_left
                        + title_font.size(title_text)[0]
                        + layout.TOAST_BANNER_TITLE_GAP,
                        center_y
                    )
                )
            )

        alpha = self._get_toast_alpha(toast, now)
        if alpha < 255:
            toast_surface.set_alpha(alpha)

        self.screen.blit(toast_surface, banner_rect.topleft)
    def show_tide_preview(self, effect, preview=""):
        """显示灵气潮汐预兆（先亮后动：只预告，效果等对应行动才结算）"""
        sub_message = preview or str(effect.get("label", ""))
        self.show_toast(
            title="灵气潮汐预兆",
            sub_message=sub_message,
            tone=effect.get("tone", "buff")
        )
    def show_tide_consumed(self, label, tone, before, after):
        """显示灵气潮汐消耗提示"""
        self.show_toast(
            title="潮汐已生效并消耗",
            sub_message=f"{label}｜{before} → {after}",
            tone=tone
        )

    def get_character_name(self) -> Optional[str]:
        """获取角色名称输入"""
        # 简单实现：返回默认名称
        return "无名修士"

    def show_confirmation(self, title: str, message: str) -> bool:
        """显示是/否确认对话框并等待用户选择。"""
        if self.screen is None:
            return False

        theme = theme_manager.get_theme()
        title_font = font_manager.get_font("title")
        message_font = font_manager.get_font("normal")
        button_font = font_manager.get_font("normal")

        screen_width, screen_height = self.screen.get_size()
        margin = 20
        dialog_width = max(1, min(520, screen_width - 2 * margin))
        padding = min(24, max(8, dialog_width // 10))
        content_width = max(1, dialog_width - 2 * padding)
        button_gap = 20
        button_width = max(
            1,
            min(120, (dialog_width - 2 * padding - button_gap) // 2),
        )
        button_height = 40

        def wrap_text(text: str, font):
            lines = []
            for paragraph in str(text).splitlines() or [""]:
                current = ""
                for char in paragraph:
                    candidate = current + char
                    if current and font.size(candidate)[0] > content_width:
                        lines.append(current)
                        current = char
                    else:
                        current = candidate
                lines.append(current)
            return lines

        title_lines = wrap_text(title, title_font)
        message_lines = wrap_text(message, message_font)
        title_line_height = title_font.get_linesize()
        message_line_height = message_font.get_linesize()
        title_height = len(title_lines) * title_line_height

        desired_height = (
            padding * 2
            + title_height
            + 12
            + len(message_lines) * message_line_height
            + 20
            + button_height
        )
        available_height = max(1, screen_height - 2 * margin)
        dialog_height = min(max(190, desired_height), available_height)

        dialog_rect = pygame.Rect(0, 0, dialog_width, dialog_height)
        dialog_rect.center = (screen_width // 2, screen_height // 2)

        button_y = dialog_rect.bottom - padding - button_height
        buttons_left = dialog_rect.centerx - (button_width * 2 + button_gap) // 2
        yes_rect = pygame.Rect(buttons_left, button_y, button_width, button_height)
        no_rect = pygame.Rect(
            buttons_left + button_width + button_gap,
            button_y,
            button_width,
            button_height,
        )

        title_top = dialog_rect.top + padding
        message_top = title_top + title_height + 12
        max_message_lines = max(
            0, (button_y - message_top - 8) // message_line_height
        )
        visible_message_lines = message_lines[:max_message_lines]
        if len(message_lines) > max_message_lines and visible_message_lines:
            last_line = visible_message_lines[-1]
            while (
                last_line
                and message_font.size(last_line + "...")[0] > content_width
            ):
                last_line = last_line[:-1]
            visible_message_lines[-1] = last_line + "..."

        panel_color = getattr(theme, "PANEL_BACKGROUND", (40, 40, 40))
        border_color = getattr(theme, "BORDER", (180, 180, 180))
        text_primary = getattr(theme, "TEXT_PRIMARY", (255, 255, 255))
        text_secondary = getattr(theme, "TEXT_SECONDARY", (220, 220, 220))
        button_text_color = getattr(theme, "BUTTON_TEXT", (255, 255, 255))
        yes_color = getattr(theme, "BUTTON_PRIMARY", (0, 123, 255))
        no_color = getattr(theme, "BUTTON_SECONDARY", (105, 105, 105))
        yes_hover_color = tuple(
            min(255, int(channel) + 30) for channel in yes_color[:3]
        )
        no_hover_color = tuple(
            min(255, int(channel) + 30) for channel in no_color[:3]
        )

        overlay = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 180))

        def draw_dialog(yes_hovered: bool, no_hovered: bool) -> None:
            self.screen.blit(overlay, (0, 0))
            pygame.draw.rect(self.screen, panel_color, dialog_rect)
            pygame.draw.rect(self.screen, border_color, dialog_rect, 2)

            current_y = title_top
            for line in title_lines:
                title_surface = title_font.render(line, True, text_primary)
                title_rect = title_surface.get_rect(
                    centerx=dialog_rect.centerx,
                    top=current_y,
                )
                self.screen.blit(title_surface, title_rect)
                current_y += title_line_height

            current_y = message_top
            for line in visible_message_lines:
                message_surface = message_font.render(line, True, text_secondary)
                self.screen.blit(
                    message_surface,
                    (dialog_rect.left + padding, current_y),
                )
                current_y += message_line_height

            buttons = (
                (yes_rect, "是", yes_color, yes_hover_color, yes_hovered),
                (no_rect, "否", no_color, no_hover_color, no_hovered),
            )
            for button_rect, label, normal_color, hover_color, hovered in buttons:
                pygame.draw.rect(
                    self.screen,
                    hover_color if hovered else normal_color,
                    button_rect,
                )
                pygame.draw.rect(
                    self.screen,
                    border_color,
                    button_rect,
                    2,
                )
                label_surface = button_font.render(
                    label,
                    True,
                    button_text_color,
                )
                self.screen.blit(
                    label_surface,
                    label_surface.get_rect(center=button_rect.center),
                )

            pygame.display.flip()

        hover_yes = False
        hover_no = False
        draw_dialog(hover_yes, hover_no)

        keypad_enter = getattr(pygame, "K_KP_ENTER", pygame.K_RETURN)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False

                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    typed = (getattr(event, "unicode", "") or "").lower()

                    if (
                        key in (pygame.K_y, pygame.K_RETURN, keypad_enter)
                        or typed == "y"
                    ):
                        return True

                    if key in (pygame.K_n, pygame.K_ESCAPE) or typed == "n":
                        return False

                elif event.type == pygame.MOUSEMOTION:
                    hover_yes = yes_rect.collidepoint(event.pos)
                    hover_no = no_rect.collidepoint(event.pos)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if getattr(event, "button", 1) != 1:
                        continue

                    if yes_rect.collidepoint(event.pos):
                        return True
                    if no_rect.collidepoint(event.pos):
                        return False

            draw_dialog(hover_yes, hover_no)
            pygame.time.wait(16)

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