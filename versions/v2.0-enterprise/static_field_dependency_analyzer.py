#!/usr/bin/env python3
"""
静态数据字段依赖分析工具
用于在开发阶段检查字段依赖关系和潜在问题
"""

import os
import re
import ast
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FieldReference:
    """字段引用信息"""
    field_name: str
    file_path: str
    line_number: int
    context: str
    reference_type: str  # 'status_access', 'template_usage', 'definition'

@dataclass
class FieldDependency:
    """字段依赖关系"""
    source_field: str
    source_file: str
    target_fields: List[str]
    target_files: List[str]
    dependency_type: str

class StaticFieldAnalyzer:
    """静态字段分析器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.field_references: List[FieldReference] = []
        self.dependencies: List[FieldDependency] = []

    def find_python_files(self) -> List[str]:
        """查找所有Python文件"""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # 跳过测试目录和__pycache__
            dirs[:] = [d for d in dirs if not d.startswith('__') and d != 'tests']

            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        return python_files

    def analyze_file(self, file_path: str) -> List[FieldReference]:
        """分析单个文件的字段引用"""
        references = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 1. 查找status[...]访问模式
            status_pattern = r'status\[(["\'])(\w+)\1\]'
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(status_pattern, line)
                for match in matches:
                    field_name = match.group(2)
                    references.append(FieldReference(
                        field_name=field_name,
                        file_path=file_path,
                        line_number=line_num,
                        context=line.strip(),
                        reference_type='status_access'
                    ))

            # 2. 查找模板字符串中的字段使用
            template_patterns = [
                r'\{(\w+)\}',  # 简单字段
                r'\{(\w+)\:[^}]*\}',  # 带格式的字段
            ]

            for line_num, line in enumerate(lines, 1):
                if 'template' in line.lower() or 'format' in line.lower():
                    for pattern in template_patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            field_name = match.group(1)
                            if field_name.isalpha():  # 确保是纯字段名
                                references.append(FieldReference(
                                    field_name=field_name,
                                    file_path=file_path,
                                    line_number=line_num,
                                    context=line.strip(),
                                    reference_type='template_usage'
                                ))

            # 3. 查找字段定义（在return语句中）
            for line_num, line in enumerate(lines, 1):
                if '"\\w+"\\s*:' in line or (line.strip().startswith('"') and ':' in line):
                    # 简单的字段定义检测
                    field_def_pattern = r'"(\w+)"\s*:'
                    matches = re.finditer(field_def_pattern, line)
                    for match in matches:
                        field_name = match.group(1)
                        references.append(FieldReference(
                            field_name=field_name,
                            file_path=file_path,
                            line_number=line_num,
                            context=line.strip(),
                            reference_type='definition'
                        ))

        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")

        return references

    def analyze_all_files(self) -> Dict[str, List[FieldReference]]:
        """分析所有文件的字段引用"""
        all_references = {}
        python_files = self.find_python_files()

        print(f"🔍 分析 {len(python_files)} 个Python文件...")

        for file_path in python_files:
            relative_path = os.path.relpath(file_path, self.project_root)
            references = self.analyze_file(file_path)
            if references:
                all_references[relative_path] = references
                self.field_references.extend(references)

        return all_references

    def find_field_dependencies(self) -> List[FieldDependency]:
        """查找字段依赖关系"""
        dependencies = []

        # 按字段名分组引用
        field_groups: Dict[str, List[FieldReference]] = {}
        for ref in self.field_references:
            if ref.field_name not in field_groups:
                field_groups[ref.field_name] = []
            field_groups[ref.field_name].append(ref)

        # 分析每个字段的依赖关系
        for field_name, refs in field_groups.items():
            # 查找定义和访问
            definitions = [r for r in refs if r.reference_type == 'definition']
            accesses = [r for r in refs if r.reference_type in ['status_access', 'template_usage']]

            if definitions and accesses:
                # 创建从定义到访问的依赖
                for def_ref in definitions:
                    target_fields = []
                    target_files = []

                    for access_ref in accesses:
                        if access_ref.file_path != def_ref.file_path:
                            target_fields.append(access_ref.field_name)
                            target_files.append(access_ref.file_path)

                    if target_fields:
                        dependencies.append(FieldDependency(
                            source_field=field_name,
                            source_file=def_ref.file_path,
                            target_fields=list(set(target_fields)),
                            target_files=list(set(target_files)),
                            dependency_type='definition_to_usage'
                        ))

        return dependencies

    def detect_potential_issues(self) -> List[str]:
        """检测潜在问题"""
        issues = []

        # 按字段名分组
        field_groups: Dict[str, List[FieldReference]] = {}
        for ref in self.field_references:
            if ref.field_name not in field_groups:
                field_groups[ref.field_name] = []
            field_groups[ref.field_name].append(ref)

        # 检查1: 只有访问没有定义的字段
        print("\n🔍 检查字段定义完整性...")
        for field_name, refs in field_groups.items():
            definitions = [r for r in refs if r.reference_type == 'definition']
            accesses = [r for r in refs if r.reference_type in ['status_access', 'template_usage']]

            if accesses and not definitions:
                files_using = set(r.file_path for r in accesses)
                issues.append(f"⚠️  字段 '{field_name}' 被访问但未定义 (使用于: {', '.join(files_using)})")

        # 检查2: 可能的拼写错误
        print("\n🔍 检查可能的拼写错误...")
        common_fields = {'name', 'hp', 'mp', 'exp', 'realm', 'talent', 'pills', 'level', 'power'}
        for field_name in field_groups.keys():
            if field_name not in common_fields:
                # 检查是否是常见字段的拼写错误
                for common_field in common_fields:
                    if self._is_similar(field_name, common_field):
                        issues.append(f"🔍 可能的拼写错误: '{field_name}' (应为 '{common_field}'?)")

        # 检查3: 特殊模式检查
        print("\n🔍 检查特殊模式...")

        # 检查exp_threshold相关（我们已知的问题）
        exp_threshold_refs = field_groups.get('exp_threshold', [])
        if exp_threshold_refs:
            exp_progress_refs = field_groups.get('exp_progress', [])
            if exp_progress_refs:
                issues.append(f"🎯 发现exp_threshold使用 (已在修复中): {len(exp_threshold_refs)}处引用")

        return issues

    def analyze_action_contract_consistency(self) -> Dict[str, Any]:
        """分析动作契约一致性"""
        print("\n🔍 分析动作契约一致性...")

        try:
            from actions import ActionFactory
            from ui.layouts import default_layout
            from ui.pygame_renderer import PygameInputHandler

            # 获取后端定义的动作
            backend_actions = {}
            for action in ActionFactory.get_all_actions():
                backend_actions[action.name] = {
                    'class_name': action.__class__.__name__,
                    'description': action.description,
                    'file_path': 'actions.py'
                }

            # 获取UI层定义的动作
            ui_actions = {}
            for button in default_layout.ACTION_BUTTONS:
                action_name = button["action"]
                if action_name in backend_actions:  # 只关注游戏动作
                    ui_actions[action_name] = {
                        'display_name': button["name"],
                        'description': button["description"],
                        'file_path': 'ui/layouts.py'
                    }

            # 获取快捷键映射
            renderer = PygameInputHandler(default_layout)
            shortcut_actions = {}
            for key_code, action_name in renderer.shortcuts.items():
                if action_name in backend_actions:  # 只关注游戏动作
                    shortcut_actions[action_name] = {
                        'key_code': key_code,
                        'key_name': f"pygame.K_{key_code}",
                        'file_path': 'ui/pygame_renderer.py'
                    }

            # 检查一致性
            consistency_results = {
                'backend_actions': backend_actions,
                'ui_actions': ui_actions,
                'shortcut_actions': shortcut_actions,
                'issues': [],
                'missing_in_ui': [],
                'missing_in_backend': [],
                'missing_shortcuts': []
            }

            # 检查后端动作在UI层是否存在
            for action_name in backend_actions.keys():
                if action_name not in ui_actions:
                    consistency_results['missing_in_ui'].append(action_name)
                    consistency_results['issues'].append(f"⚠️  后端动作 '{action_name}' 在UI层没有对应的按钮")

                if action_name not in shortcut_actions:
                    consistency_results['missing_shortcuts'].append(action_name)
                    consistency_results['issues'].append(f"⚠️  后端动作 '{action_name}' 没有对应的快捷键")

            # 检查UI层动作在后端是否存在
            for action_name in ui_actions.keys():
                if action_name not in backend_actions:
                    consistency_results['missing_in_backend'].append(action_name)
                    consistency_results['issues'].append(f"⚠️  UI动作 '{action_name}' 在后端没有对应的实现")

            return consistency_results

        except Exception as e:
            print(f"分析动作契约时出错: {e}")
            return {
                'backend_actions': {},
                'ui_actions': {},
                'shortcut_actions': {},
                'issues': [f"分析动作契约时出错: {e}"],
                'missing_in_ui': [],
                'missing_in_backend': [],
                'missing_shortcuts': []
            }

    def find_hardcoded_action_strings(self) -> List[Dict[str, Any]]:
        """查找硬编码的动作字符串"""
        print("\n🔍 查找硬编码的动作字符串...")

        hardcoded_strings = []
        action_names = {'meditate', 'consume_pill', 'cultivate', 'wait'}

        for ref in self.field_references:
            # 检查是否是硬编码的动作名称
            if (ref.field_name in action_names or
                ref.reference_type in ['status_access', 'template_usage']):

                # 检查上下文是否包含动作名称
                context_lower = ref.context.lower()
                for action_name in action_names:
                    if action_name in context_lower:
                        hardcoded_strings.append({
                            'action_name': action_name,
                            'file_path': ref.file_path,
                            'line_number': ref.line_number,
                            'context': ref.context,
                            'reference_type': ref.reference_type
                        })
                        break

        return hardcoded_strings

    def _is_similar(self, str1: str, str2: str) -> bool:
        """检查两个字符串是否相似（拼写错误检测）"""
        # 简单的编辑距离检测
        if abs(len(str1) - len(str2)) > 2:
            return False

        common_chars = set(str1) & set(str2)
        similarity = len(common_chars) / max(len(set(str1)), len(set(str2)))
        return similarity > 0.7

    def generate_analysis_report(self) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 80)
        report.append("🔬 静态字段依赖分析报告")
        report.append("=" * 80)
        report.append(f"📁 项目路径: {self.project_root}")
        report.append(f"📄 分析文件数: {len(set(r.file_path for r in self.field_references))}")
        report.append(f"🔤 发现字段数: {len(set(r.field_name for r in self.field_references))}")
        report.append(f"📝 总引用数: {len(self.field_references)}")
        report.append("")

        # 字段使用统计
        field_counts: Dict[str, int] = {}
        for ref in self.field_references:
            field_counts[ref.field_name] = field_counts.get(ref.field_name, 0) + 1

        report.append("📊 字段使用频率 TOP 10:")
        sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for field_name, count in sorted_fields:
            report.append(f"   {field_name}: {count} 次")
        report.append("")

        # 依赖关系
        dependencies = self.find_field_dependencies()
        report.append(f"🔗 发现 {len(dependencies)} 个字段依赖关系:")
        for dep in dependencies[:5]:  # 显示前5个
            report.append(f"   {dep.source_field} ({os.path.basename(dep.source_file)}) → {', '.join(dep.target_files)}")
        report.append("")

        # 动作契约一致性分析
        action_analysis = self.analyze_action_contract_consistency()
        report.append("🎮 动作契约一致性分析:")
        report.append(f"   后端定义动作: {len(action_analysis['backend_actions'])} 个")
        report.append(f"   UI层按钮动作: {len(action_analysis['ui_actions'])} 个")
        report.append(f"   快捷键映射动作: {len(action_analysis['shortcut_actions'])} 个")

        if action_analysis['issues']:
            report.append("")
            report.append("⚠️  动作契约问题:")
            for issue in action_analysis['issues']:
                report.append(f"   {issue}")
        else:
            report.append("✅ 动作契约完全一致")

        # 硬编码动作字符串
        hardcoded_actions = self.find_hardcoded_action_strings()
        if hardcoded_actions:
            report.append("")
            report.append(f"🔍 发现 {len(hardcoded_actions)} 处硬编码动作字符串:")
            for i, action_str in enumerate(hardcoded_actions[:5]):  # 显示前5个
                report.append(f"   {action_str['action_name']} 在 {action_str['file_path']}:{action_str['line_number']}")
        else:
            report.append("")
            report.append("✅ 未发现硬编码动作字符串问题")

        # 其他潜在问题
        issues = self.detect_potential_issues()
        if issues:
            report.append("")
            report.append("⚠️  其他潜在问题:")
            for issue in issues:
                report.append(f"   {issue}")
        else:
            report.append("")
            report.append("✅ 未发现其他字段依赖问题")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

def main():
    """主函数"""
    print("🔬 开始静态字段依赖分析...")

    project_root = os.path.dirname(os.path.abspath(__file__))
    analyzer = StaticFieldAnalyzer(project_root)

    # 分析所有文件
    all_references = analyzer.analyze_all_files()

    # 生成报告
    report = analyzer.generate_analysis_report()
    print("\n" + report)

    # 保存报告
    report_path = os.path.join(project_root, 'field_dependency_report.txt')
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 详细报告已保存到: {report_path}")
    except Exception as e:
        print(f"保存报告失败: {e}")

if __name__ == "__main__":
    main()