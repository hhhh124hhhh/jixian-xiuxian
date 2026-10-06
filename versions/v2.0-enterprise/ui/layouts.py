"""
UI布局配置 - 定义界面元素的位置和尺寸
"""

import pygame


# 仙侠视觉常量（国风青玉 / 黑玉配色）
# 说明：主题色集中在 themes.py，此处只放仙侠 UI 的局部风格常量，
# 由 pygame_renderer.py 直接引用，保证同一元素在各渲染路径上颜色一致。
JADE_BORDER = (127, 185, 168)         # #7FB9A8 青玉色细线
JADE_BORDER_BRIGHT = (167, 216, 200)  # 青玉高亮（悬停）
JADE_BORDER_DIM = (92, 126, 118)      # 青玉暗淡（禁用）
JADE_PLATE = (10, 20, 25, 190)        # 黑玉半透明底板
JADE_PLATE_HOVER = (20, 38, 44, 205)  # 黑玉半透明（悬停）
JADE_PLATE_PRESSED = (6, 14, 18, 200)  # 黑玉半透明（按下）
JADE_TITLE = (127, 209, 168)          # 玉绿色标题
JADE_SUBTEXT = (226, 232, 230)        # 灰白副文本
IVORY_TEXT = (243, 241, 233)          # 米白文字

# 顶部状态 HUD（黑玉半透明约 70% 不透明，保证白色云海背景上的文字清晰）
HUD_BACKDROP = (10, 20, 25, 180)
HUD_TEXT_PRIMARY = (240, 244, 240)
HUD_TEXT_SECONDARY = (198, 208, 204)
HUD_TEXT_HP = (255, 183, 183)
HUD_TEXT_MP = (160, 210, 255)

# 仙侠按钮样式标识（在布局里声明，由渲染器选择绘制风格）
BUTTON_STYLE_SOLID = "solid"          # 纯色矩形（默认）
BUTTON_STYLE_JADE_PLATE = "jade_plate"  # 黑玉玉牌 + 青玉细边

# toast 时序：200ms 淡入 -> 停留 2.5s -> 300ms 淡出
TOAST_FADE_IN_MS = 200
TOAST_HOLD_MS = 2500
TOAST_FADE_OUT_MS = 300
TOAST_TOTAL_MS = TOAST_FADE_IN_MS + TOAST_HOLD_MS + TOAST_FADE_OUT_MS


