"""
pytest配置文件 - 定义测试夹具和共享配置
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import CharacterStats, GameLog
from actions import ActionFactory, MeditateAction, ConsumePillAction, CultivateAction, WaitAction
from rules import game_rules, difficulty_settings
from core.game_core import GameCore


@pytest.fixture
def character():
    """创建测试角色"""
    character = CharacterStats("测试角色")
    # 设置为已知状态便于测试
    character.health.current_hp = 80
    character.mana.current_mp = 60
    character.inventory.add_item("pill", 3)
    return character


@pytest.fixture
def low_character():
    """创建状态较差的测试角色"""
    character = CharacterStats("低状态角色")
    character.health.current_hp = 20
    character.mana.current_mp = 10
    character.inventory.add_item("pill", 1)
    return character


@pytest.fixture
def dead_character():
    """创建死亡角色"""
    character = CharacterStats("死亡角色")
    character.health.current_hp = 0
    return character


@pytest.fixture
def high_talent_character():
    """创建高资质角色"""
    character = CharacterStats("高资质角色")
    character.talent.base_talent = 10
    return character


@pytest.fixture
def low_talent_character():
    """创建低资质角色"""
    character = CharacterStats("低资质角色")
    character.talent.base_talent = 1
    return character


@pytest.fixture
def game_log():
    """创建游戏日志"""
    return GameLog()


@pytest.fixture
def meditate_action():
    """创建打坐动作"""
    return MeditateAction()


@pytest.fixture
def consume_pill_action():
    """创建吃丹药动作"""
    return ConsumePillAction()


@pytest.fixture
def cultivate_action():
    """创建修炼动作"""
    return CultivateAction()


@pytest.fixture
def wait_action():
    """创建等待动作"""
    return WaitAction()


@pytest.fixture
def all_actions():
    """获取所有动作"""
    return ActionFactory.get_all_actions()


@pytest.fixture
def game_core():
    """创建游戏核心实例"""
    core = GameCore()
    core.initialize_game("测试角色", "normal")
    return core


@pytest.fixture
def game_state(character, game_log, all_actions):
    """创建游戏状态"""
    return {
        "character": character,
        "game_log": game_log,
        "actions": all_actions,
        "is_game_over": False,
        "difficulty": "normal"
    }


# 测试数据
@pytest.fixture
def test_character_data():
    """测试角色数据"""
    return {
        "name": "测试角色",
        "hp": 80,
        "max_hp": 100,
        "mp": 60,
        "max_mp": 100,
        "talent": 5,
        "pills": 3,
        "realm": "炼气期",
        "exp": 25
    }


@pytest.fixture
def expected_action_results():
    """预期的动作结果数据"""
    return {
        "meditate": {
            "hp_cost": 1,
            "min_mp_recovery": 8,
            "max_mp_recovery": 16,  # 资质10时
            "min_exp_gain": 3,
            "max_exp_gain": 11      # 资质10时
        },
        "consume_pill": {
            "pill_cost": 1,
            "min_hp_recovery": 15,
            "max_hp_recovery": 25,  # 资质10时
            "min_mp_recovery": 15,
            "max_mp_recovery": 25,  # 资质10时
            "min_exp_gain": 5,
            "max_exp_gain": 15      # 资质10时
        },
        "cultivate": {
            "mp_cost": 20,
            "min_exp_gain": 12,
            "max_exp_gain": 27      # 资质10时
        },
        "wait": {
            "hp_cost": 1,
            "min_hp_recovery": 2,
            "max_hp_recovery": 4,   # 资质10时
            "min_mp_recovery": 3,
            "max_mp_recovery": 5    # 资质10时
        }
    }


# 测试标记
def pytest_configure(config):
    """配置pytest标记"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )
    config.addinivalue_line(
        "markers", "ui: UI相关测试标记"
    )