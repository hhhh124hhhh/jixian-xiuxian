"""
UI布局配置 - 定义界面元素的位置和尺寸
"""

import pygame


class Layout:
    """界面布局配置类"""

    # 屏幕基础设置
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 30

    # 区域高度定义
    HEADER_HEIGHT = 50
    INFO_HEIGHT = 120
    BUTTON_HEIGHT = 100
    LOG_HEIGHT = 320
    STATUS_HEIGHT = 40

    # 边距设置
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    PADDING = 10

    # 区域位置计算
    @property
    def SCREEN_RECT(self) -> pygame.Rect:
        """整个屏幕区域"""
        return pygame.Rect(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    @property
    def HEADER_RECT(self) -> pygame.Rect:
        """标题栏区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            10,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.HEADER_HEIGHT
        )

    @property
    def INFO_RECT(self) -> pygame.Rect:
        """角色信息区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.HEADER_HEIGHT + 20,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.INFO_HEIGHT
        )

    @property
    def BUTTON_AREA_RECT(self) -> pygame.Rect:
        """操作按钮区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.HEADER_HEIGHT + self.INFO_HEIGHT + 30,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.BUTTON_HEIGHT
        )

    @property
    def LOG_RECT(self) -> pygame.Rect:
        """游戏日志区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.HEADER_HEIGHT + self.INFO_HEIGHT + self.BUTTON_HEIGHT + 40,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.LOG_HEIGHT
        )

    @property
    def STATUS_RECT(self) -> pygame.Rect:
        """状态栏区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.SCREEN_HEIGHT - self.STATUS_HEIGHT - 10,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.STATUS_HEIGHT
        )

    # 按钮配置
    @property
    def ACTION_BUTTONS(self) -> list:
        """操作按钮配置"""
        button_width = 120
        button_height = 40
        button_spacing = 30
        start_x = self.BUTTON_AREA_RECT.x

        return [
            {
                "name": "打坐",
                "action": "meditate",
                "rect": pygame.Rect(start_x, self.BUTTON_AREA_RECT.y + 10, button_width, button_height),
                "description": "消耗1HP，恢复仙力"
            },
            {
                "name": "吃丹药",
                "action": "consume_pill",
                "rect": pygame.Rect(start_x + button_width + button_spacing, self.BUTTON_AREA_RECT.y + 10, button_width, button_height),
                "description": "消耗1丹药，快速恢复"
            },
            {
                "name": "修炼",
                "action": "cultivate",
                "rect": pygame.Rect(start_x + (button_width + button_spacing) * 2, self.BUTTON_AREA_RECT.y + 10, button_width, button_height),
                "description": "消耗20MP，大量经验"
            },
            {
                "name": "等待",
                "action": "wait",
                "rect": pygame.Rect(start_x + (button_width + button_spacing) * 3, self.BUTTON_AREA_RECT.y + 10, button_width, button_height),
                "description": "消耗1HP，缓慢恢复"
            }
        ]

    @property
    def STATUS_BUTTONS(self) -> list:
        """状态栏按钮配置"""
        button_width = 80
        button_height = 30

        return [
            {
                "name": "设置",
                "action": "settings",
                "rect": pygame.Rect(self.STATUS_RECT.right - button_width - 10, self.STATUS_RECT.y + 5, button_width, button_height)
            },
            {
                "name": "重新开始",
                "action": "restart",
                "rect": pygame.Rect(self.STATUS_RECT.right - button_width * 2 - 20, self.STATUS_RECT.y + 5, button_width, button_height)
            }
        ]

    # 信息显示区域配置
    @property
    def CHARACTER_INFO_LINES(self) -> dict:
        """角色信息显示配置"""
        return {
            "name_line": {
                "pos": (self.INFO_RECT.x + 10, self.INFO_RECT.y + 10),
                "template": "{name} | 资质: {talent} | {realm} ({exp}/{exp_threshold})"
            },
            "hp_line": {
                "pos": (self.INFO_RECT.x + 10, self.INFO_RECT.y + 35),
                "template": "生命: {progress_bar} {current}/{max}",
                "bar_rect": pygame.Rect(self.INFO_RECT.x + 60, self.INFO_RECT.y + 38, 200, 16)
            },
            "mp_line": {
                "pos": (self.INFO_RECT.x + 10, self.INFO_RECT.y + 60),
                "template": "仙力: {progress_bar} {current}/{max}",
                "bar_rect": pygame.Rect(self.INFO_RECT.x + 60, self.INFO_RECT.y + 63, 200, 16)
            },
            "stats_line": {
                "pos": (self.INFO_RECT.x + 10, self.INFO_RECT.y + 85),
                "template": "丹药: {pills}颗 | 连续打坐: {streak}次"
            }
        }

    @property
    def LOG_CONFIG(self) -> dict:
        """日志显示配置"""
        return {
            "max_entries": 8,
            "line_height": 25,
            "start_pos": (self.LOG_RECT.x + 10, self.LOG_RECT.y + 10),
            "max_width": self.LOG_RECT.width - 20
        }

    @property
    def STATUS_CONFIG(self) -> dict:
        """状态栏显示配置"""
        return {
            "recommendation_pos": (self.STATUS_RECT.x + 10, self.STATUS_RECT.y + 12),
            "recommendation_template": "推荐: {recommendation}"
        }

    def get_progress_bar_width(self, current: int, maximum: int, bar_width: int = 200) -> int:
        """计算进度条宽度"""
        if maximum <= 0:
            return 0
        return int((current / maximum) * bar_width)

    def get_progress_bar_blocks(self, current: int, maximum: int, total_blocks: int = 10) -> str:
        """生成进度条字符"""
        if maximum <= 0:
            return "░" * total_blocks

        filled_blocks = int((current / maximum) * total_blocks)
        empty_blocks = total_blocks - filled_blocks

        return "█" * filled_blocks + "░" * empty_blocks


class ResponsiveLayout(Layout):
    """响应式布局 - 支持不同屏幕尺寸"""

    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height

        # 根据屏幕尺寸调整布局
        if screen_width < 800:
            self.MARGIN_LEFT = 20
            self.MARGIN_RIGHT = 20
            self.BUTTON_HEIGHT = 120  # 小屏幕下按钮区域更大

        # 重新计算区域
        self._recalculate_areas()

    def _recalculate_areas(self):
        """重新计算区域位置"""
        # 这里可以根据屏幕尺寸动态调整布局参数
        pass


# 默认布局实例
default_layout = Layout()