"""
音效管理 - 加载 assets/sfx 下的 wav 并按名字播放

鲁棒性要求（任何一条不满足都不能影响游戏跑起来）：
- 缺文件不崩：目录不存在、某个 wav 损坏都只跳过该音效，其余照常；
- 无音频设备不崩：headless / 无声卡环境下 mixer 初始化失败，整体转静音，
  play() 变成安全空操作；
- 不阻塞主循环：只做「预加载 + 异步播放」，背景音乐接口预留，资源没到位就静默返回。
"""

import os
from typing import Dict, List, Optional

import pygame

from .config import sound_config

SFX_EXTENSION = ".wav"

# 动作名 -> 音效名；None 表示该动作没有专属音效（仍保留按钮点击音）
ACTION_SFX: Dict[str, Optional[str]] = {
    "meditate": "meditate",
    "consume_pill": "pill",
    "cultivate": "cultivate",
    "wait": None,
    "restart": None,
    "settings": None,
}


class SoundManager:
    """音效播放器（一次加载，反复按名字播放）"""

    def __init__(self, sfx_dir: Optional[str] = None, config=None):
        self.config = config or sound_config
        self.sfx_dir = sfx_dir or self.config.resolve_sfx_dir()
        self.sounds: Dict[str, "pygame.mixer.Sound"] = {}
        self.failed: List[str] = []          # 加载失败的音效名，便于排查
        self.mixer_ready = False             # mixer 是否真的可用
        self.initialized = False
        self._last_played_ms: Dict[str, int] = {}
        self._music_path: Optional[str] = None
        self._music_loop = -1
        self._music_volume = self.config.MUSIC_VOLUME
        self._music_playing = False

    # ------------------------------------------------------------------ 初始化

    def initialize(self) -> bool:
        """初始化 mixer 并预加载音效；返回是否有音效真正可用

        失败只打印一行提示并静音降级，绝不抛异常。
        """
        if self.initialized:
            return self.mixer_ready

        self.initialized = True
        if not self.config.ENABLED:
            return False

        try:
            if not pygame.get_init():
                pygame.init()
        except Exception as e:  # pygame 本身起不来，后面 mixer 也用不了
            print(f"pygame 初始化失败，音效静音运行: {e}")
            return False

        try:
            # pygame.init() 内部已经试过一次 mixer，这里失败再按配置重试
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=self.config.FREQUENCY,
                    size=self.config.SIZE,
                    channels=self.config.CHANNELS,
                    buffer=self.config.BUFFER,
                )
            pygame.mixer.set_num_channels(self.config.MIXER_CHANNEL_COUNT)
            self.mixer_ready = pygame.mixer.get_init() is not None
        except Exception as e:
            self.mixer_ready = False
            print(f"音频初始化失败（音效静音运行）: {e}")
            return False

        if not self.mixer_ready:
            return False

        self.reload()
        if self._music_path:
            # mixer 之前不可用时音乐请求被挂起了，这里补一次
            self.play_music()
        return bool(self.sounds)

    def reload(self) -> int:
        """重新扫描音效目录并全部加载，返回成功加载的数量"""
        self.sounds.clear()
        self.failed.clear()

        if not self.mixer_ready:
            return 0

        try:
            filenames = sorted(os.listdir(self.sfx_dir))
        except OSError:
            print(f"音效目录不存在，跳过音效加载: {self.sfx_dir}")
            return 0

        for filename in filenames:
            if not filename.lower().endswith(SFX_EXTENSION):
                continue

            name = os.path.splitext(filename)[0]
            path = os.path.join(self.sfx_dir, filename)
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                self.failed.append(name)
                print(f"音效加载失败 {filename}: {e}")

        if not self.sounds:
            print(f"未在 {self.sfx_dir} 找到可用音效，游戏将以静音运行")
        return len(self.sounds)

    # ------------------------------------------------------------------ 播放

    def has(self, name: str) -> bool:
        """某个音效是否已加载"""
        return name in self.sounds

    def play(self, name: str, volume: Optional[float] = None) -> bool:
        """按名字播放音效；未知名字/静音/无设备时返回 False，不抛异常"""
        if not self.config.ENABLED or not self.mixer_ready:
            return False

        sound = self.sounds.get(name)
        if sound is None:
            return False

        now = pygame.time.get_ticks()
        last = self._last_played_ms.get(name)
        if last is not None and now - last < self.config.MIN_REPLAY_GAP_MS:
            return False
        self._last_played_ms[name] = now

        try:
            channel = sound.play()
            if channel is not None and volume is not None:
                channel.set_volume(max(0.0, min(1.0, float(volume))))
            return True
        except Exception:
            # 播放失败（设备被占用/音频格式问题）不应拖垮主循环
            return False

    def play_action(self, action_name: str, override: Optional[str] = None) -> bool:
        """按动作名播放音效

        override 用于同一动作的不同形态（如「修炼」按钮在渡劫窗口下播 tribulation）。
        """
        if override is not None:
            return self.play(override)

        name = ACTION_SFX.get(action_name)
        if not name:
            return False
        return self.play(name)

    def set_sfx_volume(self, volume: float) -> None:
        """调整音效音量（只影响之后播放的音效）"""
        self.config.SFX_VOLUME = max(0.0, min(1.0, float(volume)))

    # ------------------------------------------------------------ 背景音乐（预留）

    def play_music(self, path: Optional[str] = None, loop: int = -1,
                   volume: Optional[float] = None) -> bool:
        """播放背景音乐（预留接口：音乐文件还没回来时静默返回 False）

        传入 path 会记住这次请求，之后 mixer 可用时（initialize / play_music 再次调用）
        自动重试，不会阻塞主循环。
        """
        if path is not None:
            self._music_path = path
            self._music_loop = loop
            self._music_volume = (
                self.config.MUSIC_VOLUME if volume is None
                else max(0.0, min(1.0, float(volume)))
            )

        if not self._music_path:
            return False

        if self._music_playing:
            try:
                if pygame.mixer.music.get_busy():
                    return True
            except Exception:
                pass
            self._music_playing = False

        if not self.config.MUSIC_ENABLED or not self.mixer_ready:
            return False

        if not os.path.isfile(self._music_path):
            # 音乐资源还没到位，保持静音，下次调用再试
            return False

        try:
            pygame.mixer.music.load(self._music_path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(self._music_loop)
            self._music_playing = True
            return True
        except Exception as e:
            print(f"背景音乐播放失败 {self._music_path}: {e}")
            self._music_playing = False
            return False

    def stop_music(self) -> None:
        """停止背景音乐"""
        self._music_playing = False
        if not self.mixer_ready:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def is_music_playing(self) -> bool:
        """背景音乐是否正在播放"""
        if not self._music_playing or not self.mixer_ready:
            return False
        try:
            return bool(pygame.mixer.music.get_busy())
        except Exception:
            return False

    # ------------------------------------------------------------------ 清理

    def shutdown(self) -> None:
        """释放音效资源（不主动 pygame.mixer.quit，避免影响 pygame.quit 流程）"""
        self.stop_music()
        self.sounds.clear()
        self._last_played_ms.clear()
        self.mixer_ready = False

    def loaded_names(self) -> List[str]:
        """已加载的音效名（调试用）"""
        return sorted(self.sounds)
