# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于组件化架构的极简修仙文字RPG游戏，采用Python和Pygame开发。游戏实现了角色状态系统、天赋系统、境界系统和实时日志系统，具有完整的MVP功能和扩展性。

## 技术栈

- **Python** - 主要编程语言
- **Pygame** - 游戏开发框架
- **pytest** - 测试框架
- **中文显示** - 使用simhei字体支持中文界面

## 开发环境设置

### 安装依赖
```bash
pip install pygame pytest
```

### 运行游戏
```bash
python main.py
```

### 运行测试
```bash
# 检查依赖
python run_tests.py check

# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 生成测试覆盖率报告
python run_tests.py coverage
```

## 项目结构

```
极简修仙/
├── main.py                     # 主入口文件
├── application.py              # 主应用程序
├── models.py                   # 模型层 - 角色组件系统
├── actions.py                  # 动作系统
├── rules.py                    # 规则引擎
├── ui/                         # UI模块
│   ├── __init__.py
│   ├── interface.py            # UI抽象接口
│   ├── pygame_renderer.py      # Pygame实现
│   ├── layouts.py              # 布局配置
│   └── themes.py               # 主题配置
├── core/                       # 核心逻辑模块
│   ├── __init__.py
│   ├── game_core.py            # 游戏核心逻辑
│   ├── state_manager.py        # 状态管理
│   └── event_handler.py        # 事件处理
├── tests/                      # 测试模块
│   ├── conftest.py             # 测试配置
│   ├── run_tests.py            # 测试运行脚本
│   ├── README.md               # 测试文档
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
├── 模型层.md                    # 模型层设计文档
└── CLAUDE.md                   # 本文件
```

## 系统架构

### 组件化设计
1. **模型层** (`models.py`) - 角色组件系统
   - `HealthComponent` - 生命值管理
   - `ManaComponent` - 仙力值管理
   - `ExperienceComponent` - 经验与境界管理
   - `TalentComponent` - 资质系统
   - `InventoryComponent` - 物品栏管理
   - `GameLog` - 游戏日志

2. **动作系统** (`actions.py`) - 统一的动作接口
   - `MeditateAction` - 打坐
   - `ConsumePillAction` - 服用丹药
   - `CultivateAction` - 修炼
   - `WaitAction` - 等待

3. **规则引擎** (`rules.py`) - 独立的数值计算
   - `GameRule` - 游戏规则计算
   - `DifficultySettings` - 难度设置

4. **UI系统** (`ui/`) - 解耦的界面实现
   - `GameInterface` - UI抽象接口
   - `PygameGameInterface` - Pygame实现
   - `GameStateRenderer` - 状态渲染器

5. **核心逻辑** (`core/`) - 游戏业务逻辑
   - `GameCore` - 游戏核心管理
   - `StateManager` - 状态管理
   - `EventHandler` - 事件处理

### 游戏系统
1. **角色状态系统** - 组件化设计，易于扩展
2. **境界系统** - 炼气期→筑基期→结丹期→元婴期→化神期→飞升
3. **累积经验制** - 支持成就系统和长期成长
4. **操作系统** - 打坐修炼、服用丹药、运转心法、等待
5. **资质系统** - 1-10资质影响各种行为效果
6. **事件系统** - 支持成就和扩展功能

## 开发指南

### 添加新功能
1. **新组件**: 在`models.py`中添加新的组件类
2. **新动作**: 在`actions.py`中添加新的动作类
3. **新规则**: 在`rules.py`中添加新的计算规则
4. **UI更新**: 使用现有的UI组件和接口

### 测试开发
1. 单元测试放在`tests/unit/`目录
2. 集成测试放在`tests/integration/`目录
3. 使用提供的夹具和测试工具
4. 确保测试覆盖率达标

### UI开发
1. 使用`GameInterface`抽象接口，便于后期替换UI框架
2. 布局配置在`ui/layouts.py`中
3. 主题配置在`ui/themes.py`中
4. 渲染逻辑与业务逻辑完全分离

## 配置说明

### 游戏难度
- **简单**: 资质5-10，初始丹药3，经验倍率1.2
- **普通**: 资质1-10，初始丹药1，经验倍率1.0
- **困难**: 资质1-6，初始丹药0，经验倍率0.8

### 主题系统
支持多主题切换，当前包含：
- 默认主题 (明亮配色)
- 深色主题 (暗色配色)

## 快捷键
- **1**: 打坐
- **2**: 吃丹药
- **3**: 修炼
- **4**: 等待
- **R**: 重新开始
- **ESC**: 退出游戏

## 扩展性设计

系统为以下功能预留了接口：
- 时间系统 - 动作消耗时间
- 技能系统 - 动作可升级为技能
- 装备系统 - 装备影响动作效果
- 任务系统 - 事件驱动任务
- 成就系统 - 基于行为统计
- AI支持 - 清晰接口便于算法接入

## 开发注意事项

- 使用组件化架构，模块间低耦合高内聚
- UI与业务逻辑完全分离，便于测试和维护
- 遵循单一职责原则，每个组件职责明确
- 使用pytest进行测试，确保代码质量
- 代码注释详细，便于理解和维护
- 支持中文字体显示，注意跨平台兼容性

## 从旧版本迁移

如果你在使用旧的单一文件版本(`jixian_mvp_pygame.py`)，这里的变化：

1. **架构重构**: 从单一文件重构为组件化架构
2. **功能增强**: 添加了累积经验制、难度系统、主题系统等
3. **测试覆盖**: 添加了完整的测试套件
4. **UI改进**: 更好的界面布局和主题支持
5. **扩展性**: 为未来功能扩展预留了清晰的接口

旧版本的保存数据不兼容，需要重新开始游戏。