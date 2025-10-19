"""
动作模块
包含游戏动作和系统动作的定义
"""

# 从actions.py导入主要类，避免循环导入问题
try:
    # 尝试从actions.py导入主要类
    import sys
    import os
    import importlib.util

    # 获取actions.py的路径
    actions_py_path = os.path.join(os.path.dirname(__file__), '..', 'actions.py')

    if os.path.exists(actions_py_path):
        spec = importlib.util.spec_from_file_location("actions_module", actions_py_path)
        actions_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(actions_module)

        # 导出主要类
        Action = actions_module.Action
        ActionFactory = actions_module.ActionFactory
        MeditateAction = actions_module.MeditateAction
        ConsumePillAction = actions_module.ConsumePillAction
        CultivateAction = actions_module.CultivateAction
        WaitAction = actions_module.WaitAction

        # 定义__all__
        __all__ = [
            'Action',
            'ActionFactory',
            'MeditateAction',
            'ConsumePillAction',
            'CultivateAction',
            'WaitAction'
        ]
    else:
        raise ImportError("actions.py not found")

except ImportError as e:
    print(f"警告: 无法导入actions.py内容: {e}")

    # 提供最小化的兼容类
    class Action:
        def __init__(self, name: str, description: str):
            self.name = name
            self.description = description

    class ActionFactory:
        @staticmethod
        def get_all_actions():
            return []

    __all__ = ['Action', 'ActionFactory']