class Layout:
    """界面布局配置类"""

    # 屏幕基础设置
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 30

    # 区域高度定义
    HEADER_HEIGHT = 50
    INFO_HEIGHT = 120
    HUD_BACKDROP_HEIGHT = 100
    BUTTON_HEIGHT = 100
    LOG_HEIGHT = 320
    STATUS_HEIGHT = 40

    # 边距设置
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    PADDING = 10
    INFO_TOP_GAP = 12
    LOG_TOP_GAP = 8
    LOG_TEXT_PADDING_X = 12
    LOG_TEXT_PADDING_TOP = 8
    LOG_TEXT_PADDING_BOTTOM = 10
    SYSTEM_BUTTONS_X_OFFSET = -15

    # 圆形操作按钮（图标实际渲染尺寸，点击区域与视觉一致）
    ACTION_BUTTON_ICON_SIZE = 96
    ACTION_BUTTON_INSET_X = 12
    ACTION_BUTTON_SPACING = 150

    # 顶部通知槽（方案D：顶部通知槽 + 动态细横幅）
    # 通知槽固定夹在「顶部状态 HUD 底板」与「四个圆形操作按钮」之间，
    # 因此横幅永远不会压到圆形按钮（格式塔图底分离）。
    TOAST_SLOT_GAP_TOP = 6
    TOAST_SLOT_GAP_BOTTOM = 10
    TOAST_SLOT_HEIGHT = 50
    TOAST_BANNER_MIN_WIDTH = 400
    TOAST_BANNER_MAX_WIDTH = 500
    TOAST_BANNER_MIN_HEIGHT = 45
    TOAST_BANNER_MAX_HEIGHT = 60
    TOAST_BANNER_PADDING_X = 16
    TOAST_BANNER_TITLE_GAP = 12

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
            self.HEADER_HEIGHT + self.INFO_TOP_GAP,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.INFO_HEIGHT
        )

    @property
    def CHARACTER_INFO_BACKDROP_RECT(self) -> pygame.Rect:
        """角色状态文字底板区域（黑玉半透明约 70% 不透明）"""
        return pygame.Rect(
            self.INFO_RECT.x + 8,
            self.INFO_RECT.y,
            300,
            self.HUD_BACKDROP_HEIGHT
        )

    @property
    def TOAST_SLOT_RECT(self) -> pygame.Rect:
        """顶部通知槽：顶部状态HUD底板下方、四个圆形按钮上方的专用横幅槽"""
        backdrop = self.CHARACTER_INFO_BACKDROP_RECT
        width = min(
            self.TOAST_BANNER_MAX_WIDTH,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        )
        rect = pygame.Rect(
            0,
            backdrop.bottom + self.TOAST_SLOT_GAP_TOP,
            width,
            self.TOAST_SLOT_HEIGHT
        )
        rect.centerx = self.SCREEN_WIDTH // 2
        return rect

    @property
    def ACTION_BUTTON_ROW_RECT(self) -> pygame.Rect:
        """四个圆形操作按钮的实际占位区域（正方形，与视觉/点击区域一致）"""
        size = self.ACTION_BUTTON_ICON_SIZE
        row = pygame.Rect(0, 0, size, size)
        row.center = (
            self.BUTTON_AREA_RECT.centerx,
            self.BUTTON_AREA_RECT.centery
        )
        return row

    @property
    def BUTTON_AREA_RECT(self) -> pygame.Rect:
        """操作按钮区域（位于顶部通知槽下方，避开横幅）"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.TOAST_SLOT_RECT.bottom + self.TOAST_SLOT_GAP_BOTTOM,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.BUTTON_HEIGHT
        )

    @property
    def LOG_RECT(self) -> pygame.Rect:
        """游戏日志区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.BUTTON_AREA_RECT.bottom + self.LOG_TOP_GAP,
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

    @property
    def TIDE_EFFECT_RECT(self) -> pygame.Rect:
        """灵气潮汐待生效效果区域（状态栏右侧）"""
        status = self.STATUS_RECT
        width = 280
        return pygame.Rect(
            status.right - width,
            status.y + 4,
            width - 8,
            status.height - 8
        )

    # 按钮配置
    @property
    def ACTION_BUTTONS(self) -> list:
        """操作按钮配置"""
        row = self.ACTION_BUTTON_ROW_RECT
        start_x = self.BUTTON_AREA_RECT.x + self.ACTION_BUTTON_INSET_X
        configs = [
            ("打坐", "meditate", "消耗1HP，恢复仙力"),
            ("吃丹药", "consume_pill", "消耗1丹药，快速恢复"),
            ("修炼", "cultivate", "消耗20MP，大量经验"),
            ("等待", "wait", "消耗1HP，缓慢恢复"),
        ]

        return [
            {
                "name": name,
                "action": action,
                "rect": pygame.Rect(
                    start_x + self.ACTION_BUTTON_SPACING * index,
                    row.y,
                    row.width,
                    row.height
                ),
                "description": description
            }
            for index, (name, action, description) in enumerate(configs)
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
                "rect": pygame.Rect(self.STATUS_RECT.right - button_width - 10, self.STATUS_RECT.y + 5, button_width, button_height),
                "style": BUTTON_STYLE_JADE_PLATE
            },
            {
                "name": "重新开始",
                "action": "restart",
                "rect": pygame.Rect(self.STATUS_RECT.right - button_width * 2 - 20, self.STATUS_RECT.y + 5, button_width, button_height),
                "style": BUTTON_STYLE_JADE_PLATE
            }
        ]

    # 信息显示区域配置
    @property
    def CHARACTER_INFO_LINES(self) -> dict:
        """角色信息显示配置（行距按正文字高紧凑排布，全部落在 HUD 底板内）"""
        left = self.INFO_RECT.x + 10
        backdrop = self.CHARACTER_INFO_BACKDROP_RECT
        row_height = 24

        def row_y(offset: int) -> int:
            """第 offset 行的文字基线位置"""
            return min(
                backdrop.bottom - row_height - 2,
                self.INFO_RECT.y + 2 + offset
            )

        return {
            "name_line": {
                "pos": (left, row_y(0)),
                "template": "{name} | 资质: {talent} | {realm} ({exp}/{exp_threshold})"
            },
            "hp_line": {
                "pos": (left, row_y(24)),
                "template": "生命: {progress_bar} {current}/{max}",
                "bar_rect": pygame.Rect(self.INFO_RECT.x + 60, row_y(24) + 4, 200, 16)
            },
            "mp_line": {
                "pos": (left, row_y(48)),
                "template": "仙力: {progress_bar} {current}/{max}",
                "bar_rect": pygame.Rect(self.INFO_RECT.x + 60, row_y(48) + 4, 200, 16)
            },
            "stats_line": {
                "pos": (left, row_y(72)),
                "template": "丹药: {pills}颗 | 连续打坐: {streak}次"
            }
        }

    @property
    def LOG_CONFIG(self) -> dict:
        """日志显示配置"""
        return {
            "max_entries": 8,
            "line_height": 25,
            "start_pos": (self.LOG_RECT.x + self.LOG_TEXT_PADDING_X,
                          self.LOG_RECT.y + self.LOG_TEXT_PADDING_TOP),
            "max_width": self.LOG_RECT.width - 20
        }

    @property
    def STATUS_CONFIG(self) -> dict:
        """状态栏显示配置"""
        return {
            "recommendation_pos": (self.STATUS_RECT.x + 10, self.STATUS_RECT.y + 12),
            "recommendation_template": "推荐: {recommendation}"
        }

    def get_toast_banner_rect(self, content_width: int, content_height: int) -> pygame.Rect:
        """按内容算出通知横幅矩形：宽 400~500、高 45~60，在通知槽内居中"""
        slot = self.TOAST_SLOT_RECT
        max_width = min(self.TOAST_BANNER_MAX_WIDTH, slot.width)
        width = max(1, min(max_width, max(self.TOAST_BANNER_MIN_WIDTH, content_width)))
        height = max(1, min(
            self.TOAST_BANNER_MAX_HEIGHT,
            max(self.TOAST_BANNER_MIN_HEIGHT, content_height)
        ))
        rect = pygame.Rect(0, 0, width, height)
        rect.center = (slot.centerx, slot.centery)
        return rect

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