"""
状态管理器 - 管理游戏状态的保存和恢复
"""

from typing import Dict, Any, Optional, List
import json
import pickle
from datetime import datetime


class StateManager:
    """游戏状态管理器"""

    def __init__(self):
        self.current_state: Dict[str, Any] = {}
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 50

    def update_state(self, new_state: Dict[str, Any]):
        """
        更新当前状态
        Args:
            new_state: 新的游戏状态
        """
        # 保存到历史
        if self.current_state:
            self._add_to_history(self.current_state)

        # 更新当前状态
        self.current_state = new_state.copy()

    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state.copy()

    def _add_to_history(self, state: Dict[str, Any]):
        """添加状态到历史记录"""
        state_with_timestamp = {
            "state": state.copy(),
            "timestamp": datetime.now().isoformat()
        }

        self.state_history.append(state_with_timestamp)

        # 限制历史记录大小
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)

    def get_previous_state(self, steps_back: int = 1) -> Optional[Dict[str, Any]]:
        """
        获取之前的状态
        Args:
            steps_back: 回退步数
        Returns:
            Dict: 之前的状态，如果不存在则返回None
        """
        if len(self.state_history) >= steps_back:
            return self.state_history[-steps_back]["state"].copy()
        return None

    def rollback_state(self, steps_back: int = 1) -> bool:
        """
        回滚到之前的状态
        Args:
            steps_back: 回退步数
        Returns:
            bool: 回滚是否成功
        """
        previous_state = self.get_previous_state(steps_back)
        if previous_state:
            self.current_state = previous_state

            # 移除历史记录中回退的部分
            for _ in range(steps_back):
                if self.state_history:
                    self.state_history.pop()

            return True
        return False

    def clear_history(self):
        """清空历史记录"""
        self.state_history.clear()

    def export_state(self) -> str:
        """
        导出当前状态为JSON字符串
        Returns:
            str: JSON格式的状态数据
        """
        try:
            # 创建可序列化的状态副本
            serializable_state = self._make_serializable(self.current_state)
            return json.dumps(serializable_state, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"导出状态失败: {e}")
            return "{}"

    def import_state(self, state_json: str) -> bool:
        """
        从JSON字符串导入状态
        Args:
            state_json: JSON格式的状态数据
        Returns:
            bool: 导入是否成功
        """
        try:
            state_data = json.loads(state_json)
            self.current_state = state_data
            return True
        except Exception as e:
            print(f"导入状态失败: {e}")
            return False

    def _make_serializable(self, obj: Any) -> Any:
        """将对象转换为可序列化格式"""
        if hasattr(obj, '__dict__'):
            # 对于有属性的对象，尝试序列化其属性
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):  # 跳过私有属性
                    try:
                        # 尝试JSON序列化测试
                        json.dumps(value)
                        result[key] = value
                    except (TypeError, ValueError):
                        # 如果不能序列化，转换为字符串
                        result[key] = str(value)
            return result
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        else:
            return obj

    def save_to_file(self, filename: str) -> bool:
        """
        保存状态到文件
        Args:
            filename: 文件名
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.export_state())
            return True
        except Exception as e:
            print(f"保存到文件失败: {e}")
            return False

    def load_from_file(self, filename: str) -> bool:
        """
        从文件加载状态
        Args:
            filename: 文件名
        Returns:
            bool: 加载是否成功
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                state_json = f.read()
            return self.import_state(state_json)
        except Exception as e:
            print(f"从文件加载失败: {e}")
            return False

    def get_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        比较两个状态的差异
        Args:
            old_state: 旧状态
            new_state: 新状态
        Returns:
            Dict: 状态差异
        """
        diff = {}

        # 找出所有键
        all_keys = set(old_state.keys()) | set(new_state.keys())

        for key in all_keys:
            old_value = old_state.get(key)
            new_value = new_state.get(key)

            if old_value != new_value:
                diff[key] = {
                    "old": old_value,
                    "new": new_value
                }

        return diff

    def validate_state(self, state: Dict[str, Any]) -> bool:
        """
        验证状态的有效性
        Args:
            state: 要验证的状态
        Returns:
            bool: 状态是否有效
        """
        try:
            # 检查必需的字段
            required_fields = ["character", "game_log", "actions"]
            for field in required_fields:
                if field not in state:
                    print(f"缺少必需字段: {field}")
                    return False

            # 检查角色状态
            character = state.get("character")
            if character and hasattr(character, 'get_status_summary'):
                status = character.get_status_summary()

                # 验证数值范围
                if not (0 <= status.get("hp", 0) <= status.get("max_hp", 100)):
                    print("生命值超出范围")
                    return False

                if not (0 <= status.get("mp", 0) <= status.get("max_mp", 100)):
                    print("仙力值超出范围")
                    return False

                if status.get("talent", 0) < 1 or status.get("talent", 0) > 10:
                    print("资质值超出范围")
                    return False

            return True

        except Exception as e:
            print(f"状态验证失败: {e}")
            return False


class GameStateSnapshot:
    """游戏状态快照"""

    def __init__(self, state: Dict[str, Any], description: str = ""):
        self.state = state.copy()
        self.description = description
        self.timestamp = datetime.now()

    def get_age(self) -> float:
        """获取快照年龄（秒）"""
        return (datetime.now() - self.timestamp).total_seconds()

    def __str__(self):
        return f"Snapshot[{self.description} at {self.timestamp.strftime('%H:%M:%S')}]"


class SnapshotManager:
    """状态快照管理器"""

    def __init__(self, max_snapshots: int = 10):
        self.snapshots: List[GameStateSnapshot] = []
        self.max_snapshots = max_snapshots

    def create_snapshot(self, state: Dict[str, Any], description: str = ""):
        """创建状态快照"""
        snapshot = GameStateSnapshot(state, description)
        self.snapshots.append(snapshot)

        # 限制快照数量
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

    def get_latest_snapshot(self) -> Optional[GameStateSnapshot]:
        """获取最新的快照"""
        return self.snapshots[-1] if self.snapshots else None

    def get_snapshot_by_description(self, description: str) -> Optional[GameStateSnapshot]:
        """根据描述获取快照"""
        for snapshot in self.snapshots:
            if snapshot.description == description:
                return snapshot
        return None

    def restore_from_snapshot(self, snapshot: GameStateSnapshot) -> bool:
        """从快照恢复状态"""
        if snapshot:
            # 这里应该将快照状态应用到游戏核心
            # 具体实现取决于游戏核心的设计
            print(f"恢复到快照: {snapshot}")
            return True
        return False

    def clear_snapshots(self):
        """清空所有快照"""
        self.snapshots.clear()

    def get_snapshot_list(self) -> List[str]:
        """获取快照列表"""
        return [str(snapshot) for snapshot in self.snapshots]