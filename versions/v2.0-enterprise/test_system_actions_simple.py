#!/usr/bin/env python3
"""
系统动作简化测试脚本
测试系统动作的基本功能，避免循环导入问题
"""

import sys
import os
import time

def test_system_action_factory():
    """测试系统动作工厂"""
    print("🔍 测试系统动作工厂...")

    # 动态导入system_actions模块
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)

    try:
        # 导入system_actions模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "system_actions",
            os.path.join(current_dir, "actions", "system_actions.py")
        )
        system_actions = importlib.util.module_from_spec(spec)

        # 手动设置依赖
        sys.path.insert(0, os.path.dirname(current_dir))

        # 模拟依赖
        class MockAction:
            def __init__(self, name, description):
                self.name = name
                self.description = description

        class MockEventHandler:
            def dispatch_event(self, event_type, data):
                print(f"事件: {event_type}, 数据: {data}")

        # 设置到模块中
        system_actions.Action = MockAction
        system_actions.event_handler = MockEventHandler()

        # 执行模块
        spec.loader.exec_module(system_actions)

        # 测试工厂方法
        factory = system_actions.SystemActionFactory()
        all_actions = factory.get_all_system_actions()
        print(f"✅ 获取到 {len(all_actions)} 个系统动作")

        # 测试按名称获取
        restart_action = factory.get_system_action_by_name("restart")
        if restart_action:
            print("✅ 成功获取restart动作")

        # 测试系统动作检查
        is_restart = factory.is_system_action("restart")
        is_meditate = factory.is_system_action("meditate")

        assert is_restart == True, "restart应该是系统动作"
        assert is_meditate == False, "meditate不应该是系统动作"
        print("✅ 系统动作检查功能正常")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_button_type_constants():
    """测试按钮类型常量"""
    print("🔍 测试按钮类型常量...")

    try:
        # 动态导入ui.interface模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "ui.interface",
            os.path.join(os.path.dirname(__file__), "ui", "interface.py")
        )
        ui_interface = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ui_interface)

        # 测试ButtonType常量
        game_action = ui_interface.ButtonType.GAME_ACTION
        system_action = ui_interface.ButtonType.SYSTEM_ACTION

        assert game_action == "game_action", "GAME_ACTION常量值错误"
        assert system_action == "system_action", "SYSTEM_ACTION常量值错误"

        print("✅ 按钮类型常量正确")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_event_types():
    """测试事件类型"""
    print("🔍 测试事件类型...")

    try:
        # 动态导入core.event_handler模块
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "core.event_handler",
            os.path.join(os.path.dirname(__file__), "core", "event_handler.py")
        )
        event_handler_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(event_handler_module)

        # 测试系统事件类型
        event_type = event_handler_module.EventType

        # 检查新增的系统事件类型
        system_events = [
            "RESTART_REQUESTED",
            "SETTINGS_REQUESTED",
            "SAVE_GAME",
            "LOAD_GAME"
        ]

        for event_name in system_events:
            if hasattr(event_type, event_name):
                print(f"✅ 事件类型 {event_name} 存在")
            else:
                print(f"❌ 事件类型 {event_name} 不存在")
                return False

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构完整性"""
    print("🔍 测试文件结构完整性...")

    required_files = [
        "actions/system_actions.py",
        "actions/__init__.py",
        "ui/interface.py",
        "ui/pygame_renderer.py",
        "application.py",
        "core/event_handler.py"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ 缺失文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

def main():
    """主函数"""
    print("🚀 开始系统动作简化测试...")
    print("=" * 60)

    # 运行测试
    tests = [
        ("文件结构完整性", test_file_structure),
        ("事件类型", test_event_types),
        ("按钮类型常量", test_button_type_constants),
        ("系统动作工厂", test_system_action_factory),
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
    print("📊 系统动作简化测试报告")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print(f"通过率: {(passed/total*100):.1f}%")

    if passed == total:
        print("🎉 所有基础测试通过！系统动作架构正确实现。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)