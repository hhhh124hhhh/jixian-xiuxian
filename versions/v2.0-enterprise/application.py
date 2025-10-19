"""
主应用程序 - 协调各个组件
"""

import sys
import time
from typing import Optional, Dict, Any
from ui.interface import GameInterface, UIEvent
from ui.pygame_renderer import PygameGameInterface
from core.game_core import GameCore
from core.event_handler import event_handler, EventType, GameEventLogger, AchievementTracker, GameEvent
from ui.layouts import default_layout
from ui.themes import theme_manager
from actions.system_actions import SystemActionFactory


class GameApplication:
    """游戏主应用程序"""

    def __init__(self, ui_interface: GameInterface = None):
        self.ui = ui_interface or PygameGameInterface()
        self.game_core = GameCore()

        # 应用程序状态
        self.running = False
        self.paused = False
        self.clock = None
        self.fps = 30

        # 统计信息
        self.start_time = None
        self.total_actions = 0
        self.session_statistics = {}

        # 设置UI回调
        self._setup_ui_callbacks()

        # 注册事件监听器
        self._setup_event_listeners()

    def _setup_ui_callbacks(self):
        """设置UI回调函数"""
        if hasattr(self.ui, 'on_action_selected'):
            self.ui.on_action_selected = self._on_action_selected

        # 系统动作现在通过统一的动作处理机制处理，不再需要单独的回调
        # 但保留兼容性以防UI层仍调用这些方法
        if hasattr(self.ui, 'on_restart_requested'):
            self.ui.on_restart_requested = lambda: self._on_action_selected("restart")

        if hasattr(self.ui, 'on_settings_requested'):
            self.ui.on_settings_requested = lambda: self._on_action_selected("settings")

    def _setup_event_listeners(self):
        """设置事件监听器"""
        # 注册日志记录器
        self.event_logger = GameEventLogger(event_handler)

        # 注册成就跟踪器
        self.achievement_tracker = AchievementTracker(event_handler)

        # 注册应用程序事件监听器
        event_handler.register_listener(EventType.GAME_START, self._on_game_start)
        event_handler.register_listener(EventType.GAME_OVER, self._on_game_over)
        event_handler.register_listener(EventType.ACTION_EXECUTED, self._on_action_executed)
        event_handler.register_listener(EventType.LEVEL_UP, self._on_level_up)

        # 注册系统动作相关事件监听器
        event_handler.register_listener(EventType.RESTART_REQUESTED, self._on_restart_requested_event)
        event_handler.register_listener(EventType.SETTINGS_REQUESTED, self._on_settings_requested_event)
        event_handler.register_listener(EventType.SAVE_GAME, self._on_save_game_event)
        event_handler.register_listener(EventType.LOAD_GAME, self._on_load_game_event)

    def initialize(self, character_name: str = None, difficulty: str = "normal") -> bool:
        """
        初始化应用程序
        Args:
            character_name: 角色名称
            difficulty: 游戏难度
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化UI
            if not self.ui.initialize():
                print("UI初始化失败")
                return False

            # 初始化游戏核心
            if not self.game_core.initialize_game(character_name, difficulty):
                print("游戏核心初始化失败")
                return False

            # 设置时钟
            import pygame
            self.clock = pygame.time.Clock()

            # 记录开始时间
            self.start_time = time.time()

            # 分发游戏开始事件
            event_handler.dispatch_event(
                EventType.GAME_START,
                {
                    "character_name": character_name or "无名修士",
                    "difficulty": difficulty
                }
            )

            print(f"游戏初始化成功 - 角色: {character_name or '无名修士'}, 难度: {difficulty}")
            return True

        except Exception as e:
            print(f"应用程序初始化失败: {e}")
            return False

    def run(self) -> int:
        """
        运行主循环
        Returns:
            int: 退出代码
        """
        if not self.game_core.character:
            print("游戏未初始化")
            return 1

        self.running = True

        try:
            while self.running:
                # 处理输入
                ui_event = self.ui.handle_input()

                if ui_event:
                    self._handle_ui_event(ui_event)

                # 更新游戏状态
                if not self.paused:
                    self._update_game_state()

                # 渲染界面
                game_state = self.game_core.get_game_state()
                self.ui.render(game_state)

                # 控制帧率
                if self.clock:
                    self.clock.tick(self.fps)

                # 检查游戏是否结束
                if self.game_core.is_game_over:
                    self._handle_game_over()

            return 0

        except KeyboardInterrupt:
            print("\n游戏被用户中断")
            return 130
        except Exception as e:
            print(f"运行时错误: {e}")
            return 1
        finally:
            self.shutdown()

    def _handle_ui_event(self, event: UIEvent):
        """处理UI事件"""
        if event.event_type == "quit":
            self.running = False

        elif event.event_type == "action":
            action_name = event.data.get("action")
            if action_name:
                self._execute_action(action_name)

        # 移除restart和settings的独立处理，现在都通过action事件统一处理

    def _execute_action(self, action_name: str):
        """统一执行游戏动作和系统动作"""
        result = None

        # 检查是否为系统动作
        if SystemActionFactory.is_system_action(action_name):
            # 执行系统动作
            system_action = SystemActionFactory.get_system_action_by_name(action_name)
            if system_action:
                result = system_action.execute_system_action(self)
            else:
                result = {
                    "success": False,
                    "message": f"系统动作 {action_name} 未找到",
                    "effects": {},
                    "costs": {}
                }
        else:
            # 执行游戏动作
            if not self.game_core.character or self.game_core.is_game_over:
                result = {
                    "success": False,
                    "message": "游戏未开始或已结束",
                    "effects": {},
                    "costs": {}
                }
            else:
                result = self.game_core.execute_action(action_name)

        # 更新统计（只有成功的动作才计数）
        if result and result.get("success"):
            self.total_actions += 1

        # 分发动作执行事件
        if result:
            event_handler.dispatch_event(
                EventType.ACTION_EXECUTED,
                {
                    "action": action_name,
                    "result": result,
                    "total_actions": self.total_actions,
                    "action_type": "system" if SystemActionFactory.is_system_action(action_name) else "game"
                }
            )

        return result

    def _update_game_state(self):
        """更新游戏状态"""
        # 这里可以添加实时更新逻辑
        # 比如时间流逝、环境变化等
        pass

    def _on_action_selected(self, action_name: str):
        """UI动作选择回调"""
        self._execute_action(action_name)

    def _on_restart_requested(self):
        """UI重启请求回调"""
        if self.ui.show_confirmation("重新开始", "确定要重新开始游戏吗？"):
            self._restart_game()

    def _on_settings_requested(self):
        """UI设置请求回调"""
        self._show_settings()

    def _restart_game(self):
        """重启游戏"""
        # 保存统计信息
        self._save_session_statistics()

        # 重置游戏核心
        character_name = self.game_core.character.name if self.game_core.character else None
        difficulty = self.game_core.difficulty

        if self.game_core.reset_game(character_name, difficulty):
            # 重置统计
            self.total_actions = 0
            self.start_time = time.time()

            # 分发重启事件
            event_handler.dispatch_event(
                EventType.RESET_GAME,
                {
                    "character_name": character_name,
                    "difficulty": difficulty
                }
            )

            print("游戏已重新开始")

    def _show_settings(self):
        """显示设置界面"""
        # 简单实现：循环切换主题
        current_theme = theme_manager.current_theme
        available_themes = theme_manager.get_available_themes()

        # 切换到下一个主题
        current_index = available_themes.index(current_theme)
        next_index = (current_index + 1) % len(available_themes)
        next_theme = available_themes[next_index]

        theme_manager.set_theme(next_theme)
        self.ui.show_message("设置", f"主题已切换为: {next_theme}")

    def _save_game(self, slot: int = 1) -> bool:
        """保存游戏到指定槽位"""
        try:
            # 这里应该实现实际的保存逻辑
            # 目前作为示例，只分发事件
            event_handler.dispatch_event(
                EventType.SAVE_GAME,
                {
                    "slot": slot,
                    "character_name": self.game_core.character.name if self.game_core.character else None,
                    "difficulty": self.game_core.difficulty,
                    "timestamp": time.time()
                }
            )
            return True
        except Exception as e:
            print(f"保存游戏失败: {e}")
            return False

    def _load_game(self, slot: int = 1) -> bool:
        """从指定槽位加载游戏"""
        try:
            # 这里应该实现实际的加载逻辑
            # 目前作为示例，只分发事件
            event_handler.dispatch_event(
                EventType.LOAD_GAME,
                {
                    "slot": slot,
                    "timestamp": time.time()
                }
            )
            return True
        except Exception as e:
            print(f"加载游戏失败: {e}")
            return False

    def _handle_game_over(self):
        """处理游戏结束"""
        if not self.game_core.is_game_over:
            return

        # 保存统计信息
        self._save_session_statistics()

        # 获取最终统计
        final_stats = self.game_core.get_game_statistics()

        # 显示结束消息
        character = self.game_core.character
        if character and character.experience.current_realm.value == "飞升":
            message = f"恭喜飞升！\n总经验: {final_stats.get('total_experience', 0)}\n总行动: {final_stats.get('total_actions', 0)}"
            self.ui.show_message("游戏胜利", message, "success")
        else:
            message = f"修炼失败...\n最终境界: {final_stats.get('current_realm', '未知')}\n总经验: {final_stats.get('total_experience', 0)}"
            self.ui.show_message("游戏结束", message, "info")

        # 分发游戏结束事件
        event_handler.dispatch_event(
            EventType.GAME_OVER,
            {
                "final_stats": final_stats,
                "session_stats": self.session_statistics,
                "victory": character and character.experience.current_realm.value == "飞升"
            }
        )

        # 等待用户确认
        time.sleep(2)

        # 询问是否重新开始
        if self.ui.show_confirmation("游戏结束", "是否重新开始？"):
            self._restart_game()
        else:
            self.running = False

    def _save_session_statistics(self):
        """保存会话统计信息"""
        if self.start_time:
            session_time = time.time() - self.start_time
        else:
            session_time = 0

        game_stats = self.game_core.get_game_statistics()

        self.session_statistics = {
            "session_time": session_time,
            "total_actions": self.total_actions,
            "final_stats": game_stats,
            "achievements": self.achievement_tracker.get_achievements()
        }

    def shutdown(self):
        """关闭应用程序"""
        try:
            # 保存最终统计
            if self.game_core.character:
                self._save_session_statistics()

            # 显示会话统计
            if self.session_statistics:
                self._print_session_statistics()

            # 关闭UI
            if self.ui:
                self.ui.shutdown()

            print("游戏已退出")

        except Exception as e:
            print(f"关闭应用程序时出错: {e}")

    def _print_session_statistics(self):
        """打印会话统计信息"""
        stats = self.session_statistics
        session_time = stats.get("session_time", 0)
        total_actions = stats.get("total_actions", 0)
        final_stats = stats.get("final_stats", {})
        achievements = stats.get("achievements", {})

        print("\n" + "="*50)
        print("会话统计信息")
        print("="*50)
        print(f"游戏时长: {session_time:.1f}秒")
        print(f"总行动次数: {total_actions}")
        print(f"最终境界: {final_stats.get('current_realm', '未知')}")
        print(f"总经验值: {final_stats.get('total_experience', 0)}")
        print(f"获得成就: {len([a for a, unlocked in achievements.items() if unlocked])}")

        if achievements:
            print("\n解锁的成就:")
            for achievement_id, unlocked in achievements.items():
                if unlocked:
                    print(f"  ✓ {achievement_id}")

        print("="*50)

    # 事件处理器
    def _on_game_start(self, event: GameEvent):
        """游戏开始事件处理"""
        print(f"游戏开始 - {event.data}")

    def _on_game_over(self, event: GameEvent):
        """游戏结束事件处理"""
        victory = event.data.get("victory", False)
        result = "胜利" if victory else "失败"
        print(f"游戏结束 - {result}")

    def _on_action_executed(self, event: GameEvent):
        """动作执行事件处理"""
        action = event.data.get("action", "未知")
        result = event.data.get("result", {})
        success = result.get("success", False)

        if success:
            print(f"动作执行: {action} - 成功")
        else:
            print(f"动作执行: {action} - 失败: {result.get('message', '未知错误')}")

    def _on_level_up(self, event: GameEvent):
        """等级提升事件处理"""
        new_level = event.data.get("new_level", "未知")
        print(f"🎉 突破境界: {new_level}")

    # 系统动作事件处理器
    def _on_restart_requested_event(self, event: GameEvent):
        """重启请求事件处理"""
        print("收到重启请求事件")
        # 这个事件现在由RestartAction自己处理，这里只做日志记录

    def _on_settings_requested_event(self, event: GameEvent):
        """设置请求事件处理"""
        print("收到设置请求事件")
        # 这个事件现在由SettingsAction自己处理，这里只做日志记录

    def _on_save_game_event(self, event: GameEvent):
        """保存游戏事件处理"""
        slot = event.data.get("slot", 1)
        print(f"保存游戏到槽位 {slot}")

    def _on_load_game_event(self, event: GameEvent):
        """加载游戏事件处理"""
        slot = event.data.get("slot", 1)
        print(f"从槽位 {slot} 加载游戏")

    def get_application_info(self) -> Dict[str, Any]:
        """获取应用程序信息"""
        return {
            "version": "1.0.0",
            "name": "极简修仙 MVP",
            "running": self.running,
            "paused": self.paused,
            "fps": self.fps,
            "ui_type": type(self.ui).__name__,
            "total_actions": self.total_actions,
            "session_time": time.time() - self.start_time if self.start_time else 0
        }


def main():
    """主函数"""
    # 创建应用程序
    app = GameApplication()

    # 获取角色名称（可选）
    # character_name = input("请输入角色名称（回车使用默认名称）: ").strip()
    # if not character_name:
    #     character_name = None

    character_name = None  # 暂时使用默认名称

    # 初始化应用程序
    if not app.initialize(character_name, "normal"):
        print("初始化失败，程序退出")
        return 1

    # 运行应用程序
    exit_code = app.run()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())