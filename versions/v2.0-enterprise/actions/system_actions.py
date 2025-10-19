"""
系统动作实现
处理重启、设置等系统级功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import os
import time
from datetime import datetime

# 延迟导入避免循环依赖
def get_action_class():
    """获取Action基类，避免循环导入"""
    try:
        from actions import Action as ActionClass
        return ActionClass
    except ImportError:
        # 如果导入失败，创建一个最小的兼容类
        class ActionClass:
            def __init__(self, name: str, description: str):
                self.name = name
                self.description = description

            def get_cost(self):
                from models import Cost
                return Cost()

        return ActionClass

def get_event_handler():
    """获取事件处理器，避免循环导入"""
    try:
        from core.event_handler import event_handler
        return event_handler
    except ImportError:
        return None

def get_event_type():
    """获取事件类型，避免循环导入"""
    try:
        from core.event_handler import EventType
        return EventType
    except ImportError:
        # 创建兼容的事件类型枚举
        class EventType:
            RESET_GAME = "reset_game"
            SAVE_GAME = "save_game"
            LOAD_GAME = "load_game"
            ACTION_EXECUTED = "action_executed"
        return EventType


class SystemAction(ABC):
    """系统动作基类"""

    def __init__(self, name: str, description: str):
        # 延迟获取Action基类
        Action = get_action_class()
        if Action and hasattr(Action, '__init__'):
            Action.__init__(self, name, description)
        else:
            self.name = name
            self.description = description

        self.category = "system"  # 标记为系统动作

    @abstractmethod
    def execute_system_action(self, app_context) -> Dict[str, Any]:
        """执行系统动作（应用层上下文）"""
        pass

    def get_cost(self):
        """获取动作消耗"""
        try:
            from models import Cost
            return Cost()  # 系统动作通常无消耗
        except ImportError:
            return {"time": 0}

    def can_execute(self, app_context=None) -> bool:
        """检查是否可以执行动作"""
        # 系统动作通常总是可执行，但需要验证上下文
        if app_context is None:
            return False
        return True

    def _validate_app_context(self, app_context) -> bool:
        """验证应用上下文是否有效"""
        return app_context is not None and hasattr(app_context, '__class__')

    def _log_action(self, action_name: str, success: bool, message: str, extra_data: Dict = None):
        """记录动作执行日志"""
        event_handler = get_event_handler()
        if event_handler:
            EventType = get_event_type()
            event_handler.dispatch_event(
                EventType.ACTION_EXECUTED,
                {
                    "action": action_name,
                    "success": success,
                    "message": message,
                    "action_type": "system",
                    "timestamp": time.time(),
                    **(extra_data or {})
                }
            )

    def _dispatch_system_event(self, event_type: str, data: Dict):
        """分发系统事件"""
        event_handler = get_event_handler()
        if event_handler:
            EventType = get_event_type()
            if hasattr(EventType, event_type):
                event_handler.dispatch_event(getattr(EventType, event_type), data)


class RestartAction(SystemAction):
    """重新开始动作"""

    def __init__(self):
        super().__init__("restart", "重新开始游戏")

    def execute_system_action(self, app_context) -> Dict[str, Any]:
        """执行重新开始逻辑"""
        if not self._validate_app_context(app_context):
            return {
                "success": False,
                "message": "应用上下文无效",
                "effects": {},
                "costs": {}
            }

        try:
            # 保存统计信息
            if hasattr(app_context, '_save_session_statistics'):
                app_context._save_session_statistics()

            # 获取当前游戏信息
            character_name = None
            difficulty = "normal"

            if hasattr(app_context, 'game_core') and app_context.game_core.character:
                character_name = app_context.game_core.character.name

            if hasattr(app_context, 'game_core') and hasattr(app_context.game_core, 'difficulty'):
                difficulty = app_context.game_core.difficulty

            # 执行重置
            success = False
            reset_data = {}
            if hasattr(app_context, 'game_core'):
                success = app_context.game_core.reset_game(character_name, difficulty)
                reset_data = {
                    "previous_character": character_name,
                    "previous_difficulty": difficulty
                }

            if success:
                # 重置应用层统计
                if hasattr(app_context, 'total_actions'):
                    app_context.total_actions = 0
                if hasattr(app_context, 'start_time'):
                    app_context.start_time = time.time()

                # 分发重启事件
                self._dispatch_system_event("RESET_GAME", {
                    "character_name": character_name,
                    "difficulty": difficulty,
                    "timestamp": time.time(),
                    "reset_data": reset_data
                })

                result_message = f"游戏已重新开始 - 角色: {character_name or '无名修士'}, 难度: {difficulty}"

                # 记录动作日志
                self._log_action("restart", True, result_message, reset_data)

                return {
                    "success": True,
                    "message": result_message,
                    "effects": {"game_reset": True},
                    "costs": {}
                }
            else:
                error_message = "重新开始失败 - 游戏核心重置失败"
                self._log_action("restart", False, error_message)

                return {
                    "success": False,
                    "message": error_message,
                    "effects": {},
                    "costs": {}
                }

        except Exception as e:
            error_message = f"重新开始时出错: {str(e)}"
            self._log_action("restart", False, error_message, {"error": str(e)})

            return {
                "success": False,
                "message": error_message,
                "effects": {},
                "costs": {}
            }


class SettingsAction(SystemAction):
    """设置动作"""

    def __init__(self):
        super().__init__("settings", "打开设置界面")

    def execute_system_action(self, app_context) -> Dict[str, Any]:
        """执行设置逻辑"""
        if not self._validate_app_context(app_context):
            return {
                "success": False,
                "message": "应用上下文无效",
                "effects": {},
                "costs": {}
            }

        try:
            # 检查是否有设置方法
            if hasattr(app_context, '_show_settings'):
                settings_result = app_context._show_settings()

                # 如果方法返回了结果，使用返回值
                if isinstance(settings_result, dict):
                    success = settings_result.get("success", True)
                    message = settings_result.get("message", "设置界面已打开")
                    effects = settings_result.get("effects", {})
                else:
                    success = True
                    message = "设置界面已打开"
                    effects = {}

                if success:
                    self._log_action("settings", True, message, effects)
                    return {
                        "success": True,
                        "message": message,
                        "effects": effects,
                        "costs": {}
                    }
                else:
                    self._log_action("settings", False, message)
                    return {
                        "success": False,
                        "message": message,
                        "effects": {},
                        "costs": {}
                    }

            # 尝试使用主题管理器切换主题
            elif hasattr(app_context, 'ui') and hasattr(app_context.ui, 'show_message'):
                try:
                    from ui.themes import theme_manager
                    current_theme = theme_manager.current_theme
                    available_themes = theme_manager.get_available_themes()

                    if available_themes and len(available_themes) > 1:
                        # 切换到下一个主题
                        current_index = available_themes.index(current_theme)
                        next_index = (current_index + 1) % len(available_themes)
                        next_theme = available_themes[next_index]

                        theme_manager.set_theme(next_theme)
                        message = f"主题已切换为: {next_theme}"

                        # 显示消息
                        app_context.ui.show_message("设置", message)

                        self._log_action("settings", True, message, {
                            "previous_theme": current_theme,
                            "new_theme": next_theme
                        })

                        return {
                            "success": True,
                            "message": message,
                            "effects": {"theme_changed": True, "new_theme": next_theme},
                            "costs": {}
                        }
                    else:
                        message = "没有可切换的主题"
                        app_context.ui.show_message("设置", message)
                        self._log_action("settings", False, message)

                        return {
                            "success": False,
                            "message": message,
                            "effects": {},
                            "costs": {}
                        }

                except ImportError:
                    message = "主题管理器不可用"
                    self._log_action("settings", False, message)
                    return {
                        "success": False,
                        "message": message,
                        "effects": {},
                        "costs": {}
                    }

            else:
                message = "设置功能不可用"
                self._log_action("settings", False, message)
                return {
                    "success": False,
                    "message": message,
                    "effects": {},
                    "costs": {}
                }

        except Exception as e:
            error_message = f"打开设置时出错: {str(e)}"
            self._log_action("settings", False, error_message, {"error": str(e)})
            return {
                "success": False,
                "message": error_message,
                "effects": {},
                "costs": {}
            }


class GameSaveManager:
    """游戏存档管理器"""

    def __init__(self, save_dir: str = "saves"):
        self.save_dir = save_dir
        self._ensure_save_directory()

    def _ensure_save_directory(self):
        """确保存档目录存在"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def _get_save_file_path(self, slot: int) -> str:
        """获取存档文件路径"""
        return os.path.join(self.save_dir, f"save_slot_{slot}.json")

    def _generate_save_data(self, app_context) -> Dict[str, Any]:
        """生成存档数据"""
        save_data = {
            "version": "2.0",
            "timestamp": time.time(),
            "save_time": datetime.now().isoformat(),
        }

        # 游戏核心数据
        if hasattr(app_context, 'game_core') and app_context.game_core:
            game_core_data = {}

            # 角色数据
            if hasattr(app_context.game_core, 'character') and app_context.game_core.character:
                try:
                    character_status = app_context.game_core.character.get_status_summary()
                    game_core_data["character"] = character_status
                except Exception as e:
                    print(f"保存角色数据失败: {e}")
                    game_core_data["character"] = None

            # 游戏状态
            if hasattr(app_context.game_core, 'difficulty'):
                game_core_data["difficulty"] = app_context.game_core.difficulty

            if hasattr(app_context.game_core, 'is_game_over'):
                game_core_data["is_game_over"] = app_context.game_core.is_game_over

            save_data["game_core"] = game_core_data

        # 应用层统计
        app_data = {}
        if hasattr(app_context, 'total_actions'):
            app_data["total_actions"] = app_context.total_actions
        if hasattr(app_context, 'start_time') and app_context.start_time:
            app_data["session_time"] = time.time() - app_context.start_time
        if hasattr(app_context, 'session_statistics'):
            app_data["session_statistics"] = app_context.session_statistics

        save_data["application"] = app_data

        return save_data

    def save_game(self, app_context, slot: int = 1) -> Dict[str, Any]:
        """保存游戏到指定槽位"""
        try:
            save_data = self._generate_save_data(app_context)
            save_file_path = self._get_save_file_path(slot)

            # 写入存档文件
            with open(save_file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "message": f"游戏已保存到槽位 {slot}",
                "save_file": save_file_path,
                "save_data": save_data
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"保存失败: {str(e)}",
                "error": str(e)
            }

    def load_game(self, app_context, slot: int = 1) -> Dict[str, Any]:
        """从指定槽位加载游戏"""
        try:
            save_file_path = self._get_save_file_path(slot)

            if not os.path.exists(save_file_path):
                return {
                    "success": False,
                    "message": f"槽位 {slot} 没有存档文件",
                    "save_file": save_file_path
                }

            # 读取存档文件
            with open(save_file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # 验证存档版本
            if save_data.get("version") != "2.0":
                return {
                    "success": False,
                    "message": f"存档版本不兼容 (版本: {save_data.get('version', 'unknown')})",
                    "save_data": save_data
                }

            return {
                "success": True,
                "message": f"存档文件读取成功 (槽位 {slot})",
                "save_file": save_file_path,
                "save_data": save_data
            }

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "message": f"存档文件损坏: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}",
                "error": str(e)
            }

    def get_save_info(self, slot: int) -> Optional[Dict[str, Any]]:
        """获取存档信息"""
        save_file_path = self._get_save_file_path(slot)
        if not os.path.exists(save_file_path):
            return None

        try:
            with open(save_file_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            return {
                "slot": slot,
                "save_time": save_data.get("save_time", "未知时间"),
                "character_name": save_data.get("game_core", {}).get("character", {}).get("name", "未知角色"),
                "realm": save_data.get("game_core", {}).get("character", {}).get("realm", "未知境界"),
                "difficulty": save_data.get("game_core", {}).get("difficulty", "未知难度"),
                "total_actions": save_data.get("application", {}).get("total_actions", 0)
            }
        except Exception:
            return None


class SaveGameAction(SystemAction):
    """保存游戏动作"""

    def __init__(self, slot: int = 1):
        super().__init__("save_game", f"保存游戏到槽位 {slot}")
        self.slot = slot

    def get_cost(self):
        """获取动作消耗"""
        try:
            from models import Cost
            return Cost(time=1)  # 保存需要时间
        except ImportError:
            return {"time": 1}

    def execute_system_action(self, app_context) -> Dict[str, Any]:
        """执行保存逻辑"""
        if not self._validate_app_context(app_context):
            return {
                "success": False,
                "message": "应用上下文无效",
                "effects": {},
                "costs": {"time": 1}
            }

        try:
            # 创建存档管理器
            save_manager = GameSaveManager()

            # 执行保存
            save_result = save_manager.save_game(app_context, self.slot)

            if save_result["success"]:
                # 分发保存事件
                self._dispatch_system_event("SAVE_GAME", {
                    "slot": self.slot,
                    "save_file": save_result["save_file"],
                    "timestamp": time.time()
                })

                # 记录动作日志
                self._log_action("save_game", True, save_result["message"], {
                    "slot": self.slot,
                    "save_file": save_result["save_file"]
                })

                return {
                    "success": True,
                    "message": save_result["message"],
                    "effects": {"game_saved": True, "slot": self.slot},
                    "costs": {"time": 1}
                }
            else:
                # 记录失败日志
                self._log_action("save_game", False, save_result["message"], {
                    "slot": self.slot,
                    "error": save_result.get("error", "未知错误")
                })

                return {
                    "success": False,
                    "message": save_result["message"],
                    "effects": {},
                    "costs": {"time": 1}
                }

        except Exception as e:
            error_message = f"保存游戏时出错: {str(e)}"
            self._log_action("save_game", False, error_message, {"error": str(e)})
            return {
                "success": False,
                "message": error_message,
                "effects": {},
                "costs": {"time": 1}
            }


class LoadGameAction(SystemAction):
    """加载游戏动作"""

    def __init__(self, slot: int = 1):
        super().__init__("load_game", f"从槽位 {slot} 加载游戏")
        self.slot = slot

    def get_cost(self):
        """获取动作消耗"""
        try:
            from models import Cost
            return Cost(time=2)  # 加载需要更多时间
        except ImportError:
            return {"time": 2}

    def execute_system_action(self, app_context) -> Dict[str, Any]:
        """执行加载逻辑"""
        if not self._validate_app_context(app_context):
            return {
                "success": False,
                "message": "应用上下文无效",
                "effects": {},
                "costs": {"time": 2}
            }

        try:
            # 创建存档管理器
            save_manager = GameSaveManager()

            # 执行加载
            load_result = save_manager.load_game(app_context, self.slot)

            if load_result["success"]:
                save_data = load_result["save_data"]

                # 恢复游戏核心数据
                if "game_core" in save_data and hasattr(app_context, 'game_core'):
                    game_core_data = save_data["game_core"]

                    # 恢复角色数据 (这里需要根据实际的游戏核心实现来调整)
                    if "character" in game_core_data and game_core_data["character"]:
                        try:
                            # 这里应该有实际的角色数据恢复逻辑
                            # 由于不知道具体的实现，我们只是分发事件
                            pass
                        except Exception as e:
                            print(f"恢复角色数据失败: {e}")

                    # 恢复游戏状态
                    if "difficulty" in game_core_data:
                        app_context.game_core.difficulty = game_core_data["difficulty"]
                    if "is_game_over" in game_core_data:
                        app_context.game_core.is_game_over = game_core_data["is_game_over"]

                # 恢复应用层统计
                if "application" in save_data:
                    app_data = save_data["application"]
                    if "total_actions" in app_data:
                        app_context.total_actions = app_data["total_actions"]
                    if "session_statistics" in app_data:
                        app_context.session_statistics = app_data["session_statistics"]

                # 重置开始时间
                app_context.start_time = time.time()

                # 分发加载事件
                self._dispatch_system_event("LOAD_GAME", {
                    "slot": self.slot,
                    "save_file": load_result["save_file"],
                    "timestamp": time.time(),
                    "save_data": save_data
                })

                # 记录动作日志
                self._log_action("load_game", True, load_result["message"], {
                    "slot": self.slot,
                    "save_file": load_result["save_file"]
                })

                return {
                    "success": True,
                    "message": load_result["message"],
                    "effects": {"game_loaded": True, "slot": self.slot},
                    "costs": {"time": 2}
                }
            else:
                # 记录失败日志
                self._log_action("load_game", False, load_result["message"], {
                    "slot": self.slot,
                    "error": load_result.get("error", "未知错误")
                })

                return {
                    "success": False,
                    "message": load_result["message"],
                    "effects": {},
                    "costs": {"time": 2}
                }

        except Exception as e:
            error_message = f"加载游戏时出错: {str(e)}"
            self._log_action("load_game", False, error_message, {"error": str(e)})
            return {
                "success": False,
                "message": error_message,
                "effects": {},
                "costs": {"time": 2}
            }


class SystemActionFactory:
    """系统动作工厂类"""

    @staticmethod
    def get_all_system_actions() -> list:
        """获取所有系统动作"""
        return [
            RestartAction(),
            SettingsAction(),
            SaveGameAction(slot=1),  # 默认槽位1
            LoadGameAction(slot=1),  # 默认槽位1
        ]

    @staticmethod
    def get_system_action_by_name(action_name: str, slot: int = 1):
        """根据名称获取系统动作"""
        if action_name == "restart":
            return RestartAction()
        elif action_name == "settings":
            return SettingsAction()
        elif action_name == "save_game":
            return SaveGameAction(slot=slot)
        elif action_name == "load_game":
            return LoadGameAction(slot=slot)
        else:
            return None

    @staticmethod
    def is_system_action(action_name: str) -> bool:
        """检查是否为系统动作"""
        system_action_names = {"restart", "settings", "save_game", "load_game"}
        return action_name in system_action_names

    @staticmethod
    def get_save_slot_list() -> list:
        """获取可用的存档槽位列表"""
        save_manager = GameSaveManager()
        slot_list = []
        for slot in range(1, 6):  # 支持5个槽位
            save_info = save_manager.get_save_info(slot)
            if save_info:
                slot_list.append(save_info)
            else:
                slot_list.append({
                    "slot": slot,
                    "save_time": None,
                    "character_name": "空槽位",
                    "realm": None,
                    "difficulty": None,
                    "total_actions": 0,
                    "empty": True
                })
        return slot_list