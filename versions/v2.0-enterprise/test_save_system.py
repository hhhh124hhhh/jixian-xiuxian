#!/usr/bin/env python3
"""
存档系统测试脚本
测试GameSaveManager和相关的保存/加载功能
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_save_manager():
    """测试存档管理器"""
    print("🔍 测试存档管理器...")

    try:
        # 动态导入system_actions模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "system_actions",
            os.path.join(current_dir, "actions", "system_actions.py")
        )
        system_actions = importlib.util.module_from_spec(spec)

        # 模拟事件处理器
        class MockEventHandler:
            def dispatch_event(self, event_type, data):
                print(f"事件: {event_type}")

        system_actions.get_event_handler = lambda: MockEventHandler()
        system_actions.get_event_type = lambda: type('EventType', (), {
            'SAVE_GAME': 'save_game',
            'LOAD_GAME': 'load_game',
            'ACTION_EXECUTED': 'action_executed'
        })()

        # 执行模块
        spec.loader.exec_module(system_actions)

        # 创建临时目录用于测试
        temp_dir = tempfile.mkdtemp()
        save_manager = system_actions.GameSaveManager(temp_dir)

        # 创建模拟的应用上下文
        class MockAppContext:
            def __init__(self):
                self.total_actions = 42
                self.start_time = 1234567890
                self.session_statistics = {"achievements": {"test": True}}

                # 模拟游戏核心
                self.game_core = MockGameCore()

        class MockGameCore:
            def __init__(self):
                self.difficulty = "normal"
                self.is_game_over = False

                # 模拟角色
                self.character = MockCharacter()

        class MockCharacter:
            def get_status_summary(self):
                return {
                    "name": "测试角色",
                    "realm": "筑基期",
                    "hp": 80,
                    "max_hp": 100,
                    "mp": 50,
                    "max_mp": 60,
                    "exp": 150,
                    "pills": 3,
                    "meditation_streak": 5
                }

        mock_app = MockAppContext()

        # 测试保存功能
        print("  📝 测试保存功能...")
        save_result = save_manager.save_game(mock_app, 1)
        assert save_result["success"], f"保存失败: {save_result['message']}"

        # 验证文件存在
        save_file_path = save_manager._get_save_file_path(1)
        assert os.path.exists(save_file_path), "存档文件不存在"

        # 验证文件内容
        with open(save_file_path, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        assert save_data["version"] == "2.0", "版本号错误"
        assert "game_core" in save_data, "缺少游戏核心数据"
        assert "application" in save_data, "缺少应用层数据"

        print("  ✅ 保存功能测试通过")

        # 测试加载功能
        print("  📂 测试加载功能...")
        load_result = save_manager.load_game(mock_app, 1)
        assert load_result["success"], f"加载失败: {load_result['message']}"
        assert "save_data" in load_result, "缺少存档数据"

        print("  ✅ 加载功能测试通过")

        # 测试存档信息获取
        print("  ℹ️ 测试存档信息获取...")
        save_info = save_manager.get_save_info(1)
        assert save_info is not None, "无法获取存档信息"
        assert save_info["slot"] == 1, "槽位号错误"
        assert save_info["character_name"] == "测试角色", "角色名错误"

        print("  ✅ 存档信息获取测试通过")

        # 测试空槽位
        print("  🕳️ 测试空槽位...")
        empty_info = save_manager.get_save_info(2)
        assert empty_info is None, "空槽位应该返回None"

        print("  ✅ 空槽位测试通过")

        # 清理临时目录
        shutil.rmtree(temp_dir)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_load_actions():
    """测试保存和加载动作"""
    print("🔍 测试保存和加载动作...")

    try:
        # 动态导入system_actions模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "system_actions",
            os.path.join(current_dir, "actions", "system_actions.py")
        )
        system_actions = importlib.util.module_from_spec(spec)

        # 模拟依赖
        system_actions.get_event_handler = lambda: type('EventHandler', (), {
            'dispatch_event': lambda self, event_type, data: None
        })()
        system_actions.get_event_type = lambda: type('EventType', (), {
            'SAVE_GAME': 'save_game',
            'LOAD_GAME': 'load_game',
            'ACTION_EXECUTED': 'action_executed'
        })()

        # 执行模块
        spec.loader.exec_module(system_actions)

        # 创建临时目录
        temp_dir = tempfile.mkdtemp()

        # 创建模拟的应用上下文
        class MockAppContext:
            def __init__(self):
                self.total_actions = 10
                self.start_time = time.time()
                self.game_core = type('GameCore', (), {
                    'character': type('Character', (), {
                        'get_status_summary': lambda self: {
                            "name": "测试角色", "realm": "炼气期"
                        }
                    })(),
                    'difficulty': "normal"
                })()

        mock_app = MockAppContext()

        # 测试保存动作
        print("  💾 测试保存动作...")
        save_action = system_actions.SaveGameAction(slot=1)

        # 重定向存档目录
        original_init = system_actions.GameSaveManager.__init__
        def patched_init(self, save_dir="saves"):
            original_init(self, temp_dir)
        system_actions.GameSaveManager.__init__ = patched_init

        save_result = save_action.execute_system_action(mock_app)
        assert save_result["success"], f"保存动作失败: {save_result['message']}"
        assert save_result["effects"]["game_saved"], "缺少保存效果标记"

        print("  ✅ 保存动作测试通过")

        # 测试加载动作
        print("  📂 测试加载动作...")
        load_action = system_actions.LoadGameAction(slot=1)
        load_result = load_action.execute_system_action(mock_app)
        assert load_result["success"], f"加载动作失败: {load_result['message']}"
        assert load_result["effects"]["game_loaded"], "缺少加载效果标记"

        print("  ✅ 加载动作测试通过")

        # 测试不存在的槽位
        print("  ❌ 测试不存在的槽位...")
        load_action_fail = system_actions.LoadGameAction(slot=99)
        load_result_fail = load_action_fail.execute_system_action(mock_app)
        assert not load_result_fail["success"], "不存在的槽位应该失败"
        assert "没有存档文件" in load_result_fail["message"], "错误消息不正确"

        print("  ✅ 不存在槽位测试通过")

        # 清理临时目录
        shutil.rmtree(temp_dir)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factory_slot_management():
    """测试工厂类的槽位管理"""
    print("🔍 测试工厂类的槽位管理...")

    try:
        # 动态导入system_actions模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "system_actions",
            os.path.join(current_dir, "actions", "system_actions.py")
        )
        system_actions = importlib.util.module_from_spec(spec)

        # 模拟依赖
        system_actions.get_event_handler = lambda: None
        system_actions.get_event_type = lambda: type('EventType', (), {})()

        # 执行模块
        spec.loader.exec_module(system_actions)

        # 测试按名称和槽位获取动作
        print("  🏭 测试按名称和槽位获取动作...")

        save_action_1 = system_actions.SystemActionFactory.get_system_action_by_name("save_game", 1)
        save_action_2 = system_actions.SystemActionFactory.get_system_action_by_name("save_game", 2)

        assert save_action_1.slot == 1, "槽位1动作错误"
        assert save_action_2.slot == 2, "槽位2动作错误"
        assert save_action_1.name == "save_game", "动作名称错误"

        load_action = system_actions.SystemActionFactory.get_system_action_by_name("load_game", 3)
        assert load_action.slot == 3, "加载动作槽位错误"

        restart_action = system_actions.SystemActionFactory.get_system_action_by_name("restart")
        assert restart_action.name == "restart", "重启动作错误"

        print("  ✅ 按名称和槽位获取动作测试通过")

        # 测试获取槽位列表
        print("  📋 测试获取槽位列表...")

        # 这里需要创建临时目录
        temp_dir = tempfile.mkdtemp()
        original_init = system_actions.GameSaveManager.__init__
        def patched_init(self, save_dir="saves"):
            original_init(self, temp_dir)
        system_actions.GameSaveManager.__init__ = patched_init

        slot_list = system_actions.SystemActionFactory.get_save_slot_list()
        assert len(slot_list) == 5, "应该有5个槽位"
        assert all(slot["slot"] in range(1, 6) for slot in slot_list), "槽位号错误"

        # 所有槽位应该都是空的（因为我们没有创建存档）
        assert all(slot.get("empty", False) for slot in slot_list), "所有槽位应该是空的"

        print("  ✅ 获取槽位列表测试通过")

        # 清理
        shutil.rmtree(temp_dir)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始存档系统测试...")
    print("=" * 60)

    # 运行测试
    tests = [
        ("存档管理器", test_save_manager),
        ("保存/加载动作", test_save_load_actions),
        ("工厂槽位管理", test_factory_slot_management),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        print("-" * 40)

        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")

    # 生成报告
    print("\n" + "=" * 60)
    print("📊 存档系统测试报告")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {(passed/total*100):.1f}%")

    if passed == total:
        print("🎉 所有存档系统测试通过！存档功能完整可用。")
        return True
    else:
        print("⚠️  部分测试失败，请检查存档系统实现。")
        return False

if __name__ == "__main__":
    import time
    success = main()
    sys.exit(0 if success else 1)