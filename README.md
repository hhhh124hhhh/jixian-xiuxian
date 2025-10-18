# 极简修仙 - 多版本架构游戏

## 项目概述

这是一个基于Python和Pygame开发的修仙题材文字RPG游戏，提供了多种架构版本以满足不同需求：

- **v1.0 MVP**: 单文件实现，轻量级，适合快速原型和学习
- **v2.0 Enterprise**: 组件化企业级架构，功能完整，易于扩展

## 🚀 快速开始

### 安装依赖

```bash
# 安装v2.0企业级版本依赖（推荐）
pip install pygame pytest

# 或安装v1.0 MVP版本依赖
pip install pygame
```

### 运行游戏

#### 方法一：运行企业级版本（默认推荐）
```bash
python main.py
```

#### 方法二：运行简单MVP版本
```bash
cd versions/v1.0-mvp
python jixian_mvp_pygame.py
```

#### 方法三：直接运行企业级版本
```bash
cd versions/v2.0-enterprise
python main.py
```

## 📁 项目结构

```
极简修仙/
├── main.py                           # 主入口文件（运行v2.0版本）
├── README.md                         # 项目总体说明
├── CLAUDE.md                         # Claude开发指南
├── versions/                         # 版本分层目录
│   ├── v1.0-mvp/                     # 简单MVP版本
│   │   ├── jixian_mvp_pygame.py      # 单文件实现（148行）
│   │   ├── README_v1.md              # v1.0版本说明
│   │   └── requirements.txt          # v1.0依赖
│   │
│   └── v2.0-enterprise/              # 企业级架构版本
│       ├── main.py                   # v2.0主入口
│       ├── application.py            # 主应用程序
│       ├── models.py                 # 模型层
│       ├── actions.py                # 动作系统
│       ├── rules.py                  # 规则引擎
│       ├── run_tests.py              # 测试运行脚本
│       ├── 模型层.md                  # 设计文档
│       ├── requirements.txt          # v2.0依赖
│       ├── ui/                       # UI模块
│       ├── core/                     # 核心逻辑模块
│       └── tests/                    # 测试模块
└── 配置文件...
```

## 🎮 游戏特性

### 核心系统
- **境界系统**: 炼气期 → 筑基期 → 结丹期 → 元婴期 → 化神期 → 飞升
- **角色状态**: 生命值、仙力值、经验值、丹药数量
- **操作系统**: 打坐修炼、服用丹药、运转心法、等待
- **资质系统**: 1-10资质影响修炼效率
- **日志系统**: 实时显示游戏事件

### 操作方式
- **鼠标点击**: 点击按钮执行对应动作
- **快捷键**:
  - 1: 打坐
  - 2: 吃丹药
  - 3: 修炼
  - 4: 等待
  - R: 重新开始
  - ESC: 退出游戏

## 📊 版本对比

| 特性 | v1.0 MVP | v2.0 Enterprise |
|------|----------|-----------------|
| 架构设计 | 单文件 | 组件化模块化 |
| 代码量 | 148行 | 1500+行 |
| 测试覆盖 | 无 | 完整测试套件 |
| 扩展性 | 有限 | 高度可扩展 |
| 文档完整性 | 基础 | 详细文档 |
| 主题系统 | 无 | 多主题支持 |
| 难度设置 | 固定 | 多难度可选 |
| 事件系统 | 无 | 完整事件系统 |
| 成就系统 | 无 | 成就框架 |

## 🛠️ 开发指南

### 选择合适的版本

**选择v1.0 MVP的情况：**
- 学习游戏开发基础
- 快速原型开发
- 简单需求实现
- 代码阅读理解

**选择v2.0 Enterprise的情况：**
- 正式项目开发
- 团队协作开发
- 复杂功能扩展
- 生产环境部署

### 测试运行（仅v2.0版本）

```bash
cd versions/v2.0-enterprise

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

### 扩展开发

**v1.0版本扩展：**
- 直接修改`jixian_mvp_pygame.py`文件
- 适合添加简单的功能

**v2.0版本扩展：**
- 遵循组件化架构设计
- 在相应模块中添加新功能
- 编写相应的测试用例
- 更新相关文档

## 📈 技术栈

### 共同技术
- **Python 3.x** - 主要编程语言
- **Pygame** - 游戏开发框架
- **中文显示** - simhei字体支持

### v2.0企业级版本额外技术
- **pytest** - 测试框架
- **组件化架构** - 模块化设计
- **事件驱动** - 解耦的事件系统
- **抽象接口** - UI与业务逻辑分离

## 🤝 贡献指南

1. Fork项目
2. 选择合适的版本进行开发
3. 创建功能分支
4. 提交代码更改
5. 创建Pull Request

## 📝 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 创建Issue
- 发起Discussion
- 提交Pull Request

---

**享受修仙之旅！** ✨