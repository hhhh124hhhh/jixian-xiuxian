# 测试文档

## 概述

本文档描述了极简修仙游戏的测试策略、测试结构和运行方法。

## 测试结构

```
tests/
├── __init__.py              # 测试模块初始化
├── conftest.py              # pytest配置和共享夹具
├── README.md                # 测试文档（本文件）
├── unit/                    # 单元测试
│   ├── test_models.py       # 模型组件测试
│   ├── test_actions.py      # 动作系统测试
│   ├── test_rules.py        # 规则引擎测试
│   └── test_game_core.py    # 游戏核心测试
└── integration/             # 集成测试
    ├── __init__.py
    ├── test_game_flow.py    # 游戏流程集成测试
    └── test_ui_integration.py # UI与逻辑交互测试
```

## 测试分类

### 单元测试 (`tests/unit/`)

- **test_models.py**: 测试所有模型组件
  - `HealthComponent`: 生命值组件测试
  - `ManaComponent`: 仙力值组件测试
  - `ExperienceComponent`: 经验值组件测试
  - `TalentComponent`: 资质组件测试
  - `InventoryComponent`: 物品栏组件测试
  - `CharacterStats`: 角色状态测试
  - `GameLog`: 游戏日志测试

- **test_actions.py**: 测试动作系统
  - `MeditateAction`: 打坐动作测试
  - `ConsumePillAction`: 服用丹药动作测试
  - `CultivateAction`: 修炼动作测试
  - `WaitAction`: 等待动作测试
  - `ActionFactory`: 动作工厂测试

- **test_rules.py**: 测试规则引擎
  - `GameRule`: 游戏规则测试
  - `DifficultySettings`: 难度设置测试
  - 边界情况测试

- **test_game_core.py**: 测试游戏核心
  - `GameCore`: 游戏核心逻辑测试
  - `GameStateManager`: 状态管理器测试

### 集成测试 (`tests/integration/`)

- **test_game_flow.py**: 测试完整游戏流程
  - 完整游戏会话测试
  - 难度影响测试
  - 角色死亡流程测试
  - 境界突破流程测试
  - 资源管理流程测试
  - 动作序列优化测试
  - 边缘场景测试
  - 应用程序集成测试

- **test_ui_integration.py**: 测试UI与逻辑交互
  - `GameStateRenderer`: 游戏状态渲染器测试
  - UI布局集成测试
  - 主题系统集成测试
  - 字体系统集成测试
  - UI组件交互测试

## 测试标记

使用pytest标记来分类测试：

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.ui`: UI相关测试

## 运行测试

### 使用测试运行脚本（推荐）

```bash
# 检查测试依赖
python run_tests.py check

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 运行所有测试（不包括慢速测试）
python run_tests.py all

# 运行所有测试（包括慢速测试）
python run_tests.py all --include-slow

# 生成测试覆盖率报告
python run_tests.py coverage

# 运行特定测试
python run_tests.py specific --test-path tests/unit/test_models.py

# 设置输出详细程度
python run_tests.py unit -v 3
```

### 直接使用pytest

```bash
# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 运行特定测试文件
pytest tests/unit/test_models.py -v

# 运行特定测试类
pytest tests/unit/test_models.py::TestHealthComponent -v

# 运行特定测试方法
pytest tests/unit/test_models.py::TestHealthComponent::test_initialization -v

# 按标记运行测试
pytest -m unit -v
pytest -m integration -v
pytest -m "not slow" -v

# 生成覆盖率报告
coverage run -m pytest tests/
coverage report
coverage html
```

## 测试夹具

### 角色夹具

- `character`: 正常状态的测试角色
- `low_character`: 状态较差的测试角色
- `dead_character`: 死亡角色
- `high_talent_character`: 高资质角色
- `low_talent_character`: 低资质角色

### 动作夹具

- `meditate_action`: 打坐动作
- `consume_pill_action`: 服用丹药动作
- `cultivate_action`: 修炼动作
- `wait_action`: 等待动作
- `all_actions`: 所有动作

### 其他夹具

- `game_log`: 游戏日志实例
- `game_core`: 游戏核心实例
- `game_state`: 游戏状态数据

## 测试覆盖率

项目使用coverage.py来测量测试覆盖率：

```bash
# 运行覆盖率测试
coverage run -m pytest tests/

# 查看覆盖率报告
coverage report

# 生成HTML报告
coverage html
```

目标覆盖率：
- 核心逻辑覆盖率 ≥ 95%
- 组件覆盖率 ≥ 90%
- UI相关覆盖率 ≥ 80%

## 测试最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 遵循 `test_[功能]_[场景]` 的命名模式
- 例如: `test_health_restore_normal_amount`

### 2. 测试结构

使用AAA模式（Arrange, Act, Assert）：

```python
def test_health_restore_normal_amount(self):
    # Arrange - 准备测试数据
    health = HealthComponent(100)
    health.current_hp = 50

    # Act - 执行测试操作
    restored = health.restore(20)

    # Assert - 验证结果
    assert restored == 20
    assert health.current_hp == 70
```

### 3. 边界测试

- 测试正常情况
- 测试边界情况
- 测试异常情况

### 4. 独立性

- 每个测试应该独立运行
- 不依赖测试执行顺序
- 使用夹具确保测试隔离

### 5. 可重复性

- 测试结果应该一致
- 避免依赖外部状态
- 使用确定性的测试数据

## 持续集成

测试应该在每个代码提交时运行：

```bash
# 在CI/CD流水线中
python run_tests.py check && python run_tests.py unit && python run_tests.py integration
```

## 调试测试

### 运行单个测试

```bash
pytest -s tests/unit/test_models.py::TestHealthComponent::test_initialization
```

### 使用pdb调试

```bash
pytest --pdb tests/unit/test_models.py::TestHealthComponent::test_initialization
```

### 查看详细输出

```bash
pytest -v -s tests/unit/test_models.py
```

## 添加新测试

1. 确定测试类型（单元测试或集成测试）
2. 选择合适的测试文件或创建新的测试文件
3. 使用现有的夹具或创建新的夹具
4. 编写测试方法
5. 运行测试确保通过
6. 检查测试覆盖率

## 测试数据

测试使用固定的、可预测的数据：

- 角色名称: "测试角色"
- 固定的属性值
- 可复现的场景

这确保了测试的一致性和可重复性。

## 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录在Python路径中
2. **依赖缺失**: 运行 `python run_tests.py check` 检查依赖
3. **权限问题**: 确保有写入权限（用于生成覆盖率报告）

### 获取帮助

```bash
# 查看pytest帮助
pytest --help

# 查看测试运行器帮助
python run_tests.py --help
```