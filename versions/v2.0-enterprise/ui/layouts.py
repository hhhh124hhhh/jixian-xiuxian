"""
UI布局配置 - 定义界面元素的位置和尺寸
"""

from __future__ import annotations

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
# HUD 细进度条：深色轨道 + 饱和填充，在黑玉底板上依然清晰
HUD_BAR_TRACK = (26, 40, 44)
HUD_BAR_FILL_HP = (214, 74, 86)
HUD_BAR_FILL_MP = (74, 150, 226)
# 头像圆底（纯色圆 + 境界首字）
HUD_AVATAR_FILL = (18, 34, 39)

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
    HUD_BACKDROP_HEIGHT = 52
    BUTTON_HEIGHT = 100
    LOG_HEIGHT = 320
    STATUS_HEIGHT = 40

    # 顶部状态 HUD 细长条内部度量（800x600 下一行排开：头像+名字 | 细进度条 | 丹药 | 连击）
    HUD_CONTENT_PADDING_X = 14
    HUD_AVATAR_SIZE = 36
    HUD_AVATAR_TEXT_GAP = 10
    HUD_NAME_COLUMN_WIDTH = 140
    HUD_NAME_REALM_RESERVE = 64      # 名字列里给境界留的宽度
    HUD_BAR_LABEL_WIDTH = 16
    HUD_BAR_LABEL_GAP = 4
    HUD_BAR_WIDTH = 120
    HUD_BAR_HEIGHT = 9
    HUD_BAR_ROW_GAP = 5              # 生命/仙力两根细条之间的行距
    HUD_BAR_VALUE_GAP = 6
    HUD_VALUE_COLUMN_WIDTH = 58
    HUD_GROUP_GAP = 14               # 中部分组之间的横向间距
    HUD_PILLS_COLUMN_WIDTH = 48
    HUD_QUOTA_ROW_INSET = 11             # 配额小字距状态条底边的距离（第二行基线）
    HUD_RESERVED_RIGHT = 110         # 右侧留空（toast 通知槽区域），不放任何内容

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

    # 标题横幅（位于顶部状态条下方，避免被细长条切掉上沿装饰）
    TITLE_BANNER_WIDTH = 420
    TITLE_BANNER_HEIGHT = 140
    TITLE_BANNER_TOP_GAP = 2

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
    def SCREEN_RECT(self) -> "pygame.Rect":
        """整个屏幕区域"""
        return pygame.Rect(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    @property
    def HEADER_RECT(self) -> "pygame.Rect":
        """标题栏区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            10,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.HEADER_HEIGHT
        )

    @property
    def HUD_RECT(self) -> "pygame.Rect":
        """顶部通栏状态条：横贯屏幕顶部的黑玉半透明细长条"""
        return pygame.Rect(0, 0, self.SCREEN_WIDTH, self.HUD_BACKDROP_HEIGHT)

    @property
    def HUD_AVATAR_RECT(self) -> "pygame.Rect":
        """状态条左侧的圆形头像（垂直居中）"""
        size = self.HUD_AVATAR_SIZE
        return pygame.Rect(
            self.HUD_CONTENT_PADDING_X,
            (self.HUD_BACKDROP_HEIGHT - size) // 2,
            size,
            size
        )

    @property
    def INFO_RECT(self) -> "pygame.Rect":
        """角色信息区域（顶部状态条本体）"""
        return self.HUD_RECT

    @property
    def CHARACTER_INFO_BACKDROP_RECT(self) -> "pygame.Rect":
        """角色状态底板区域（顶部状态条本体）"""
        return self.HUD_RECT

    @property
    def TITLE_BANNER_RECT(self) -> "pygame.Rect":
        """标题横幅：贴在顶部状态条下方，水平居中"""
        rect = pygame.Rect(
            0,
            self.HUD_RECT.bottom + self.TITLE_BANNER_TOP_GAP,
            self.TITLE_BANNER_WIDTH,
            self.TITLE_BANNER_HEIGHT
        )
        rect.centerx = self.SCREEN_WIDTH // 2
        return rect

    @property
    def TOAST_SLOT_RECT(self) -> "pygame.Rect":
        """顶部通知槽：顶部状态条下方、四个圆形按钮上方的专用横幅槽"""
        width = min(
            self.TOAST_BANNER_MAX_WIDTH,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        )
        rect = pygame.Rect(
            0,
            self.HUD_RECT.bottom + self.TOAST_SLOT_GAP_TOP,
            width,
            self.TOAST_SLOT_HEIGHT
        )
        rect.centerx = self.SCREEN_WIDTH // 2
        return rect

    @property
    def ACTION_BUTTON_ROW_RECT(self) -> "pygame.Rect":
        """四个圆形操作按钮的实际占位区域（正方形，与视觉/点击区域一致）"""
        size = self.ACTION_BUTTON_ICON_SIZE
        row = pygame.Rect(0, 0, size, size)
        row.center = (
            self.BUTTON_AREA_RECT.centerx,
            self.BUTTON_AREA_RECT.centery
        )
        return row

    @property
    def BUTTON_AREA_RECT(self) -> "pygame.Rect":
        """操作按钮区域（位于顶部通知槽下方，避开横幅）"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.TOAST_SLOT_RECT.bottom + self.TOAST_SLOT_GAP_BOTTOM,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.BUTTON_HEIGHT
        )

    @property
    def LOG_RECT(self) -> "pygame.Rect":
        """游戏日志区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.BUTTON_AREA_RECT.bottom + self.LOG_TOP_GAP,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.LOG_HEIGHT
        )

    @property
    def STATUS_RECT(self) -> "pygame.Rect":
        """状态栏区域"""
        return pygame.Rect(
            self.MARGIN_LEFT,
            self.SCREEN_HEIGHT - self.STATUS_HEIGHT - 10,
            self.SCREEN_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            self.STATUS_HEIGHT
        )

    @property
    def TIDE_EFFECT_RECT(self) -> "pygame.Rect":
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
        """顶部状态条内容配置

        一行排开：左=圆形头像 + 「名字 · 境界」，中=生命/仙力细进度条 + 数值、
        丹药、连击小字，右侧预留 HUD_RESERVED_RIGHT 宽度给 toast 通知槽（不放内容）。
        资质、经验、打坐次数等旧明细已从状态条移除。
        """
        hud = self.HUD_RECT
        mid = hud.height // 2

        # 左：圆形头像 + 名字/境界
        avatar = self.HUD_AVATAR_RECT
        name_x = avatar.right + self.HUD_AVATAR_TEXT_GAP

        # 中：生命/仙力两根细进度条上下叠放，整块在状态条内垂直居中
        vitals_x = name_x + self.HUD_NAME_COLUMN_WIDTH
        bar_x = vitals_x + self.HUD_BAR_LABEL_WIDTH + self.HUD_BAR_LABEL_GAP
        block_height = self.HUD_BAR_HEIGHT * 2 + self.HUD_BAR_ROW_GAP
        block_top = (hud.height - block_height) // 2
        hp_bar_rect = pygame.Rect(bar_x, block_top, self.HUD_BAR_WIDTH, self.HUD_BAR_HEIGHT)
        mp_bar_rect = pygame.Rect(
            bar_x,
            block_top + self.HUD_BAR_HEIGHT + self.HUD_BAR_ROW_GAP,
            self.HUD_BAR_WIDTH,
            self.HUD_BAR_HEIGHT
        )

        value_x = hp_bar_rect.right + self.HUD_BAR_VALUE_GAP
        value_rect = pygame.Rect(value_x, 0, self.HUD_VALUE_COLUMN_WIDTH, hud.height)

        # 丹药、连击：一行排开，连击小字最右不越过预留的右侧空位
        pills_x = value_rect.right + self.HUD_GROUP_GAP
        combo_x = pills_x + self.HUD_PILLS_COLUMN_WIDTH + self.HUD_GROUP_GAP
        combo_width = self.SCREEN_WIDTH - self.HUD_RESERVED_RIGHT - combo_x

        return {
            "avatar": {
                "pos": avatar.topleft,
                "rect": avatar,
                "template": "{realm}"
            },
            "name_line": {
                "pos": (name_x, mid),
                "template": "{name} · {realm}",
                "max_width": self.HUD_NAME_COLUMN_WIDTH
            },
            "hp_line": {
                "pos": (vitals_x, mid),
                "template": "{current}/{max}",
                "label": "命",
                "bar_rect": hp_bar_rect,
                "value_rect": value_rect
            },
            "mp_line": {
                "pos": (vitals_x, mid),
                "template": "{current}/{max}",
                "label": "仙",
                "bar_rect": mp_bar_rect,
                "value_rect": value_rect
            },
            "stats_line": {
                "pos": (pills_x, mid),
                "template": "丹药 {pills}",
                "max_width": self.HUD_PILLS_COLUMN_WIDTH
            },
            "combo_line": {
                "pos": (combo_x, mid),
                "template": "{combo}",
                "max_width": combo_width
            },
            # 境界配额（玩法 v2）：丹药/修炼额度压在丹药数字下方一行，
            # 复用状态条右半区的第二行空白，不改变原有列宽与视觉层级
            "quota_line": {
                "pos": (pills_x, hud.height - self.HUD_QUOTA_ROW_INSET),
                "template": "{quota}",
                "max_width": (
                    self.SCREEN_WIDTH - self.HUD_CONTENT_PADDING_X - pills_x
                )
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

    def get_toast_banner_rect(self, content_width: int, content_height: int) -> "pygame.Rect":
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