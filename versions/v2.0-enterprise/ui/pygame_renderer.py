"""
Pygame界面渲染器 - 具体的UI实现
"""

from __future__ import annotations

import pygame
import sys
from typing import Dict, Any, Optional, List
from .interface import GameInterface, UIEvent, GameStateRenderer, InputHandler, UIComponent
from .layouts import (
    default_layout,
    BUTTON_STYLE_JADE_PLATE,
    BUTTON_STYLE_SOLID,
    HUD_AVATAR_FILL,
    HUD_BACKDROP,
    HUD_BAR_FILL_HP,
    HUD_BAR_FILL_MP,
    HUD_BAR_TRACK,
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
from .config import effects_config
from .sound_manager import SoundManager
from .effects import EffectManager, ease_out


def _K(name: str, fallback: int) -> int:
    """按键常量兼容：pygbag 的 pygame-ce wasm 版缺 pygame.constants，
    直接 getattr(pygame, ...) 会 AttributeError。用 ASCII 码回退
    （SDL 键码与 ASCII 一致：K_1=49, K_a=97, K_ESCAPE=27, K_RETURN=13）。
    注意：只能在运行时调用（pygame.init 之后），不要在模块顶层求值。"""
    return getattr(pygame, name, fallback)


class _Keys:
    """按键常量惰性命名空间：_KEYS.K_1 首次访问时才求值，避免模块导入时碰 pygame。"""
    _FALLBACKS = {
        "K_1": ord("1"), "K_2": ord("2"), "K_3": ord("3"), "K_4": ord("4"),
        "K_r": ord("r"), "K_s": ord("s"), "K_y": ord("y"), "K_n": ord("n"),
        "K_ESCAPE": 27, "K_RETURN": 13,
    }

    def __getattr__(self, name: str) -> int:
        if name == "K_KP_ENTER":
            return _K("K_KP_ENTER", self.K_RETURN)
        if name in self._FALLBACKS:
            return _K(name, self._FALLBACKS[name])
        raise AttributeError(name)


_KEYS = _Keys()

# 通知横幅的垂直内边距（使单行内容刚好撑满 TOAST_SLOT_HEIGHT）
TOAST_BANNER_VERTICAL_PADDING = 13
# 通知横幅左侧的色调标记宽度，用来区分灵气潮汐的增益/减益
TOAST_TONE_MARK_WIDTH = 3
# 文本被横幅宽度裁切时保留的省略号宽度余量
TOAST_ELLIPSIS_RESERVE = 12
# 境界顺序，用于判断「境界提升」（重开局境界会回退，不该触发突破特效）
REALM_ORDER = ("炼气期", "筑基期", "结丹期", "元婴期", "化神期", "飞升")


class PygameInputHandler(InputHandler):
    """Pygame输入处理器"""

    def __init__(self, layout):
        self.layout = layout
        self.shortcuts = {
            _KEYS.K_1: "meditate",
            _KEYS.K_2: "consume_pill",
            _KEYS.K_3: "cultivate",
            _KEYS.K_4: "wait",
            _KEYS.K_r: "restart",
            _KEYS.K_s: "settings",  # 添加设置快捷键
            _KEYS.K_ESCAPE: "quit"
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
                 color=(0, 123, 255), bg_color=(200, 200, 200),
                 border_color=(100, 100, 100)):
        super().__init__(position, size)
        self.current_value = current_value
        self.max_value = max_value
        self.color = color
        self.bg_color = bg_color
        self.border_color = border_color

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
        if self.border_color is not None:
            pygame.draw.rect(surface, self.border_color, (x, y, w, h), 1)

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
        # 按压动画起始时刻（None 表示无动画），只影响绘制不影响布局
        self._press_started_ms = None

    def trigger_press(self) -> None:
        """进入按压态，开始 120ms 缩放弹回动画"""
        self.is_pressed = True
        if effects_config.ENABLED:
            self._press_started_ms = pygame.time.get_ticks()

    def release_press(self) -> None:
        """离开按压态，立即取消未播完的按压动画"""
        self.is_pressed = False
        self._press_started_ms = None

    def _press_scale(self) -> float:
        """按压缩放系数：按下瞬间 0.95，在 120ms 内缓动弹回 1.0"""
        if not effects_config.ENABLED or self._press_started_ms is None:
            return 1.0

        elapsed = pygame.time.get_ticks() - self._press_started_ms
        duration = effects_config.button_press_duration_ms()
        if elapsed >= duration:
            self._press_started_ms = None
            return 1.0

        min_scale = effects_config.button_press_min_scale()
        ratio = ease_out(elapsed / duration)
        return min_scale + (1.0 - min_scale) * ratio

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

    def _render_jade_plate(self, surface, x: int = None, y: int = None,
                            w: int = None, h: int = None):
        """绘制仙侠玉牌按钮：黑玉半透明底 + 青玉细线 1px 边框 + 米白文字"""
        rect_x, rect_y, rect_w, rect_h = self.rect
        x = rect_x if x is None else x
        y = rect_y if y is None else y
        w = rect_w if w is None else w
        h = rect_h if h is None else h
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
        """渲染按钮（按压动画只缩放绘制，不改 position/size，点击区域与布局不变）"""
        if not self.visible:
            return

        x, y, w, h = self.rect
        scale = self._press_scale()

        if scale >= 1.0:
            self._render_content(surface, x, y, w, h)
            return

        # 有按压动画时先在原始尺寸的离屏表面上绘制，再整体缩放并居中贴回
        base = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
        self._render_content(base, 0, 0, w, h)
        scaled_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        surface.blit(
            pygame.transform.smoothscale(base, scaled_size),
            (x + (w - scaled_size[0]) // 2, y + (h - scaled_size[1]) // 2),
        )

    def _render_content(self, surface, x: int, y: int, w: int, h: int):
        """在指定 surface 上按原始尺寸绘制按钮内容"""
        theme = theme_manager.get_theme()

        # 仙侠玉牌风格（右下系统按钮等无图标矩形按钮）
        if self.image is None and self.style == BUTTON_STYLE_JADE_PLATE:
            self._render_jade_plate(surface, x, y, w, h)
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
                             text_surface.get_width() + pad * 2, text_surface.get_height() + 4)
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
                self.trigger_press()
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            was_pressed = self.is_pressed
            if was_pressed and self.is_point_inside(event.pos):
                self.release_press()
                if self.on_click:
                    self.on_click(self.action)
                return True
            self.release_press()

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

        # 音效（缺文件/无音频设备时静音降级）与动效（默认开，可在 ui/config.py 关）
        self.sound = SoundManager()
        self.effects = EffectManager()

        # 表现层状态快照：用来识别「境界提升 / 经验增加 / 走火」这类瞬时变化
        self._prev_realm = None
        self._prev_exp = None
        self._prev_deviation_turns = 0
        self._tribulation_ready = False
        self._state_signals_ok = True

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

            # 加载音效（缺文件/无音频设备都不阻塞，内部已做静音降级）
            self.sound.initialize()

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

        # 创建进度条（顶部状态条内的细进度条）
        info_lines = self.layout.CHARACTER_INFO_LINES
        self.progress_bars["hp"] = ProgressBar(
            (info_lines["hp_line"]["bar_rect"].x,
             info_lines["hp_line"]["bar_rect"].y),
            (info_lines["hp_line"]["bar_rect"].width,
             info_lines["hp_line"]["bar_rect"].height),
            color=HUD_BAR_FILL_HP,
            bg_color=HUD_BAR_TRACK,
            border_color=JADE_BORDER_DIM
        )

        self.progress_bars["mp"] = ProgressBar(
            (info_lines["mp_line"]["bar_rect"].x,
             info_lines["mp_line"]["bar_rect"].y),
            (info_lines["mp_line"]["bar_rect"].width,
             info_lines["mp_line"]["bar_rect"].height),
            color=HUD_BAR_FILL_MP,
            bg_color=HUD_BAR_TRACK,
            border_color=JADE_BORDER_DIM
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
        # 点击音 + 动作专属音效（失败/无效动作也只响点击音，不报错）
        self._play_action_feedback(action)

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

    def _play_action_feedback(self, action: str) -> None:
        """播放一次交互反馈：按钮点击音 + 该动作的专属音效"""
        self.sound.play("click")

        # 「修炼」按钮在经验条满时会临时变成渡劫，此时播渡劫音
        override = "tribulation" if action == "cultivate" and self._tribulation_ready else None
        self.sound.play_action(action, override)

    def _exp_pop_anchor(self) -> tuple:
        """经验数字跳动的落点：顶部状态条中部（生命/仙力数值右侧的空位）"""
        info_lines = self.layout.CHARACTER_INFO_LINES
        value_rect = info_lines["mp_line"]["value_rect"]
        return (value_rect.right + 8, int(self.layout.HUD_RECT.centery))

    def _sync_play_signals(self, game_state: Dict[str, Any]) -> None:
        """比对前后两帧状态，把瞬时变化翻译成音效与动效

        只读游戏状态、不改玩法逻辑：境界提升 -> 突破圆环+音效，
        经验增加 -> +N 上浮，走火（紊乱回合数增加）-> 红边脉冲+音效。
        """
        character = game_state.get("character")
        self._tribulation_ready = bool(game_state.get("tribulation_ready"))

        if not character or not self._state_signals_ok:
            if not character:
                self._prev_realm = None
                self._prev_exp = None
                self._prev_deviation_turns = 0
            return

        try:
            experience = getattr(character, "experience", None)
            realm = getattr(experience, "current_realm", None)
            realm_name = str(getattr(realm, "value", realm) or "")
            current_exp = int(getattr(experience, "current_level_experience", 0))
            deviation_turns = int(game_state.get("fire_deviation_turn") or 0)
        except Exception as e:
            # 状态结构异常时只停用表现层信号，不再逐帧重试刷屏
            self._state_signals_ok = False
            print(f"表现层状态同步失败（音效/动效自动降级）: {e}")
            return

        previous_realm = self._prev_realm
        previous_exp = self._prev_exp

        # 首帧只记录基线，不触发任何反馈
        if previous_realm is not None:
            if self._realm_index(realm_name) > self._realm_index(previous_realm):
                # 境界提升（重开局境界回退，不会走到这里）
                self.effects.trigger_breakthrough(
                    (self.width // 2, self.height // 2),
                    (self.width, self.height),
                )
                self.sound.play("breakthrough")
            elif previous_exp is not None and current_exp > previous_exp:
                self.effects.trigger_exp_gain(current_exp - previous_exp,
                                               self._exp_pop_anchor())

            if deviation_turns > self._prev_deviation_turns:
                self.effects.trigger_deviation()
                self.sound.play("deviation")

        self._prev_realm = realm_name
        self._prev_exp = current_exp
        self._prev_deviation_turns = deviation_turns

    @staticmethod
    def _realm_index(realm_name: str) -> int:
        """境界序号（未知境界返回 -1，不会被当成提升）"""
        try:
            return REALM_ORDER.index(realm_name)
        except ValueError:
            return -1

    def render(self, game_state: Dict[str, Any]) -> None:
        """渲染游戏状态"""
        if not self.screen:
            return

        # 先比对状态变化，保证本帧就能看到本回合的突破/走火/经验反馈
        self._sync_play_signals(game_state)

        theme = theme_manager.get_theme()
        font_title = font_manager.get_font("title")
        font_normal = font_manager.get_font("normal")

        # 背景：有美术资产用图，无图回退纯色
        bg = self.ui_assets.get("bg")
        if bg is not None:
            self.screen.blit(pygame.transform.smoothscale(bg, (self.width, self.height)), (0, 0))
        else:
            self.screen.fill(theme.BACKGROUND)

        # 标题横幅（有图用图，无图用文字），贴在顶部状态条下方
        banner = self.ui_assets.get("banner")
        banner_rect = self.layout.TITLE_BANNER_RECT
        if banner is not None:
            scaled = pygame.transform.smoothscale(
                banner, (banner_rect.width, banner_rect.height)
            )
            self.screen.blit(scaled, banner_rect.topleft)
        else:
            title_text = font_title.render("极简修仙 MVP", True, theme.TEXT_PRIMARY)
            self.screen.blit(title_text, title_text.get_rect(
                midtop=(self.width // 2, banner_rect.y + 8)
            ))

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

        # 动效层（突破圆环 / 走火脉冲 / 经验跳动），永远画在最上层
        self.effects.draw(self.screen)

        # 更新显示
        pygame.display.flip()

    def _draw_hud_backdrop(self):
        """绘制顶部通栏状态条底板（黑玉半透明 + 青玉发丝分隔线）

        底板与文字分离：文字画在深色底板之上，保证白色云海背景下依然清晰。
        """
        hud_rect = self.layout.HUD_RECT
        backdrop = pygame.Surface(hud_rect.size, pygame.SRCALPHA)
        backdrop.fill(HUD_BACKDROP)
        pygame.draw.line(
            backdrop,
            JADE_BORDER_DIM,
            (0, hud_rect.height - 1),
            (hud_rect.width, hud_rect.height - 1)
        )
        self.screen.blit(backdrop, hud_rect.topleft)

    def _render_hud_avatar(self, realm: str):
        """状态条左侧的小圆头像：纯色圆 + 境界首字（如「炼」）"""
        avatar_rect = self.layout.CHARACTER_INFO_LINES["avatar"]["rect"]
        center = avatar_rect.center
        radius = avatar_rect.width // 2

        pygame.draw.circle(self.screen, HUD_AVATAR_FILL, center, radius)
        pygame.draw.circle(self.screen, JADE_BORDER, center, radius, 1)

        initial = str(realm or "")[:1]
        if not initial:
            return

        initial_surface = font_manager.get_font("normal").render(
            initial, True, HUD_TEXT_PRIMARY
        )
        self.screen.blit(initial_surface, initial_surface.get_rect(center=center))

    def _render_hud_text(self, text: str, font, color, left: int, center_y: int,
                         max_width: int = 0) -> int:
        """在状态条内按「左边界 + 垂直中线」绘制一行小字，超宽按省略号裁切

        返回实际占用宽度，供同一行内的后续文字接着排。
        """
        if not text:
            return 0

        if max_width > 0:
            text = self._fit_text(text, font, max_width)
            if not text:
                return 0

        surface = font.render(text, True, color)
        rect = surface.get_rect(midleft=(left, center_y))
        if max_width > 0:
            rect.width = min(rect.width, max_width)
        self.screen.blit(surface, rect)
        return surface.get_width()

    def _render_character_info(self, game_state: Dict[str, Any]):
        """渲染顶部状态条：头像+名字/境界 | 生命/仙力细条 | 丹药 | 连击"""
        character = game_state.get("character")
        if not character:
            return

        self._draw_hud_backdrop()

        theme = theme_manager.get_theme()
        name_font = font_manager.get_font("normal")
        small_font = font_manager.get_font("small")
        info_config = self.layout.CHARACTER_INFO_LINES

        char_info = self.renderer.format_character_info(character)

        # 左：圆形头像 + 「名字 · 境界」
        self._render_hud_avatar(char_info.realm)

        name_cfg = info_config["name_line"]
        name_x, name_mid = name_cfg["pos"]
        name_max = name_cfg.get("max_width", 0)
        cursor = name_x
        cursor += self._render_hud_text(
            char_info.name,
            name_font,
            HUD_TEXT_PRIMARY,
            cursor,
            name_mid,
            max(0, name_max - self.layout.HUD_NAME_REALM_RESERVE)
        )
        cursor += self._render_hud_text(
            " · ", name_font, HUD_TEXT_SECONDARY, cursor, name_mid
        )
        self._render_hud_text(
            char_info.realm,
            name_font,
            JADE_TITLE,
            cursor,
            name_mid,
            max(0, name_x + name_max - cursor)
        )

        # 中：生命 / 仙力细进度条 + 数值
        for line_key, bar_key, current, maximum in (
            ("hp_line", "hp", char_info.hp, char_info.max_hp),
            ("mp_line", "mp", char_info.mp, char_info.max_mp),
        ):
            line_cfg = info_config[line_key]
            bar_rect = line_cfg["bar_rect"]
            value_rect = line_cfg["value_rect"]

            bar = self.progress_bars[bar_key]
            bar.update_values(current, maximum)
            bar.render(self.screen)

            label_cfg = line_cfg.get("label")
            if label_cfg:
                shown_label = ("寿元" if bar_key == "hp" else "配额") if game_state.get("risk_mode") else label_cfg
                label_surface = small_font.render(shown_label, True, HUD_TEXT_SECONDARY)
                self.screen.blit(label_surface, label_surface.get_rect(
                    midleft=(line_cfg["pos"][0], bar_rect.centery)
                ))

            self._render_hud_text(
                line_cfg["template"].format(current=current, max=maximum),
                small_font,
                HUD_TEXT_HP if bar_key == "hp" else HUD_TEXT_MP,
                value_rect.x,
                int(bar_rect.centery),
                value_rect.width
            )

        # 中右：丹药数量 + 连击小字（连击层数 / 走火概率）
        pills_cfg = info_config["stats_line"]
        self._render_hud_text(
            pills_cfg["template"].format(pills=char_info.pills),
            small_font,
            HUD_TEXT_SECONDARY,
            pills_cfg["pos"][0],
            pills_cfg["pos"][1],
            pills_cfg.get("max_width", 0)
        )

        combo_cfg = info_config["combo_line"]
        combo_color = (
            theme.STATUS_COLORS["warning"]
            if game_state.get("fire_deviation_turn")
            else JADE_TITLE
        )
        self._render_hud_text(
            combo_cfg["template"].format(
                combo=str(game_state.get("breath_combo_status") or "")
            ),
            small_font,
            combo_color,
            combo_cfg["pos"][0],
            combo_cfg["pos"][1],
            combo_cfg.get("max_width", 0)
        )

        # 右下第二行：境界配额（丹药 X/6 · 修炼 X/12），破心魔加速时并排显示
        quota_status = game_state.get("quota_status") or {}
        quota_text = str(quota_status.get("text") or "")
        demon_status = str(game_state.get("demon_cleared_status") or "")
        if demon_status:
            quota_text = f"{quota_text} · {demon_status}" if quota_text else demon_status

        quota_cfg = info_config["quota_line"]
        self._render_hud_text(
            quota_cfg["template"].format(quota=quota_text),
            small_font,
            theme.STATUS_COLORS["warning"]
            if quota_status.get("exhausted") or game_state.get("fire_deviation_turn")
            else HUD_TEXT_SECONDARY,
            quota_cfg["pos"][0],
            quota_cfg["pos"][1],
            quota_cfg.get("max_width", 0)
        )

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

            # 按钮文字按状态改写：渡劫（成功率X%）/ 破心魔 / 静心（不新增按钮）
            action_labels = game_state.get("action_labels") or {}
            for button in game_buttons:
                label = action_labels.get(button.action)
                if label:
                    button.text = label

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
        recommendation = (game_state.get("recommendation") if game_state.get("risk_mode") else self.renderer.format_status_recommendation(character))
        status_config = self.layout.STATUS_CONFIG

        status_text = status_config["recommendation_template"].format(
            recommendation=recommendation
        )
        if game_state.get("risk_mode"):
            status_text = self._fit_text(status_text, font, self.layout.STATUS_RECT.width - 115)
        status_surface = font.render(status_text, True, theme.TEXT_PRIMARY)
        rec_pos = (
            self.layout.STATUS_RECT.left + self.layout.LOG_TEXT_PADDING_X,
            self.layout.STATUS_RECT.bottom
            - self.layout.LOG_TEXT_PADDING_BOTTOM
            - status_surface.get_height(),
        )
        self.screen.blit(status_surface, rec_pos)

        # 注：吐纳连击小字（连击层数 / 走火概率）已移到顶部状态条中部，此处不再重复

        # 渲染状态栏按钮
        for button in self.buttons[-2:]:  # 只渲染状态栏按钮
            button.render(self.screen)

    def _button_at(self, position: tuple) -> Optional[Button]:
        """找出鼠标位置命中的按钮（用于按压动画，不影响点击区域判定）"""
        for button in self.buttons:
            if button.visible and button.is_point_inside(position):
                return button
        return None

    def handle_input(self) -> Optional[UIEvent]:
        """处理用户输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return UIEvent("quit", {}, pygame.time.get_ticks())

            elif event.type == pygame.KEYDOWN:
                if event.key == _KEYS.K_ESCAPE:
                    return UIEvent("quit", {}, pygame.time.get_ticks())

                # 处理快捷键
                action = self.input_handler.handle_key_press(event.key)
                if action:
                    # 快捷键与点按钮等效：同一套点击音 + 动作音
                    self._play_action_feedback(action)
                    return UIEvent("action", {"action": action}, pygame.time.get_ticks())

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 按下即触发按压缩放动画（120ms 弹回），点击区域仍由布局决定
                pressed_button = self._button_at(event.pos)
                if pressed_button is not None:
                    pressed_button.trigger_press()

                # 处理鼠标点击
                action = self.input_handler.handle_mouse_click(event.pos)
                if action:
                    if pressed_button is None:
                        # 命中的是布局里的点击区但没有对应按钮实例时，音效照常
                        self._play_action_feedback(action)
                    return UIEvent("action", {"action": action}, pygame.time.get_ticks())

                # 处理按钮事件
                for button in self.buttons:
                    if button.handle_event(event):
                        break

            elif event.type == pygame.MOUSEMOTION:
                # 处理鼠标移动事件
                for button in self.buttons:
                    button.handle_event(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                # 松开鼠标：结束按压态（动画未播完则立即复原）
                released_button = self._button_at(event.pos)
                if released_button is not None:
                    released_button.release_press()
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
        self.sound.play("tide")
        self.show_toast(
            title="灵气潮汐预兆",
            sub_message=sub_message,
            tone=effect.get("tone", "buff")
        )
    def show_tide_consumed(self, label, tone, before, after):
        """显示灵气潮汐消耗提示"""
        self.sound.play("tide")
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

        keypad_enter = _KEYS.K_KP_ENTER

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return False

                elif event.type == pygame.KEYDOWN:
                    key = event.key
                    typed = (getattr(event, "unicode", "") or "").lower()

                    if (
                        key in (_KEYS.K_y, _KEYS.K_RETURN, keypad_enter)
                        or typed == "y"
                    ):
                        return True

                    if key in (_KEYS.K_n, _KEYS.K_ESCAPE) or typed == "n":
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
        self.effects.clear()
        self.sound.shutdown()
        pygame.quit()

    def is_running(self) -> bool:
        """检查界面是否正在运行"""
        return self.running