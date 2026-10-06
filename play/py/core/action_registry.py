#!/usr/bin/env python3
"""
动作注册机制
提供统一的动作注册、管理和获取功能
"""

from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from models import CharacterStats, GameLog


@dataclass
class ActionInfo:
    """动作信息"""
    action_id: str
    display_name: str
    description: str
    category: str = "game"  # game, system, etc.
    enabled: bool = True
    hotkey: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0


class ActionRegistry:
    """动作注册中心"""

    def __init__(self):
        self.actions: Dict[str, Any] = {}  # action_id -> action_instance
        self.action_info: Dict[str, ActionInfo] = {}  # action_id -> action_info
        self.categories: Dict[str, List[str]] = {}  # category -> [action_ids]

    def register_action(self, action_id: str, action_class,
                       display_name: str = None, description: str = None,
                       category: str = "game", hotkey: str = None,
                       icon: str = None, sort_order: int = 0, enabled: bool = True) -> bool:
        """
        注册动作

        Args:
            action_id: 动作唯一标识符
            action_class: 动作类
            display_name: 显示名称
            description: 描述信息
            category: 动作分类
            hotkey: 快捷键
            icon: 图标
            sort_order: 排序权重
            enabled: 是否启用

        Returns:
            bool: 注册是否成功
        """
        try:
            # 创建动作实例
            action_instance = action_class()

            # 使用动作类的名称和描述作为默认值
            if display_name is None:
                display_name = action_instance.name
            if description is None:
                description = action_instance.description

            # 创建动作信息
            info = ActionInfo(
                action_id=action_id,
                display_name=display_name,
                description=description,
                category=category,
                hotkey=hotkey,
                icon=icon,
                sort_order=sort_order,
                enabled=enabled
            )

            # 注册动作和信息
            self.actions[action_id] = action_instance
            self.action_info[action_id] = info

            # 更新分类
            if category not in self.categories:
                self.categories[category] = []
            if action_id not in self.categories[category]:
                self.categories[category].append(action_id)

            return True

        except Exception as e:
            print(f"注册动作 {action_id} 失败: {e}")
            return False

    def unregister_action(self, action_id: str) -> bool:
        """
        取消注册动作

        Args:
            action_id: 动作标识符

        Returns:
            bool: 取消注册是否成功
        """
        if action_id in self.actions:
            # 获取分类信息
            info = self.action_info.get(action_id)
            category = info.category if info else "unknown"

            # 移除动作
            del self.actions[action_id]
            del self.action_info[action_id]

            # 从分类中移除
            if category in self.categories and action_id in self.categories[category]:
                self.categories[category].remove(action_id)

            return True
        return False

    def get_action(self, action_id: str) -> Optional[Any]:
        """
        获取动作实例

        Args:
            action_id: 动作标识符

        Returns:
            动作实例或None
        """
        return self.actions.get(action_id)

    def get_action_info(self, action_id: str) -> Optional[ActionInfo]:
        """
        获取动作信息

        Args:
            action_id: 动作标识符

        Returns:
            动作信息或None
        """
        return self.action_info.get(action_id)

    def get_actions_by_category(self, category: str = "game") -> List[str]:
        """
        获取指定分类的动作ID列表

        Args:
            category: 动作分类

        Returns:
            动作ID列表
        """
        action_ids = self.categories.get(category, [])

        # 按sort_order排序
        action_ids.sort(key=lambda x: self.action_info.get(x, ActionInfo("", "", "")).sort_order)

        # 只返回启用的动作
        return [aid for aid in action_ids if self.action_info.get(aid, ActionInfo("", "", "")).enabled]

    def get_all_action_ids(self) -> List[str]:
        """
        获取所有动作ID

        Returns:
            所有动作ID列表
        """
        return list(self.actions.keys())

    def get_enabled_action_ids(self) -> List[str]:
        """
        获取所有启用的动作ID

        Returns:
            启用的动作ID列表
        """
        return [aid for aid, info in self.action_info.items() if info.enabled]

    def enable_action(self, action_id: str) -> bool:
        """
        启用动作

        Args:
            action_id: 动作标识符

        Returns:
            bool: 操作是否成功
        """
        if action_id in self.action_info:
            self.action_info[action_id].enabled = True
            return True
        return False

    def disable_action(self, action_id: str) -> bool:
        """
        禁用动作

        Args:
            action_id: 动作标识符

        Returns:
            bool: 操作是否成功
        """
        if action_id in self.action_info:
            self.action_info[action_id].enabled = False
            return True
        return False

    def is_action_enabled(self, action_id: str) -> bool:
        """
        检查动作是否启用

        Args:
            action_id: 动作标识符

        Returns:
            bool: 是否启用
        """
        info = self.action_info.get(action_id)
        return info.enabled if info else False

    def search_actions(self, query: str) -> List[str]:
        """
        搜索动作

        Args:
            query: 搜索关键词

        Returns:
            匹配的动作ID列表
        """
        query = query.lower()
        results = []

        for action_id, info in self.action_info.items():
            if (query in action_id.lower() or
                query in info.display_name.lower() or
                query in info.description.lower()):
                results.append(action_id)

        return results

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        获取注册中心统计信息

        Returns:
            统计信息字典
        """
        total_actions = len(self.actions)
        enabled_actions = len(self.get_enabled_action_ids())
        categories_count = len(self.categories)

        category_stats = {}
        for category, action_ids in self.categories.items():
            enabled_in_category = len([aid for aid in action_ids if self.is_action_enabled(aid)])
            category_stats[category] = {
                "total": len(action_ids),
                "enabled": enabled_in_category
            }

        return {
            "total_actions": total_actions,
            "enabled_actions": enabled_actions,
            "disabled_actions": total_actions - enabled_actions,
            "categories_count": categories_count,
            "category_stats": category_stats
        }

    def export_registry_info(self) -> Dict[str, Any]:
        """
        导出注册中心信息（用于UI显示）

        Returns:
            注册中心信息字典
        """
        result = {}

        for category in self.categories.keys():
            action_ids = self.get_actions_by_category(category)
            result[category] = []

            for action_id in action_ids:
                info = self.action_info[action_id]
                action = self.actions[action_id]

                result[category].append({
                    "id": action_id,
                    "name": info.display_name,
                    "description": info.description,
                    "hotkey": info.hotkey,
                    "icon": info.icon,
                    "enabled": info.enabled,
                    "can_execute": True if hasattr(action, 'can_execute') else None
                })

        return result

    def validate_registry(self) -> List[str]:
        """
        验证注册中心的完整性

        Returns:
            问题列表
        """
        issues = []

        # 检查动作实例是否有效
        for action_id, action in self.actions.items():
            if not hasattr(action, 'execute'):
                issues.append(f"动作 {action_id} 缺少execute方法")
            if not hasattr(action, 'can_execute'):
                issues.append(f"动作 {action_id} 缺少can_execute方法")
            if not hasattr(action, 'get_cost'):
                issues.append(f"动作 {action_id} 缺少get_cost方法")

        # 检查动作信息是否完整
        for action_id, info in self.action_info.items():
            if not info.display_name:
                issues.append(f"动作 {action_id} 缺少显示名称")
            if not info.description:
                issues.append(f"动作 {action_id} 缺少描述")

        # 检查分类一致性
        for action_id in self.actions.keys():
            if action_id not in self.action_info:
                issues.append(f"动作 {action_id} 缺少动作信息")

        for action_id in self.action_info.keys():
            if action_id not in self.actions:
                issues.append(f"动作信息 {action_id} 缺少对应的动作实例")

        return issues


# 全局动作注册中心实例
action_registry = ActionRegistry()


def initialize_game_actions():
    """初始化游戏动作"""
    from actions import MeditateAction, ConsumePillAction, CultivateAction, WaitAction

    # 注册游戏动作
    action_registry.register_action(
        "meditate", MeditateAction,
        display_name="打坐",
        description="进入冥想状态，恢复仙力并获得少量经验",
        category="game",
        hotkey="1",
        sort_order=1
    )

    action_registry.register_action(
        "consume_pill", ConsumePillAction,
        display_name="吃丹药",
        description="服用丹药快速恢复生命力和仙力",
        category="game",
        hotkey="2",
        sort_order=2
    )

    action_registry.register_action(
        "cultivate", CultivateAction,
        display_name="修炼",
        description="运转心法，大量提升修为",
        category="game",
        hotkey="3",
        sort_order=3
    )

    action_registry.register_action(
        "wait", WaitAction,
        display_name="等待",
        description="静心养神，缓慢恢复状态",
        category="game",
        hotkey="4",
        sort_order=4
    )

    print(f"已初始化 {len(action_registry.get_actions_by_category('game'))} 个游戏动作")


def get_action(action_id: str) -> Optional[Any]:
    """便捷函数：获取动作实例"""
    return action_registry.get_action(action_id)


def get_all_game_actions() -> List[str]:
    """便捷函数：获取所有游戏动作ID"""
    return action_registry.get_actions_by_category("game")


def execute_action_safely(action_id: str, character: CharacterStats,
                         game_log: GameLog) -> Dict[str, Any]:
    """
    安全执行动作

    Args:
        action_id: 动作ID
        character: 角色对象
        game_log: 游戏日志

    Returns:
        执行结果字典
    """
    action = action_registry.get_action(action_id)
    if not action:
        return {
            "success": False,
            "message": f"未找到动作: {action_id}",
            "effects": {},
            "costs": {}
        }

    if not action_registry.is_action_enabled(action_id):
        return {
            "success": False,
            "message": f"动作已禁用: {action_id}",
            "effects": {},
            "costs": {}
        }

    try:
        result = action.execute(character, game_log)
        # 如果result是ActionResult对象，转换为字典
        if hasattr(result, '__dict__'):
            return {
                "success": result.success,
                "message": result.message,
                "effects": result.effects,
                "costs": result.costs
            }
        else:
            return result
    except Exception as e:
        return {
            "success": False,
            "message": f"执行动作时出错: {e}",
            "effects": {},
            "costs": {}
        }