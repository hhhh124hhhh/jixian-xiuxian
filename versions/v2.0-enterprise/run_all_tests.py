#!/usr/bin/env python3
"""
综合测试运行器
整合所有测试套件，提供完整的测试报告
"""

import sys
import os
import subprocess
import time
from typing import Dict, List, Any
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: int
    total: int
    duration: float
    output: str
    success: bool


class TestSuite:
    """测试套件管理器"""

    def __init__(self):
        self.test_results: List[TestResult] = []

    def add_test_result(self, result: TestResult):
        """添加测试结果"""
        self.test_results.append(result)

    def run_test_script(self, name: str, script_path: str) -> TestResult:
        """运行测试脚本"""
        print(f"\n🔍 运行测试: {name}")
        print("=" * 60)

        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            duration = time.time() - start_time
            output = result.stdout + ("\n" + result.stderr if result.stderr else "")

            # 解析测试结果
            success = result.returncode == 0
            if success:
                # 尝试从输出中提取测试统计
                passed, total = self._parse_test_output(output)
            else:
                passed, total = 0, 1

            test_result = TestResult(
                name=name,
                passed=passed,
                total=total,
                duration=duration,
                output=output,
                success=success
            )

            self._print_test_result(test_result)
            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"❌ 测试超时 (30秒)")
            return TestResult(
                name=name,
                passed=0,
                total=1,
                duration=duration,
                output="测试超时",
                success=False
            )
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ 测试执行异常: {e}")
            return TestResult(
                name=name,
                passed=0,
                total=1,
                duration=duration,
                output=f"执行异常: {e}",
                success=False
            )

    def _parse_test_output(self, output: str) -> tuple:
        """解析测试输出，提取通过和总数"""
        try:
            # 查找类似 "📊 测试结果: X/Y 个测试通过" 的模式
            import re
            pattern = r"测试结果: (\d+)/(\d+) 个测试通过"
            match = re.search(pattern, output)
            if match:
                passed = int(match.group(1))
                total = int(match.group(2))
                return passed, total

            # 查找类似 "✅ 所有X个测试通过！" 的模式
            pattern = r"所有(\d+)个测试通过"
            match = re.search(pattern, output)
            if match:
                total = int(match.group(1))
                return total, total

            # 查找类似 "✅ [name] 成功: X 个断言全部通过" 的模式
            pattern = r"成功: (\d+) 个断言全部通过"
            matches = re.findall(pattern, output)
            if matches:
                total_assertions = sum(int(x) for x in matches)
                return total_assertions, total_assertions

        except Exception:
            pass

        return 1, 1  # 默认值

    def _print_test_result(self, result: TestResult):
        """打印测试结果"""
        if result.success:
            print(f"✅ {result.name} 通过 ({result.passed}/{result.total}) - 用时 {result.duration:.2f}s")
        else:
            print(f"❌ {result.name} 失败 ({result.passed}/{result.total}) - 用时 {result.duration:.2f}s")
            print(f"   错误输出: {result.output[:200]}...")

    def generate_summary_report(self) -> str:
        """生成总结报告"""
        total_tests = sum(r.total for r in self.test_results)
        passed_tests = sum(r.passed for r in self.test_results)
        total_duration = sum(r.duration for r in self.test_results)

        successful_suites = sum(1 for r in self.test_results if r.success)
        total_suites = len(self.test_results)

        report = []
        report.append("=" * 80)
        report.append("🧪 极简修仙 v2.0 综合测试报告")
        report.append("=" * 80)
        report.append(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"⏱️  总耗时: {total_duration:.2f}秒")
        report.append("")

        # 整体统计
        report.append("📊 整体测试统计:")
        report.append(f"   测试套件: {successful_suites}/{total_suites} 通过")
        report.append(f"   测试用例: {passed_tests}/{total_tests} 通过")
        report.append(f"   通过率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   通过率: N/A")
        report.append("")

        # 详细结果
        report.append("📋 详细测试结果:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅ 通过" if result.success else "❌ 失败"
            report.append(f"   {i}. {result.name}: {status} ({result.passed}/{result.total}) - {result.duration:.2f}s")

        report.append("")

        # 失败的测试
        failed_tests = [r for r in self.test_results if not r.success]
        if failed_tests:
            report.append("⚠️  失败的测试:")
            for result in failed_tests:
                report.append(f"   - {result.name}:")
                # 只显示前几行错误信息
                error_lines = result.output.split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        report.append(f"     {line}")
                report.append("")

        # 质量评估
        if successful_suites == total_suites and passed_tests == total_tests:
            report.append("🎉 所有测试通过！代码质量优秀！")
        elif successful_suites >= total_suites * 0.8:
            report.append("✅ 大部分测试通过，代码质量良好。")
        else:
            report.append("⚠️  存在较多测试失败，需要检查代码质量。")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, report: str, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            filename = f"test_report_{int(time.time())}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 测试报告已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存测试报告失败: {e}")


def main():
    """主函数"""
    print("🚀 开始极简修仙 v2.0 综合测试...")
    print("=" * 80)

    # 创建测试套件
    test_suite = TestSuite()

    # 定义所有测试
    tests = [
        ("数据契约一致性测试", "test_data_contract_consistency.py"),
        ("静态字段依赖分析", "static_field_dependency_analyzer.py"),
        ("数据契约集成测试", "run_data_contract_tests.py"),
        ("端到端集成测试", "tests/e2e/test_complete_action_flow.py"),
        ("动作注册机制测试", "test_action_registry.py"),
    ]

    # 检查测试文件是否存在
    available_tests = []
    for name, script in tests:
        if os.path.exists(script):
            available_tests.append((name, script))
        else:
            print(f"⚠️  测试文件不存在: {script}")

    print(f"📋 发现 {len(available_tests)} 个可执行的测试")
    print()

    # 运行所有测试
    for name, script in available_tests:
        result = test_suite.run_test_script(name, script)
        test_suite.add_test_result(result)

    # 生成并显示报告
    print("\n")
    summary_report = test_suite.generate_summary_report()
    print(summary_report)

    # 保存报告
    test_suite.save_report(summary_report)

    # 返回退出码
    failed_tests = sum(1 for r in test_suite.test_results if not r.success)
    return 1 if failed_tests > 0 else 0


if __name__ == "__main__":
    sys.exit(main())