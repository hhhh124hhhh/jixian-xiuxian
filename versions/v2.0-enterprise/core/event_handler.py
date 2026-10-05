"""
事件处理器 - 管理游戏事件和回调
"""

from typing import Dict, Any, Callable, List, Optional
from enum import Enum
import time
from dataclasses import dataclass


class EventType(Enum):
    """事件类型枚举"""
    # 游戏生命周期事件
    GAME_START = "game_start"
    GAME_OVER = "game_over"
    RESET_GAME = "reset_game"

    # 动作相关事件
    ACTION_EXECUTED = "action_executed"

    # 角色相关事件
    LEVEL_UP = "level_up"
    CHARACTER_DIED = "character_died"

    # 游戏进度事件
    PILL_OBTAINED = "pill_obtained"
    MEDITATION_STREAK = "meditation_streak"
    QI_TIDE_TRIGGERED = "qi_tide_triggered"
    QI_TIDE_CONSUMED = "qi_tide_consumed"

    # 数据管理事件
    SAVE_GAME = "save_game"
    LOAD_GAME = "load_game"

    # 系统功能事件
    RESTART_REQUESTED = "restart_requested"
    SETTINGS_REQUESTED = "settings_requested"

    # 错误和状态事件
    ERROR_OCCURRED = "error_occurred"


