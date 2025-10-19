#!/usr/bin/env python3
"""
数据契约一致性测试脚本
用于检测各层之间的数据字段契约不一致问题
"""

import sys
import os
import ast
import re
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class DataFieldUsage:
    """数据字段使用信息"""
    field_name: str
    file_path: str
    line_number: int
    usage_type: str  # 'read', 'write', 'expected'
    context: str

@dataclass
class DataContract:
    """数据契约定义"""
    provider_method: str
    provider_file: str
    consumer_method: str
    consumer_file: str
    expected_fields: List[str]
    provided_fields: List[str]
    missing_fields: List[str]
    extra_fields: List[str]

class DataContractAnalyzer:
    """数据契约分析器"""

    def __init__(self):
        self.field_usages: List[DataFieldUsage] = []
        self.data_contracts: List[DataContract] = []

    def scan_python_file(self, file_path: str) -> List[DataFieldUsage]:
        """扫描Python文件中的数据字段使用"""
        usages = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')

            # 查找status[...]模式的字段访问
            status_pattern = r'status\[(["\'])(\w+)\1\]'
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(status_pattern, line)
                for match in matches:
                    field_name = match.group(2)
                    usages.append(DataFieldUsage(
                        field_name=field_name,
                        file_path=file_path,
                        line_number=line_num,
                        usage_type='read',
                        context=line.strip()
                    ))

        except Exception as e:
            print(f"扫描文件 {file_path} 时出错: {e}")

        return usages

    def analyze_get_status_summary(self) -> Dict[str, List[str]]:
        """分析get_status_summary方法提供的字段"""
        # 使用动态导入直接获取字段
        try:
            from models import CharacterStats
            char = CharacterStats('测试角色')
            status = char.get_status_summary()
            return {'provided_fields': list(status.keys())}
        except Exception as e:
            print(f"分析get_status_summary时出错: {e}")
            return {'provided_fields': []}

    def analyze_ui_expected_fields(self) -> Dict[str, List[str]]:
        """分析UI层期望的字段"""
        # 扫描UI相关文件
        ui_files = ['ui/interface.py', 'ui/pygame_renderer.py']
        expected_fields = set()

        for ui_file in ui_files:
            file_path = os.path.join(os.path.dirname(__file__), ui_file)
            if os.path.exists(file_path):
                usages = self.scan_python_file(file_path)
                for usage in usages:
                    if usage.usage_type == 'read':
                        expected_fields.add(usage.field_name)

        return {'expected_fields': list(expected_fields)}

    def analyze_character_display_info(self) -> Dict[str, List[str]]:
        """分析CharacterDisplayInfo期望的字段"""
        interface_path = os.path.join(os.path.dirname(__file__), 'ui/interface.py')

        try:
            with open(interface_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找CharacterDisplayInfo类定义
            pattern = r'class CharacterDisplayInfo.*?:\s*\((.*?)\):'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                fields_str = match.group(1)
                # 提取所有字段名
                field_pattern = r'(\w+)\s*:'
                fields = re.findall(field_pattern, fields_str)
                return {'character_display_info_fields': fields}

        except Exception as e:
            print(f"分析CharacterDisplayInfo时出错: {e}")

        return {'character_display_info_fields': []}

    def run_contract_analysis(self) -> List[DataContract]:
        """运行数据契约分析"""
        contracts = []

        # 分析get_status_summary提供的字段
        status_analysis = self.analyze_get_status_summary()
        provided_fields = set(status_analysis['provided_fields'])

        # 分析UI层期望的字段
        ui_analysis = self.analyze_ui_expected_fields()
        expected_fields = set(ui_analysis['expected_fields'])

        # 分析CharacterDisplayInfo字段
        display_info_analysis = self.analyze_character_display_info()
        display_info_fields = set(display_info_analysis['character_display_info_fields'])

        # 创建数据契约（只关注缺失字段，多余字段是正常的）
        missing_fields = expected_fields - provided_fields

        if missing_fields:
            contracts.append(DataContract(
                provider_method="CharacterStats.get_status_summary()",
                provider_file="models.py",
                consumer_method="UI层",
                consumer_file="ui/interface.py, ui/pygame_renderer.py",
                expected_fields=list(expected_fields),
                provided_fields=list(provided_fields),
                missing_fields=list(missing_fields),
                extra_fields=[]  # 多余字段是正常的
            ))

        # 专门分析CharacterDisplayInfo契约（只关注缺失字段）
        missing_display_fields = display_info_fields - provided_fields

        if missing_display_fields:
            contracts.append(DataContract(
                provider_method="CharacterStats.get_status_summary()",
                provider_file="models.py",
                consumer_method="UIRenderer.format_character_info()",
                consumer_file="ui/interface.py",
                expected_fields=list(display_info_fields),
                provided_fields=list(provided_fields),
                missing_fields=list(missing_display_fields),
                extra_fields=[]  # 多余字段是正常的
            ))

        return contracts

    def generate_test_report(self, contracts: List[DataContract]) -> str:
        """生成测试报告"""
        report = ["=" * 80]
        report.append("🔍 数据契约一致性测试报告")
        report.append("=" * 80)
        report.append("")

        if not contracts:
            report.append("✅ 所有数据契约检查通过，没有发现不一致问题。")
        else:
            report.append(f"❌ 发现 {len(contracts)} 个数据契约问题：")
            report.append("")

            for i, contract in enumerate(contracts, 1):
                report.append(f"📋 问题 {i}: {contract.provider_method} → {contract.consumer_method}")
                report.append(f"   提供方: {contract.provider_file}")
                report.append(f"   消费方: {contract.consumer_file}")
                report.append("")

                if contract.missing_fields:
                    report.append(f"   🔴 缺失字段: {', '.join(contract.missing_fields)}")
                if contract.extra_fields:
                    report.append(f"   🟡 多余字段: {', '.join(contract.extra_fields)}")

                report.append("")

        report.append("=" * 80)
        return "\n".join(report)

def main():
    """主函数"""
    print("🔍 开始数据契约一致性分析...")

    analyzer = DataContractAnalyzer()

    # 运行分析
    contracts = analyzer.run_contract_analysis()

    # 生成报告
    report = analyzer.generate_test_report(contracts)
    print(report)

    # 保存报告到文件
    report_path = os.path.join(os.path.dirname(__file__), 'data_contract_report.txt')
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 详细报告已保存到: {report_path}")
    except Exception as e:
        print(f"保存报告失败: {e}")

    # 返回退出码
    return 1 if contracts else 0

if __name__ == "__main__":
    sys.exit(main())