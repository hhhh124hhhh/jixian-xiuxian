"""
动效管理 - 突破圆环 / 经验跳字 / 走火脉冲

设计约束：
- 全部基于时间差（pygame.time.get_ticks）推进，不阻塞主循环；
- EffectManager.draw(screen) 每帧调用一次，过期动效自动清理；
- 无显示设备 / 渲染异常时不抛异常，静默跳过。
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import pygame


def ease_out(t: float) -> float:
    """三次缓出 easing，t in [0, 1] -> [0, 1]"""
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


class _BreakthroughRing:
    """突破：青玉扩散圆环（约 800ms）"""

    DURATION_MS = 800

    def __init__(self, center: Tuple[int, int], max_radius: int):
        self.center = (int(center[0]), int(center[1]))
        self.max_radius = max(8, int(max_radius))
        self.start_ms = pygame.time.get_ticks()

    def done(self, now_ms: int) -> bool:
        return now_ms - self.start_ms >= self.DURATION_MS

    def draw(self, screen, now_ms: int) -> None:
        t = (now_ms - self.start_ms) / self.DURATION_MS
        radius = int(self.max_radius * ease_out(t))
        alpha = int(200 * (1.0 - t))
        if radius <= 2 or alpha <= 0:
            return
        size = radius * 2 + 8
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        # 青玉色圆环：外圈 + 内圈淡线，营造扩散感
        pygame.draw.circle(surf, (110, 220, 195, alpha),
                           (size // 2, size // 2), radius, 4)
        inner = int(radius * 0.7)
        if inner > 2:
            pygame.draw.circle(surf, (110, 220, 195, alpha // 3),
                               (size // 2, size // 2), inner, 2)
        screen.blit(surf, (self.center[0] - size // 2, self.center[1] - size // 2))


class _ExpFloatText:
    """经验：+N 数字上浮淡出（约 300ms）"""

    DURATION_MS = 300

    def __init__(self, amount: int, anchor: Tuple[int, int], font):
        self.text = f"+{int(amount)}"
        self.anchor = (int(anchor[0]), int(anchor[1]))
        self.font = font
        self.start_ms = pygame.time.get_ticks()

    def done(self, now_ms: int) -> bool:
        return now_ms - self.start_ms >= self.DURATION_MS

    def draw(self, screen, now_ms: int) -> None:
        t = (now_ms - self.start_ms) / self.DURATION_MS
        dy = int(34 * ease_out(t))
        alpha = int(255 * (1.0 - t))
        if alpha <= 0:
            return
        try:
            text_surf = self.font.render(self.text, True, (255, 240, 180))
        except Exception:
            return
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect()
        rect.midbottom = (self.anchor[0], self.anchor[1] - dy)
        screen.blit(text_surf, rect)


class _DeviationPulse:
    """走火：屏幕边缘红色脉冲两次（约 600ms）"""

    DURATION_MS = 600
    PULSES = 2
    EDGE_WIDTH = 14

    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_size = (int(screen_size[0]), int(screen_size[1]))
        self.start_ms = pygame.time.get_ticks()

    def done(self, now_ms: int) -> bool:
        return now_ms - self.start_ms >= self.DURATION_MS

    def draw(self, screen, now_ms: int) -> None:
        t = (now_ms - self.start_ms) / self.DURATION_MS
        # 两次脉冲：正弦包络
        pulse = abs(math.sin(t * math.pi * self.PULSES))
        alpha = int(160 * pulse * (1.0 - t * 0.5))
        if alpha <= 0:
            return
        w, h = self.screen_size
        edge = self.EDGE_WIDTH
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (220, 40, 40, alpha)
        overlay.fill(color, (0, 0, w, edge))              # 上
        overlay.fill(color, (0, h - edge, w, edge))      # 下
        overlay.fill(color, (0, 0, edge, h))              # 左
        overlay.fill(color, (w - edge, 0, edge, h))      # 右
        screen.blit(overlay, (0, 0))


class EffectManager:
    """动效管理器：触发 / 每帧绘制 / 清理"""

    def __init__(self):
        self._active: List = []
        self._font = None

    # ---------------------------------------------------------- 触发接口

    def trigger_breakthrough(self, center: Tuple[int, int],
                             screen_size: Tuple[int, int]) -> None:
        """突破：以 center 为圆心扩散青玉圆环"""
        try:
            max_radius = int(min(screen_size) * 0.45)
            self._active.append(_BreakthroughRing(center, max_radius))
        except Exception:
            pass

    def trigger_exp_gain(self, amount: int, anchor: Tuple[int, int]) -> None:
        """经验：anchor 处上浮 +N"""
        if amount <= 0:
            return
        try:
            font = self._get_font()
            if font is None:
                return
            self._active.append(_ExpFloatText(amount, anchor, font))
        except Exception:
            pass

    def trigger_deviation(self, screen_size: Optional[Tuple[int, int]] = None) -> None:
        """走火：屏幕边缘红色脉冲"""
        try:
            if screen_size is None:
                surf = pygame.display.get_surface()
                if surf is None:
                    return
                screen_size = surf.get_size()
            self._active.append(_DeviationPulse(screen_size))
        except Exception:
            pass

    # ---------------------------------------------------------- 每帧绘制

    def draw(self, screen) -> None:
        """绘制所有进行中的动效，自动清理过期项；异常静默跳过"""
        if not self._active or screen is None:
            return
        try:
            now_ms = pygame.time.get_ticks()
        except Exception:
            return
        alive = []
        for fx in self._active:
            try:
                if fx.done(now_ms):
                    continue
                fx.draw(screen, now_ms)
                alive.append(fx)
            except Exception:
                continue
        self._active = alive

    def clear(self) -> None:
        """清空所有动效（重开局 / 切换场景时调用）"""
        self._active = []

    # ---------------------------------------------------------- 内部工具

    def _get_font(self):
        if self._font is None:
            try:
                # 优先用游戏自带字体管理，保持风格一致
                from .themes import font_manager
                self._font = font_manager.get_font("normal")
            except Exception:
                try:
                    self._font = pygame.font.SysFont(None, 24)
                except Exception:
                    self._font = None
        return self._font
