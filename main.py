#!/usr/bin/env python3
"""
极简修仙游戏 - 主入口文件
默认运行企业级架构版本 (v2.0)

如需运行简单MVP版本，请访问 versions/v1.0-mvp/ 目录

作者: AI Assistant
版本: 2.0.0 Enterprise
"""

import sys
import os

# 添加v2.0-enterprise目录到Python路径
v2_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "versions", "v2.0-enterprise")
sys.path.insert(0, v2_path)

# 切换到v2.0-enterprise目录运行
os.chdir(v2_path)

from main import main as app_main


def main():
    """主入口函数"""
    print("=" * 60)
    print("           欢迎来到 极简修仙 v2.0 Enterprise")
    print("=" * 60)
    print()
    print("📋 版本信息:")
    print("  - 当前版本: v2.0 Enterprise (企业级架构)")
    print("  - 架构特点: 组件化设计、模块化、测试覆盖")
    print("  - 其他版本: versions/v1.0-mvp/ (单文件MVP)")
    print()

    return app_main()


if __name__ == "__main__":
    sys.exit(main())