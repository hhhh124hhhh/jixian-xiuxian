"""
游戏核心逻辑 - 集成所有游戏模块
"""

from typing import Dict, Any, Optional, List
from models import CharacterStats, GameLog
from actions import ActionFactory
from rules import game_rules, difficulty_settings
from core.event_handler import event_handler, EventType


class GameCore:
    """游戏核心逻辑类"""

    def __init__(self):
        self.character: Optional[CharacterStats] = None
        self.game_log: Optional[GameLog] = None
        self.available_actions: List = []
        self.game_state: Dict[str, Any] = {}
        self.is_game_over = False
        self.difficulty = "normal"

        # 初始化动作列表
        self._init_actions()

    def _init_actions(self):
        """初始化可用动作"""
        self.available_actions = ActionFactory.get_all_actions()

    def initialize_game(self, character_name: str = None, difficulty: str = "normal") -> bool:
        """
        初始化游戏
        Args:
            character_name: 角色名称
            difficulty: 游戏难度
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 设置难度
            self.difficulty = difficulty
            settings = difficulty_settings.get_difficulty_settings(difficulty)

            # 创建角色
            name = character_name or "无名修士"
            self.character = CharacterStats(name)

            # 应用难度设置
            difficulty_settings.apply_difficulty_to_character(self.character, difficulty)

            # 创建游戏日志
            self.game_log = GameLog()

            # 添加初始日志
            self.game_log.add_entry(f"欢迎来到极简修仙世界，{name}！")
            self.game_log.add_entry(f"你的资质为 {self.character.talent.base_talent}，开始你的修仙之旅。")

            # 初始化游戏状态
            self._update_game_state()

            self.is_game_over = False

            # 分发游戏开始事件
            event_handler.dispatch_event(
                EventType.GAME_START,
                {
                    "character_name": self.character.name,
                    "talent": self.character.talent.base_talent,
                    "difficulty": difficulty
                }
            )

            return True

        except Exception as e:
            print(f"游戏初始化失败: {e}")
            return False

    def execute_action(self, action_name: str) -> Dict[str, Any]:
        """
        执行动作
        Args:
            action_name: 动作名称
        Returns:
            Dict: 执行结果
        """
        if self.is_game_over or not self.character:
            return {
                "success": False,
                "message": "游戏已结束",
                "effects": {},
                "costs": {}
            }

        # 查找动作
        action = ActionFactory.get_action_by_name(action_name)
        if not action:
            return {
                "success": False,
                "message": f"未找到动作: {action_name}",
                "effects": {},
                "costs": {}
            }

        # 检查是否可以执行
        if not action.can_execute(self.character):
            return {
                "success": False,
                "message": action.get_failure_message(self.character),
                "effects": {},
                "costs": {}
            }

        # 执行动作
        try:
            result = action.execute(self.character, self.game_log)

            # 分发动作执行事件
            event_handler.dispatch_event(
                EventType.ACTION_EXECUTED,
                {
                    "action": action_name,
                    "result": {
                        "success": result.success,
                        "message": result.message,
                        "effects": result.effects,
                        "costs": result.costs
                    },
                    "character_state": self.character.get_status_summary()
                }
            )

            # 检查是否获得丹药奖励
            if result.effects.get("pill_bonus", 0) > 0:
                event_handler.dispatch_event(
                    EventType.PILL_OBTAINED,
                    {
                        "amount": result.effects["pill_bonus"],
                        "reason": "连续打坐奖励",
                        "streak": self.character.meditation_streak
                    }
                )

            # 检查连续打坐
            if action_name == "打坐" and self.character.meditation_streak % 5 == 0:
                event_handler.dispatch_event(
                    EventType.MEDITATION_STREAK,
                    {
                        "streak": self.character.meditation_streak,
                        "pills_obtained": result.effects.get("pill_bonus", 0)
                    }
                )

            # 检查等级提升
            if result.effects.get("level_up", False):
                event_handler.dispatch_event(
                    EventType.LEVEL_UP,
                    {
                        "new_level": result.effects["new_level"],
                        "character_name": self.character.name,
                        "total_experience": self.character.experience.total_experience,
                        "action": action_name
                    }
                )

            # 更新游戏状态
            self._update_game_state()

            # 检查游戏是否结束
            self._check_game_over()

            return {
                "success": result.success,
                "message": result.message,
                "effects": result.effects,
                "costs": result.costs
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"执行动作时出错: {e}",
                "effects": {},
                "costs": {}
            }

    def _update_game_state(self):
        """更新游戏状态"""
        if not self.character:
            return

        self.game_state = {
            "character": self.character,
            "game_log": self.game_log,
            "actions": self.available_actions,
            "is_game_over": self.is_game_over,
            "difficulty": self.difficulty,
            "power_level": game_rules.get_character_power_level(self.character),
            "recommendation": game_rules.get_action_recommendation(self.character)
        }

    def _check_game_over(self):
        """检查游戏是否结束"""
        if not self.character:
            return

        if not self.character.is_alive():
            self.is_game_over = True
            self.game_log.add_entry("修炼失败，游戏结束。")

            # 分发角色死亡事件
            event_handler.dispatch_event(
                EventType.CHARACTER_DIED,
                {
                    "character_name": self.character.name,
                    "realm": self.character.experience.current_realm.value,
                    "total_experience": self.character.experience.total_experience,
                    "total_actions": self.character.total_actions
                }
            )

            # 分发游戏结束事件
            event_handler.dispatch_event(
                EventType.GAME_OVER,
                {
                    "reason": "character_died",
                    "character_state": self.character.get_status_summary(),
                    "victory": False
                }
            )

        elif self.character.experience.current_realm.value == "飞升":
            self.is_game_over = True
            self.game_log.add_entry("恭喜！你已成功飞升，达成完美结局！")

            # 分发游戏结束事件
            event_handler.dispatch_event(
                EventType.GAME_OVER,
                {
                    "reason": "ascension",
                    "character_state": self.character.get_status_summary(),
                    "victory": True
                }
            )

    def get_game_state(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        return self.game_state.copy()

    def reset_game(self, character_name: str = None, difficulty: str = None) -> bool:
        """
        重置游戏
        Args:
            character_name: 新角色名称
            difficulty: 新游戏难度
        Returns:
            bool: 重置是否成功
        """
        difficulty = difficulty or self.difficulty
        return self.initialize_game(character_name, difficulty)

    def save_game(self, slot: int = 1) -> bool:
        """
        保存游戏
        Args:
            slot: 保存槽位
        Returns:
            bool: 保存是否成功
        """
        if not self.character:
            print("没有角色数据可保存")
            return False

        try:
            import json
            import os

            # 创建保存目录
            save_dir = "saves"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            save_file = os.path.join(save_dir, f"save_slot_{slot}.json")

            # 准备保存数据
            save_data = {
                "character": self.character.get_status_summary(),
                "game_log_entries": self.game_log.entries if self.game_log else [],
                "difficulty": self.difficulty,
                "is_game_over": self.is_game_over,
                "meditation_streak": self.character.meditation_streak,
                "total_actions": self.character.total_actions,
                "actions": self.character.total_actions,  # 备用字段名
                "version": "2.0.0"
            }

            # 保存到文件
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            print(f"游戏已保存到槽位 {slot}")
            return True

        except Exception as e:
            print(f"保存游戏失败: {e}")
            return False

    def load_game(self, slot: int = 1) -> bool:
        """
        加载游戏
        Args:
            slot: 保存槽位
        Returns:
            bool: 加载是否成功
        """
        try:
            import json
            import os

            save_file = os.path.join("saves", f"save_slot_{slot}.json")

            if not os.path.exists(save_file):
                print(f"槽位 {slot} 没有保存数据")
                return False

            # 加载保存数据
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # 检查版本兼容性
            if save_data.get("version") != "2.0.0":
                print("保存版本不兼容，无法加载")
                return False

            # 重新初始化游戏
            character_data = save_data["character"]
            difficulty = save_data["difficulty"]

            self.initialize_game(character_data["name"], difficulty)

            # 恢复角色状态
            if self.character:
                self.character.health.current_hp = character_data["hp"]
                self.character.mana.current_mp = character_data["mp"]
                self.character.inventory.add_item("pill", character_data["pills"] - self.character.inventory.get_item_count("pill"))
                self.character.meditation_streak = character_data["meditation_streak"]
                # 恢复总行动次数
                total_actions = character_data.get("total_actions", 0)
                if not total_actions:
                    total_actions = character_data.get("actions", 0)  # 尝试备用字段名
                self.character.total_actions = total_actions

                # 恢复经验值和境界
                from models import RealmLevel
                realm_map = {
                    "炼气期": RealmLevel.QI_REFINING,
                    "筑基期": RealmLevel.FOUNDATION,
                    "结丹期": RealmLevel.CORE_FORMATION,
                    "元婴期": RealmLevel.NASCENT_SOUL,
                    "化神期": RealmLevel.SPIRITUAL_TRANSFORMATION,
                    "飞升": RealmLevel.ASCENSION
                }

                if character_data["realm"] in realm_map:
                    self.character.experience.current_realm = realm_map[character_data["realm"]]
                    self.character.experience.current_level_experience = character_data["exp"]
                    self.character.experience.total_experience = character_data["total_exp"]

                # 恢复游戏日志
                if self.game_log and save_data.get("game_log_entries"):
                    self.game_log.entries = save_data["game_log_entries"]

                self.is_game_over = save_data["is_game_over"]

            print(f"游戏已从槽位 {slot} 加载")
            return True

        except Exception as e:
            print(f"加载游戏失败: {e}")
            return False

    def get_game_statistics(self) -> Dict[str, Any]:
        """获取游戏统计信息"""
        if not self.character:
            return {}

        status = self.character.get_status_summary()

        return {
            "total_actions": status["total_actions"],
            "total_experience": status["total_exp"],
            "current_realm": status["realm"],
            "talent": status["talent"],
            "pills_used": max(0, status["total_actions"] - status["pills"]),  # 简单估算
            "max_meditation_streak": status["meditation_streak"],  # 当前连续
            "power_level": game_rules.get_character_power_level(self.character),
            "difficulty": self.difficulty
        }

    def get_available_actions(self) -> List[str]:
        """获取可用动作列表"""
        if self.is_game_over or not self.character:
            return []

        available = []
        for action in self.available_actions:
            if action.can_execute(self.character):
                available.append(action.name)

        return available

    def get_character_info(self) -> Dict[str, Any]:
        """获取角色详细信息"""
        if not self.character:
            return {}

        return self.character.get_status_summary()

    def is_action_available(self, action_name: str) -> bool:
        """检查动作是否可用"""
        if self.is_game_over or not self.character:
            return False

        action = ActionFactory.get_action_by_name(action_name)
        if not action:
            return False

        return action.can_execute(self.character)

    def get_action_description(self, action_name: str) -> str:
        """获取动作描述"""
        action = ActionFactory.get_action_by_name(action_name)
        if action:
            return action.description
        return "未知动作"

    def get_action_cost(self, action_name: str) -> Dict[str, int]:
        """获取动作消耗"""
        action = ActionFactory.get_action_by_name(action_name)
        if action:
            cost = action.get_cost()
            return {
                "hp": cost.hp,
                "mp": cost.mp,
                "pills": cost.pills,
                "time": cost.time
            }
        return {}

    def simulate_action(self, action_name: str) -> Dict[str, Any]:
        """
        模拟动作执行（不实际执行，只返回预期结果）
        Args:
            action_name: 动作名称
        Returns:
            Dict: 预期执行结果
        """
        if self.is_game_over or not self.character:
            return {
                "success": False,
                "message": "游戏已结束",
                "effects": {},
                "costs": {}
            }

        action = ActionFactory.get_action_by_name(action_name)
        if not action:
            return {
                "success": False,
                "message": f"未找到动作: {action_name}",
                "effects": {},
                "costs": {}
            }

        # 检查是否可以执行
        if not action.can_execute(self.character):
            return {
                "success": False,
                "message": action.get_failure_message(self.character),
                "effects": {},
                "costs": {}
            }

        # 返回预期结果（不实际执行）
        cost = action.get_cost()
        return {
            "success": True,
            "message": f"预期执行: {action.name}",
            "effects": {},  # 这里可以根据动作类型计算预期效果
            "costs": {
                "hp": cost.hp,
                "mp": cost.mp,
                "pills": cost.pills,
                "time": cost.time
            }
        }


class GameStateManager:
    """游戏状态管理器"""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.max_history = 100

    def save_state(self, state: Dict[str, Any]):
        """保存状态到历史"""
        self.history.append(state.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_previous_state(self, steps: int = 1) -> Optional[Dict[str, Any]]:
        """获取之前的状态"""
        if len(self.history) > steps:
            return self.history[-steps - 1]
        return None

    def clear_history(self):
        """清空历史"""
        self.history.clear()


# 全局游戏核心实例
game_core = GameCore()