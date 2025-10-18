#!/usr/bin/env python3
"""
测试运行脚本
提供便捷的测试运行和报告功能
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("错误输出:")
            print(result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"运行命令时出错: {e}")
        return False


def run_unit_tests(verbosity=2):
    """运行单元测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v" if verbosity > 0 else "-q",
        f"-{'v' * min(verbosity, 4)}",
        "--tb=short",
        "--color=yes"
    ]

    return run_command(cmd, "单元测试")


def run_integration_tests(verbosity=2):
    """运行集成测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v" if verbosity > 0 else "-q",
        f"-{'v' * min(verbosity, 4)}",
        "--tb=short",
        "--color=yes",
        "-m", "not slow"  # 排除慢速测试
    ]

    return run_command(cmd, "集成测试")


def run_all_tests(verbosity=2, include_slow=False):
    """运行所有测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v" if verbosity > 0 else "-q",
        f"-{'v' * min(verbosity, 4)}",
        "--tb=short",
        "--color=yes"
    ]

    if not include_slow:
        cmd.extend(["-m", "not slow"])

    return run_command(cmd, "所有测试")


def run_coverage_report():
    """运行测试覆盖率报告"""
    print("生成测试覆盖率报告...")

    # 安装coverage（如果需要）
    install_cmd = [sys.executable, "-m", "pip", "install", "coverage"]
    run_command(install_cmd, "安装coverage包")

    # 运行覆盖率测试
    coverage_cmd = [
        sys.executable, "-m", "coverage", "run",
        "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ]

    if not run_command(coverage_cmd, "运行覆盖率测试"):
        return False

    # 生成报告
    report_cmd = [sys.executable, "-m", "coverage", "report", "--show-missing"]
    html_cmd = [sys.executable, "-m", "coverage", "html"]

    run_command(report_cmd, "覆盖率报告")
    run_command(html_cmd, "生成HTML覆盖率报告")

    print("\nHTML覆盖率报告已生成到 htmlcov/ 目录")
    return True


def run_specific_test(test_path, verbosity=2):
    """运行特定测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v" if verbosity > 0 else "-q",
        f"-{'v' * min(verbosity, 4)}",
        "--tb=long",
        "--color=yes"
    ]

    return run_command(cmd, f"特定测试: {test_path}")


def check_dependencies():
    """检查测试依赖"""
    print("检查测试依赖...")

    required_packages = ["pytest"]
    optional_packages = ["coverage"]

    missing_required = []
    missing_optional = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"✗ {package} (必需)")

    for package in optional_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"✗ {package} (可选)")

    if missing_required:
        print(f"\n缺少必需依赖: {', '.join(missing_required)}")
        print("请运行: pip install " + " ".join(missing_required))
        return False

    if missing_optional:
        print(f"\n缺少可选依赖: {', '.join(missing_optional)}")
        print("运行覆盖率报告需要: pip install " + " ".join(missing_optional))

    print("\n依赖检查完成!")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="极简修仙游戏测试运行器")

    parser.add_argument(
        "command",
        choices=["unit", "integration", "all", "coverage", "check", "specific"],
        help="要运行的测试类型"
    )

    parser.add_argument(
        "--test-path",
        help="特定测试路径（当command为specific时使用）"
    )

    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        default=2,
        choices=[0, 1, 2, 3, 4],
        help="输出详细程度 (0-4)"
    )

    parser.add_argument(
        "--include-slow",
        action="store_true",
        help="包含慢速测试"
    )

    args = parser.parse_args()

    # 检查依赖
    if not check_dependencies():
        return 1

    success = True

    if args.command == "check":
        # 只检查依赖
        pass

    elif args.command == "unit":
        success = run_unit_tests(args.verbosity)

    elif args.command == "integration":
        success = run_integration_tests(args.verbosity)

    elif args.command == "all":
        success = run_all_tests(args.verbosity, args.include_slow)

    elif args.command == "coverage":
        success = run_coverage_report()

    elif args.command == "specific":
        if not args.test_path:
            print("错误: 使用specific命令时必须指定--test-path")
            return 1
        success = run_specific_test(args.test_path, args.verbosity)

    else:
        print(f"未知命令: {args.command}")
        return 1

    if success:
        print("\n🎉 测试运行成功!")
        return 0
    else:
        print("\n❌ 测试运行失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())