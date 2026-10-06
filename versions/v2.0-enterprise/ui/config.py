"""
UI 配置 - 音效与动效的开关和参数

集中管理，避免魔法数字散落在渲染代码里。
动效/音效默认开启，可配置关闭（无障碍或性能需求）。
"""

import os


class SoundConfig:
    """音效配置"""

    ENABLED = True          # 总开关：False 则 SoundManager 直接静音
    MUSIC_ENABLED = True    # 背景音乐开关
    SFX_VOLUME = 0.8        # 音效音量 0.0-1.0
    MUSIC_VOLUME = 0.4      # 背景音乐音量 0.0-1.0
    MIN_REPLAY_GAP_MS = 60  # 同一音效最小重播间隔（防连点爆音）

    # pygame.mixer 初始化参数
    FREQUENCY = 44100
    SIZE = -16
    CHANNELS = 2
    BUFFER = 512
    MIXER_CHANNEL_COUNT = 16

    def resolve_sfx_dir(self) -> str:
        """音效目录：版本根目录下的 assets/sfx"""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "assets", "sfx")


class EffectsConfig:
    """动效配置"""

    ENABLED = True  # 总开关：False 则跳过全部动效（按钮缩放/圆环/跳字/脉冲）

    # 按钮按下缩放：120ms 内缩到 0.95 后回弹
    BUTTON_PRESS_DURATION_MS = 120
    BUTTON_PRESS_MIN_SCALE = 0.95

    # 突破：青玉扩散圆环约 800ms
    BREAKTHROUGH_DURATION_MS = 800
    # 经验：数字上浮淡出约 300ms
    EXP_POP_DURATION_MS = 300
    # 走火：屏幕边缘红色脉冲两次约 600ms
    DEVIATION_DURATION_MS = 600

    def button_press_duration_ms(self) -> int:
        return self.BUTTON_PRESS_DURATION_MS

    def button_press_min_scale(self) -> float:
        return self.BUTTON_PRESS_MIN_SCALE


sound_config = SoundConfig()
effects_config = EffectsConfig()
