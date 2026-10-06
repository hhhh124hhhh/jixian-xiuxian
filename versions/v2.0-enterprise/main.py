#!/usr/bin/env python3
"""
极简修仙游戏 - 主入口文件
一个基于组件化架构的修仙题材文字RPG游戏

作者: AI Assistant
版本: 1.0.0
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 诊断：检查 pygame 模块状态（pygbag wasm 环境排查用）
try:
    import pygame
    print(f"[DIAG] pygame file: {getattr(pygame, '__file__', 'N/A')}")
    print(f"[DIAG] has init: {hasattr(pygame, 'init')}")
    print(f"[DIAG] has K_1: {hasattr(pygame, 'K_1')}")
    print(f"[DIAG] has Rect: {hasattr(pygame, 'Rect')}")
    print(f"[DIAG] has font: {hasattr(pygame, 'font')}")
    print(f"[DIAG] version: {getattr(pygame, 'version', 'N/A')}")
    try:
        import pygame.constants
        print("[DIAG] import pygame.constants: OK")
    except Exception as e:
        print(f"[DIAG] import pygame.constants FAILED: {e}")
    try:
        import pygame.font
        print("[DIAG] import pygame.font: OK")
    except Exception as e:
        print(f"[DIAG] import pygame.font FAILED: {e}")
except Exception as e:
    print(f"[DIAG] pygame import failed: {e}")

from application import main as app_main


def main():
    """主入口函数"""
    try:
        print("=" * 60)
        print("           欢迎来到 极简修仙 MVP v1.0")
        print("=" * 60)
        print()
        print("游戏说明:")
        print("- 修炼境界: 炼气期 → 筑基期 → 结丹期 → 元婴期 → 化神期 → 飞升")
        print("- 操作指南:")
        print("  * 点击按钮或使用数字键 1-4 执行对应动作")
        print("  * 1: 打坐  2: 吃丹药  3: 修炼  4: 等待")
        print("  * R: 重新开始  ESC: 退出游戏")
        print()
        print("游戏特色:")
        print("- 组件化架构设计，易于扩展")
        print("- 资质影响修炼效率，每局体验不同")
        print("- 策略性资源管理，需要平衡消耗与收益")
        print("- 累积制经验系统，支持长期成长")
        print()
        print("=" * 60)
        print()

        # 运行主应用程序
        exit_code = app_main()

        if exit_code == 0:
            print("\n感谢游玩极简修仙！")
        else:
            print(f"\n游戏异常退出，代码: {exit_code}")

        return exit_code

    except KeyboardInterrupt:
        print("\n\n游戏被用户中断")
        return 130
    except ImportError as e:
        print(f"\n导入模块失败: {e}")
        print("请确保已安装所需的依赖包:")
        print("pip install pygame")
        return 1
    except Exception as e:
        print(f"\n运行游戏时发生错误: {e}")
        print("请检查游戏文件是否完整")
        return 1


if __name__ == "__main__":
    sys.exit(main())
else:
    # 兼容 pygbag：它用 shell.source() 执行本文件，此时 __name__ 不是
    # "__main__"，上面的分支永远不进，游戏根本不会启动。直接跑。
    # main() 内部已区分桌面同步 / 网页异步两种主循环。
    main()