@dataclass
class GameEvent:
    """游戏事件数据类"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: float
    source: str = "system"

    def __post_init__(self):
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)


class EventListener:
    """事件监听器"""

    def __init__(self, event_type: EventType, callback: Callable, priority: int = 0):
        self.event_type = event_type
        self.callback = callback
        self.priority = priority
        self.enabled = True

    def handle_event(self, event: GameEvent) -> bool:
        """
        处理事件
        Args:
            event: 游戏事件
        Returns:
            bool: 是否成功处理
        """
        if not self.enabled:
            return False

        try:
            self.callback(event)
            return True
        except Exception as e:
            print(f"事件处理失败: {e}")
            return False


class EventHandler:
    """游戏事件处理器"""

    def __init__(self):
        self.listeners: Dict[EventType, List[EventListener]] = {}
        self.event_history: List[GameEvent] = []
        self.max_history = 100
        self.enabled = True

    def register_listener(self, event_type: EventType, callback: Callable, priority: int = 0) -> str:
        """
        注册事件监听器
        Args:
            event_type: 事件类型
            callback: 回调函数
            priority: 优先级（数字越大优先级越高）
        Returns:
            str: 监听器ID
        """
        listener = EventListener(event_type, callback, priority)

        if event_type not in self.listeners:
            self.listeners[event_type] = []

        self.listeners[event_type].append(listener)

        # 按优先级排序（高优先级在前）
        self.listeners[event_type].sort(key=lambda x: x.priority, reverse=True)

        return f"listener_{id(listener)}"

    def unregister_listener(self, event_type: EventType, listener_id: str) -> bool:
        """
        取消注册监听器
        Args:
            event_type: 事件类型
            listener_id: 监听器ID
        Returns:
            bool: 是否成功取消注册
        """
        if event_type in self.listeners:
            self.listeners[event_type] = [
                listener for listener in self.listeners[event_type]
                if f"listener_{id(listener)}" != listener_id
            ]
            return True
        return False

    def dispatch_event(self, event_type: EventType, data: Dict[str, Any], source: str = "system") -> bool:
        """
        分发事件
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        Returns:
            bool: 是否有监听器处理了事件
        """
        if not self.enabled:
            return False

        event = GameEvent(
            event_type=event_type,
            data=data.copy(),
            timestamp=time.time(),
            source=source
        )

        # 添加到历史记录
        self._add_to_history(event)

        # 通知监听器
        handled = False
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                if listener.handle_event(event):
                    handled = True

        return handled

    def _add_to_history(self, event: GameEvent):
        """添加事件到历史记录"""
        self.event_history.append(event)

        # 限制历史记录大小
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

    def get_event_history(self, event_type: EventType = None, limit: int = 10) -> List[GameEvent]:
        """
        获取事件历史
        Args:
            event_type: 筛选特定事件类型
            limit: 返回数量限制
        Returns:
            List[GameEvent]: 事件列表
        """
        events = self.event_history

        if event_type:
            events = [event for event in events if event.event_type == event_type]

        # 返回最近的事件
        return events[-limit:] if len(events) > limit else events

    def clear_history(self):
        """清空事件历史"""
        self.event_history.clear()

    def enable(self):
        """启用事件处理器"""
        self.enabled = True

    def disable(self):
        """禁用事件处理器"""
        self.enabled = False

    def get_listener_count(self, event_type: EventType = None) -> int:
        """
        获取监听器数量
        Args:
            event_type: 特定事件类型，None表示总数
        Returns:
            int: 监听器数量
        """
        if event_type:
            return len(self.listeners.get(event_type, []))
        else:
            return sum(len(listeners) for listeners in self.listeners.values())

    def remove_all_listeners(self, event_type: EventType = None):
        """
        移除所有监听器
        Args:
            event_type: 特定事件类型，None表示所有类型
        """
        if event_type:
            self.listeners[event_type].clear()
        else:
            self.listeners.clear()


class GameEventLogger:
    """游戏事件日志记录器"""

    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.register_logging_listeners()

    def register_logging_listeners(self):
        """注册日志记录监听器"""
        # 为所有事件类型注册日志记录
        for event_type in EventType:
            self.event_handler.register_listener(
                event_type,
                self._log_event,
                priority=-100  # 低优先级，在其他处理之后记录
            )

    def _log_event(self, event: GameEvent):
        """记录事件到日志"""
        timestamp = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        message = f"[{timestamp}] {event.event_type.value}: {event.data}"
        print(message)


class AchievementTracker:
    """成就跟踪器"""

    def __init__(self, event_handler: EventHandler):
        self.event_handler = event_handler
        self.achievements: Dict[str, bool] = {}
        self.register_achievement_listeners()

    def register_achievement_listeners(self):
        """注册成就监听器"""
        self.event_handler.register_listener(EventType.LEVEL_UP, self._on_level_up)
        self.event_handler.register_listener(EventType.MEDITATION_STREAK, self._on_meditation_streak)
        self.event_handler.register_listener(EventType.CHARACTER_DIED, self._on_character_died)
        self.event_handler.register_listener(EventType.PILL_OBTAINED, self._on_pill_obtained)
        self.event_handler.register_listener(EventType.ACTION_EXECUTED, self._on_action_executed)
        self.event_handler.register_listener(EventType.QI_TIDE_TRIGGERED, self._on_tide_triggered)

    def _on_level_up(self, event: GameEvent):
        """处理等级提升事件"""
        new_level = event.data.get("new_level")
        if new_level == "筑基期":
            self.unlock_achievement("first_breakthrough", "首次突破")

    def _on_meditation_streak(self, event: GameEvent):
        """处理连续打坐事件"""
        streak = event.data.get("streak", 0)
        if streak >= 5:
            self.unlock_achievement("meditation_beginner", "打坐初学者")
        if streak >= 10:
            self.unlock_achievement("meditation_master", "打坐大师")

    def _on_character_died(self, event: GameEvent):
        """处理角色死亡事件"""
        self.unlock_achievement("first_death", "初次死亡")

    def _on_pill_obtained(self, event: GameEvent):
        """处理获得丹药事件"""
        amount = event.data.get("amount", 0)
        if amount >= 1:
            self.unlock_achievement("first_pill", "获得丹药")

    def _on_action_executed(self, event: GameEvent):
        """处理动作执行事件"""
        action = event.data.get("action", "")
        character_state = event.data.get("character_state", {})
        total_actions = character_state.get("total_actions", 0)

        # 首次动作成就
        if total_actions == 1:
            self.unlock_achievement("first_action", "开始修炼")

        # 动作次数成就
        if total_actions >= 10:
            self.unlock_achievement("persistent_cultivator", "坚持修炼")

        # 特定动作成就
        if action == "cultivate" and total_actions >= 5:
            self.unlock_achievement("cultivation_enthusiast", "修炼爱好者")

    def _on_tide_triggered(self, event: GameEvent):
        """处理灵气潮汐触发事件"""
        total = event.data["total"]
        if total >= 1:
            self.unlock_achievement("tide_first", "初感潮汐")
        if total >= 10:
            self.unlock_achievement("tide_veteran", "潮汐老手")

    def unlock_achievement(self, achievement_id: str, description: str):
        """解锁成就"""
        if not self.achievements.get(achievement_id, False):
            self.achievements[achievement_id] = True
            print(f"🏆 成就解锁: {description}")

    def get_achievements(self) -> Dict[str, bool]:
        """获取所有成就状态"""
        return self.achievements.copy()


# 全局事件处理器实例
event_handler = EventHandler()
