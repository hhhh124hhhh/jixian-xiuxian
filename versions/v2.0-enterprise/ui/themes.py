"""
UI主题配置 - 定义颜色、字体和样式
"""

from typing import Dict, Tuple
import pygame


class Theme:
    """默认主题配置"""

    # 基础颜色
    BACKGROUND = (245, 245, 245)           # 背景色
    PANEL_BACKGROUND = (255, 255, 255)     # 面板背景
    BORDER = (200, 200, 200)               # 边框颜色
    TEXT_PRIMARY = (33, 37, 41)            # 主要文字颜色
    TEXT_SECONDARY = (108, 117, 125)       # 次要文字颜色
    TEXT_MUTED = (173, 181, 189)           # 暗淡文字颜色

    # 状态颜色
    HP_COLOR = (220, 53, 69)               # 生命值颜色 (红色)
    HP_BACKGROUND = (248, 215, 218)        # 生命值背景
    MP_COLOR = (0, 123, 255)               # 仙力值颜色 (蓝色)
    MP_BACKGROUND = (204, 229, 255)        # 仙力值背景
    EXP_COLOR = (40, 167, 69)              # 经验值颜色 (绿色)
    EXP_BACKGROUND = (206, 235, 203)       # 经验值背景

    # 按钮颜色
    BUTTON_NORMAL = (0, 123, 255)          # 按钮正常状态
    BUTTON_HOVER = (0, 105, 217)           # 按钮悬停状态
    BUTTON_PRESSED = (0, 86, 179)          # 按钮按下状态
    BUTTON_DISABLED = (200, 200, 200)      # 按钮禁用状态
    BUTTON_TEXT = (255, 255, 255)          # 按钮文字颜色

    # 操作按钮特定颜色
    ACTION_BUTTONS = {
        "打坐": (52, 58, 64),              # 深灰色
        "吃丹药": (25, 135, 84),           # 绿色
        "修炼": (220, 53, 69),             # 红色
        "等待": (108, 117, 125),           # 灰色
    }

    # 状态颜色映射
    STATUS_COLORS = {
        "success": (40, 167, 69),          # 成功 - 绿色
        "warning": (255, 193, 7),          # 警告 - 黄色
        "danger": (220, 53, 69),           # 危险 - 红色
        "info": (0, 123, 255),             # 信息 - 蓝色
        "light": (248, 249, 250),          # 浅色
        "dark": (52, 58, 64),              # 深色
    }

    # 字体配置
    FONT_NAME = "simhei"                   # 字体名称
    FONT_SIZES = {
        "small": 14,                       # 小字体
        "normal": 16,                      # 正常字体
        "large": 20,                       # 大字体
        "title": 24,                       # 标题字体
    }

    # 渐变配置
    def get_gradient_color(self, start_color: Tuple[int, int, int],
                          end_color: Tuple[int, int, int],
                          position: float) -> Tuple[int, int, int]:
        """获取渐变颜色"""
        position = max(0.0, min(1.0, position))

        r = int(start_color[0] + (end_color[0] - start_color[0]) * position)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * position)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * position)

        return (r, g, b)

    def get_hp_color(self, hp_percentage: float) -> Tuple[int, int, int]:
        """根据生命值百分比获取颜色"""
        if hp_percentage > 0.6:
            return self.HP_COLOR
        elif hp_percentage > 0.3:
            return (255, 193, 7)  # 黄色警告
        else:
            return (200, 35, 51)  # 深红色危险

    def get_button_color(self, button_name: str, state: str = "normal") -> Tuple[int, int, int]:
        """获取按钮颜色"""
        base_color = self.ACTION_BUTTONS.get(button_name, self.BUTTON_NORMAL)

        if state == "hover":
            return tuple(min(255, c + 20) for c in base_color)
        elif state == "pressed":
            return tuple(max(0, c - 20) for c in base_color)
        elif state == "disabled":
            return self.BUTTON_DISABLED
        else:
            return base_color


class DarkTheme(Theme):
    """深色主题"""

    # 重定义颜色为深色版本
    BACKGROUND = (33, 37, 41)
    PANEL_BACKGROUND = (52, 58, 64)
    BORDER = (108, 117, 125)
    TEXT_PRIMARY = (255, 255, 255)
    TEXT_SECONDARY = (206, 212, 218)
    TEXT_MUTED = (173, 181, 189)

    HP_COLOR = (255, 107, 107)
    MP_COLOR = (91, 192, 222)
    EXP_COLOR = (92, 184, 92)

    BUTTON_NORMAL = (91, 192, 222)
    BUTTON_HOVER = (121, 202, 222)
    BUTTON_PRESSED = (71, 182, 212)


class ThemeManager:
    """主题管理器"""

    def __init__(self):
        self.themes = {
            "default": Theme(),
            "dark": DarkTheme(),
        }
        self.current_theme = "default"

    def get_theme(self, theme_name: str = None) -> Theme:
        """获取主题"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["default"])

    def set_theme(self, theme_name: str):
        """设置当前主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name

    def get_available_themes(self) -> list:
        """获取可用主题列表"""
        return list(self.themes.keys())


class FontManager:
    """字体管理器"""

    def __init__(self):
        self.fonts = {}
        self.theme = Theme()

    def get_font(self, size_name: str = "normal", font_name: str = None) -> pygame.font.Font:
        """获取字体"""
        font_name = font_name or self.theme.FONT_NAME
        size = self.theme.FONT_SIZES.get(size_name, self.theme.FONT_SIZES["normal"])

        key = f"{font_name}_{size}"
        if key not in self.fonts:
            try:
                # 检查pygame是否已初始化
                if not pygame.get_init():
                    pygame.init()
                self.fonts[key] = pygame.font.SysFont(font_name, size)
            except:
                # 如果指定字体不可用，使用默认字体
                try:
                    if not pygame.get_init():
                        pygame.init()
                    self.fonts[key] = pygame.font.Font(None, size)
                except:
                    # 如果pygame仍未初始化，创建一个简单的字体对象
                    class DummyFont:
                        def __init__(self, size):
                            self.size = size
                        def render(self, text, antialias, color):
                            # 返回一个简单的surface
                            import pygame
                            if not pygame.get_init():
                                pygame.init()
                            return pygame.font.Font(None, size).render(text, antialias, color)
                        def get_size(self, text):
                            return (len(text) * self.size // 2, self.size)
                    self.fonts[key] = DummyFont(size)

        return self.fonts[key]

    def get_font_with_size(self, size: int, font_name: str = None) -> pygame.font.Font:
        """获取指定大小的字体"""
        font_name = font_name or self.theme.FONT_NAME

        key = f"{font_name}_{size}"
        if key not in self.fonts:
            try:
                # 检查pygame是否已初始化
                if not pygame.get_init():
                    pygame.init()
                self.fonts[key] = pygame.font.SysFont(font_name, size)
            except:
                try:
                    if not pygame.get_init():
                        pygame.init()
                    self.fonts[key] = pygame.font.Font(None, size)
                except:
                    # 如果pygame仍未初始化，创建一个简单的字体对象
                    class DummyFont:
                        def __init__(self, size):
                            self.size = size
                        def render(self, text, antialias, color):
                            import pygame
                            if not pygame.get_init():
                                pygame.init()
                            return pygame.font.Font(None, size).render(text, antialias, color)
                        def get_size(self, text):
                            return (len(text) * self.size // 2, self.size)
                    self.fonts[key] = DummyFont(size)

        return self.fonts[key]


# 全局实例
theme_manager = ThemeManager()
font_manager = FontManager()