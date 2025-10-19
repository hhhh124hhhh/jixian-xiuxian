"""
游戏界面抽象接口 - 实现UI与业务逻辑的解耦
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# 导入系统动作工厂
from actions.system_actions import SystemActionFactory


class ButtonType:
    """按钮类型常量"""
    GAME_ACTION = "game_action"    # 游戏动作按钮
    SYSTEM_ACTION = "system_action"  # 系统动作按钮


@dataclass
class UIEvent:
    """UI事件数据类"""
    event_type: str
    data: Dict[str, Any]
    timestamp: float = 0.0


@dataclass
class ButtonState:
    """按钮状态"""
    name: str
    action: str
    button_type: str = ButtonType.GAME_ACTION  # 按钮类型
    enabled: bool = True
    visible: bool = True
    tooltip: str = ""


@dataclass
class CharacterDisplayInfo:
    """角色显示信息"""
    name: str
    talent: int
    realm: str
    exp: int
    exp_threshold: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    pills: int
    meditation_streak: int
    hp_percentage: float
    mp_percentage: float
    exp_percentage: float


class GameInterface(ABC):
    """游戏界面抽象接口 - 便于后期替换为其他UI框架"""

    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化界面
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def render(self, game_state: Dict[str, Any]) -> None:
        """
        渲染游戏状态
        Args:
            game_state: 游戏状态数据
        """
        pass

    @abstractmethod
    def handle_input(self) -> Optional[UIEvent]:
        """
        处理用户输入
        Returns:
            UIEvent: 用户输入事件，如果没有输入则返回None
        """
        pass

    @abstractmethod
    def show_message(self, title: str, message: str, message_type: str = "info") -> None:
        """
        显示消息对话框
        Args:
            title: 消息标题
            message: 消息内容
            message_type: 消息类型 (info, warning, error, success)
        """
        pass

    @abstractmethod
    def get_character_name(self) -> Optional[str]:
        """
        获取角色名称输入
        Returns:
            str: 用户输入的角色名称，如果取消则返回None
        """
        pass

    @abstractmethod
    def show_confirmation(self, title: str, message: str) -> bool:
        """
        显示确认对话框
        Args:
            title: 确认标题
            message: 确认消息
        Returns:
            bool: 用户是否确认
        """
        pass

    @abstractmethod
    def update_display(self) -> None:
        """更新显示"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """关闭界面"""
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """检查界面是否正在运行"""
        pass


class GameStateRenderer:
    """游戏状态渲染器 - 负责将游戏状态转换为UI显示数据"""

    def format_character_info(self, character) -> CharacterDisplayInfo:
        """
        格式化角色信息为UI显示格式
        Args:
            character: 角色对象
        Returns:
            CharacterDisplayInfo: 格式化后的角色显示信息
        """
        status = character.get_status_summary()

        # 获取当前境界的经验阈值
        from models import RealmLevel
        from rules import game_rules
        realm_map = {
            "炼气期": RealmLevel.QI_REFINING,
            "筑基期": RealmLevel.FOUNDATION,
            "结丹期": RealmLevel.CORE_FORMATION,
            "元婴期": RealmLevel.NASCENT_SOUL,
            "化神期": RealmLevel.SPIRITUAL_TRANSFORMATION,
            "飞升": RealmLevel.ASCENSION
        }
        current_realm = realm_map.get(status["realm"], RealmLevel.QI_REFINING)
        exp_threshold = game_rules.get_realm_threshold(current_realm)

        return CharacterDisplayInfo(
            name=status["name"],
            talent=status["talent"],
            realm=status["realm"],
            exp=status["exp"],
            exp_threshold=exp_threshold,
            hp=status["hp"],
            max_hp=status["max_hp"],
            mp=status["mp"],
            max_mp=status["max_mp"],
            pills=status["pills"],
            meditation_streak=status["meditation_streak"],
            hp_percentage=status["hp"] / status["max_hp"],
            mp_percentage=status["mp"] / status["max_mp"],
            exp_percentage=status["exp_progress"] / 100.0
        )

    def format_action_buttons(self, character, actions: List) -> List[ButtonState]:
        """
        格式化操作按钮
        Args:
            character: 角色对象
            actions: 可用动作列表
        Returns:
            List[ButtonState]: 格式化后的按钮状态列表
        """
        buttons = []
        for action in actions:
            # 检查动作是否可执行
            can_execute = action.can_execute(character)

            button = ButtonState(
                name=action.name,
                action=action.__class__.__name__.lower().replace("action", ""),
                button_type=ButtonType.GAME_ACTION,
                enabled=can_execute and character.is_alive(),
                visible=True,
                tooltip=action.description if can_execute else "条件不足"
            )
            buttons.append(button)

        return buttons

    def format_system_action_buttons(self) -> List[ButtonState]:
        """
        格式化系统动作按钮
        Returns:
            List[ButtonState]: 格式化后的系统按钮状态列表
        """
        buttons = []
        system_actions = SystemActionFactory.get_all_system_actions()

        for action in system_actions:
            # 获取系统动作的中文名称用于显示
            display_names = {
                "restart": "重新开始",
                "settings": "设置",
                "save_game": "保存游戏",
                "load_game": "加载游戏"
            }

            display_name = display_names.get(action.name, action.name)

            button = ButtonState(
                name=display_name,
                action=action.name,
                button_type=ButtonType.SYSTEM_ACTION,
                enabled=True,  # 系统动作通常总是可用
                visible=True,
                tooltip=action.description
            )
            buttons.append(button)

        return buttons

    def is_system_action(self, action_name: str) -> bool:
        """
        检查是否为系统动作
        Args:
            action_name: 动作名称
        Returns:
            bool: 是否为系统动作
        """
        return SystemActionFactory.is_system_action(action_name)

    def format_game_log(self, log_entries: List[str], max_entries: int = 8) -> List[str]:
        """
        格式化游戏日志
        Args:
            log_entries: 日志条目列表
            max_entries: 最大显示条目数
        Returns:
            List[str]: 格式化后的日志条目
        """
        if not log_entries:
            return ["开始你的修仙之旅..."]

        # 获取最近的日志条目
        recent_entries = log_entries[-max_entries:] if len(log_entries) > max_entries else log_entries

        # 格式化每条日志
        formatted_entries = []
        for entry in recent_entries:
            if isinstance(entry, str):
                formatted_entries.append(f"> {entry}")
            else:
                formatted_entries.append(f"> {str(entry)}")

        return formatted_entries

    def format_status_recommendation(self, character) -> str:
        """
        格式化状态推荐信息
        Args:
            character: 角色对象
        Returns:
            str: 推荐信息
        """
        from rules import game_rules

        if not character.is_alive():
            return "修炼失败，请重新开始"

        # 使用规则引擎获取推荐
        recommendation = game_rules.get_action_recommendation(character)
        return recommendation

    def format_progress_bar(self, current: int, maximum: int, width: int = 10) -> str:
        """
        格式化进度条
        Args:
            current: 当前值
            maximum: 最大值
            width: 进度条宽度（字符数）
        Returns:
            str: 进度条字符串
        """
        if maximum <= 0:
            return "░" * width

        filled_blocks = int((current / maximum) * width)
        empty_blocks = width - filled_blocks

        return "█" * filled_blocks + "░" * empty_blocks

    def format_exp_display(self, character) -> str:
        """
        格式化经验显示
        Args:
            character: 角色对象
        Returns:
            str: 格式化的经验显示
        """
        status = character.get_status_summary()
        current_exp = status["exp"]
        realm = status["realm"]

        # 获取当前境界的经验阈值
        from models import RealmLevel
        realm_enum = None
        for realm_level in RealmLevel:
            if realm_level.value == realm:
                realm_enum = realm_level
                break

        if realm_enum:
            from rules import game_rules
            threshold = game_rules.get_realm_threshold(realm_enum)
            return f"{current_exp}/{threshold}"
        else:
            return f"{current_exp}/∞"


class InputHandler:
    """输入处理器抽象接口"""

    @abstractmethod
    def handle_mouse_click(self, position: tuple) -> Optional[str]:
        """
        处理鼠标点击
        Args:
            position: 鼠标位置 (x, y)
        Returns:
            str: 点击的动作名称，如果没有点击到有效区域则返回None
        """
        pass

    @abstractmethod
    def handle_key_press(self, key: int) -> Optional[str]:
        """
        处理键盘按键
        Args:
            key: 按键码
        Returns:
            str: 对应的动作名称，如果没有对应动作则返回None
        """
        pass

    @abstractmethod
    def register_shortcut(self, key: int, action: str):
        """
        注册快捷键
        Args:
            key: 按键码
            action: 动作名称
        """
        pass


class UIComponent(ABC):
    """UI组件抽象基类"""

    def __init__(self, position: tuple, size: tuple):
        self.position = position
        self.size = size
        self.visible = True
        self.enabled = True
        self.parent = None

    @property
    def rect(self):
        """获取组件矩形区域"""
        return (*self.position, *self.size)

    @abstractmethod
    def render(self, surface):
        """渲染组件"""
        pass

    @abstractmethod
    def handle_event(self, event) -> bool:
        """
        处理事件
        Args:
            event: 事件对象
        Returns:
            bool: 是否处理了该事件
        """
        pass

    def is_point_inside(self, point: tuple) -> bool:
        """检查点是否在组件内"""
        x, y = point
        px, py, pw, ph = self.rect
        return px <= x <= px + pw and py <= y <= py + ph