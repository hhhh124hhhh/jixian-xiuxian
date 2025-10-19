# 数据契约最佳实践指南

## 📋 概述

本文档定义了极简修仙项目中数据契约的设计、实现和维护最佳实践，用于防止类似`exp_threshold` KeyError的技术债务问题。

## 🎯 核心原则

### 1. 数据契约明确性
- **明确定义接口**: 每个数据提供者必须明确说明提供哪些字段
- **类型一致性**: 相同字段在不同层之间必须保持相同的数据类型
- **文档化**: 所有数据接口必须有完整的文档说明

### 2. 向后兼容性
- **字段演进**: 新增字段应该是可选的，不破坏现有功能
- **弃用策略**: 字段弃用必须有明确的迁移路径
- **版本控制**: 重要数据变更需要版本控制

### 3. 测试覆盖
- **契约测试**: 每个数据接口都必须有对应的契约测试
- **集成测试**: 验证完整数据流的端到端测试
- **静态分析**: 使用自动化工具检测潜在问题

## 🏗️ 数据层架构

### 数据提供者 (Data Providers)
```python
class CharacterStats:
    def get_status_summary(self) -> Dict[str, Any]:
        """
        获取角色状态摘要
        Returns:
            Dict[str, Any]: 包含以下字段的字典:
                - name: str - 角色名称
                - hp: int - 当前生命值
                - max_hp: int - 最大生命值
                - mp: int - 当前仙力值
                - max_mp: int - 最大仙力值
                - realm: str - 当前境界
                - exp: int - 当前经验值
                - exp_progress: float - 境界进度百分比 (0-100)
                - talent: int - 资质值 (1-10)
                - pills: int - 丹药数量
                - meditation_streak: int - 连续打坐次数
                - total_actions: int - 总行动次数
                - total_exp: int - 总经验值
                - alive: bool - 是否存活
        """
```

### 数据消费者 (Data Consumers)
```python
class CharacterDisplayInfo:
    """UI显示用的角色信息数据类"""
    def __init__(self,
                 name: str,
                 talent: int,
                 realm: str,
                 exp: int,
                 exp_threshold: int,  # 从rules.py获取
                 hp: int,
                 max_hp: int,
                 mp: int,
                 max_mp: int,
                 pills: int,
                 meditation_streak: int,
                 hp_percentage: float,
                 mp_percentage: float,
                 exp_percentage: float):
        # 字段定义...
```

## 🔧 实现规范

### 1. 字段命名规范
- **一致性**: 使用snake_case命名法
- **语义明确**: 字段名应该清楚地表达其含义
- **避免歧义**: `exp_progress` (百分比) vs `exp_threshold` (阈值)

### 2. 数据类型规范
```python
# 基础类型
name: str           # 字符串
hp: int            # 整数
alive: bool         # 布尔值
exp_progress: float # 浮点数(百分比)

# 复合类型
status: Dict[str, Any]           # 字典
inventory: Dict[str, int]        # 物品字典
actions: List[Action]            # 动作列表
```

### 3. 数据转换规范
```python
def format_character_info(self, character) -> CharacterDisplayInfo:
    """数据转换示例"""
    status = character.get_status_summary()

    # 数据转换和补充
    current_realm = realm_map.get(status["realm"], RealmLevel.QI_REFINING)
    exp_threshold = game_rules.get_realm_threshold(current_realm)

    return CharacterDisplayInfo(
        # 直接映射字段
        name=status["name"],
        hp=status["hp"],
        # 转换字段
        exp_threshold=exp_threshold,  # 从外部数据源获取
        hp_percentage=status["hp"] / status["max_hp"],  # 计算字段
    )
```

## 🧪 测试策略

### 1. 契约测试
```python
def test_character_status_fields_consistency(self):
    """测试角色状态字段的一致性"""
    character = CharacterStats("测试角色")
    status = character.get_status_summary()

    # 验证必需字段存在
    required_fields = ['name', 'hp', 'mp', 'realm', 'exp', ...]
    for field in required_fields:
        assert field in status
        assert status[field] is not None

    # 验证数据类型
    assert isinstance(status['name'], str)
    assert isinstance(status['hp'], int)
    assert isinstance(status['exp_progress'], (int, float))
```

### 2. 集成测试
```python
def test_ui_character_display_info_contract(self):
    """测试UI层数据契约"""
    renderer = GameStateRenderer()
    character = CharacterStats("测试角色")

    char_info = renderer.format_character_info(character)

    # 验证UI数据契约
    assert isinstance(char_info, CharacterDisplayInfo)
    assert hasattr(char_info, 'exp_threshold')  # 关键字段
    assert char_info.exp_threshold > 0
```

### 3. 边界测试
```python
def test_edge_cases(self):
    """测试边界情况"""
    # 死亡角色
    dead_character = CharacterStats("死亡角色")
    dead_character.health.current_hp = 0
    char_info = renderer.format_character_info(dead_character)
    assert char_info.hp == 0
    assert char_info.hp_percentage == 0.0

    # 最大境界
    ascended_character = CharacterStats("飞升角色")
    ascended_character.experience.current_realm = RealmLevel.ASCENSION
    char_info = renderer.format_character_info(ascended_character)
    assert char_info.realm == "飞升"
```

## 🔍 静态分析工具

### 1. 数据契约一致性检查
```bash
# 运行数据契约测试
python3 test_data_contract_consistency.py

# 运行静态字段依赖分析
python3 static_field_dependency_analyzer.py

# 运行完整数据契约测试套件
python3 run_data_contract_tests.py
```

### 2. 检查项目
- **字段完整性**: 验证所有必需字段都存在
- **类型一致性**: 检查字段类型在层间保持一致
- **命名规范**: 验证字段命名符合规范
- **依赖关系**: 分析字段间的依赖关系

## 📝 开发流程

### 1. 新增字段流程
1. **定义接口**: 在数据提供者中定义新字段
2. **更新文档**: 添加字段说明到接口文档
3. **实现转换**: 在数据转换层添加映射逻辑
4. **编写测试**: 添加契约测试覆盖新字段
5. **运行验证**: 执行完整测试套件

### 2. 修改字段流程
1. **影响分析**: 使用静态分析工具评估影响范围
2. **向后兼容**: 确保不破坏现有功能
3. **更新测试**: 修改相关测试用例
4. **渐进部署**: 分阶段发布变更

### 3. 代码审查清单
- [ ] 数据接口是否有完整的文档说明？
- [ ] 所有字段都有类型注解吗？
- [ ] 是否有对应的契约测试？
- [ ] 是否运行了静态分析工具？
- [ ] 是否验证了边界情况？

## 🚨 常见问题和解决方案

### 1. KeyError: 字段不存在
**问题**: 消费方期望的字段在提供方不存在
```python
# ❌ 错误做法
exp_threshold = status["exp_threshold"]  # KeyError

# ✅ 正确做法
if "exp_threshold" in status:
    exp_threshold = status["exp_threshold"]
else:
    exp_threshold = calculate_exp_threshold(status)
```

### 2. 类型不匹配
**问题**: 相同字段在不同层有不同类型
```python
# ❌ 错误做法
return {"exp_progress": "50%"}  # 字符串

# ✅ 正确做法
return {"exp_progress": 50.0}  # 浮点数
```

### 3. 语义混淆
**问题**: 字段名相似但含义不同
```python
# ❌ 容易混淆
exp_progress  # 进度百分比 (0-100)
exp_threshold # 经验阈值 (如100, 200等)

# ✅ 更清晰的命名
exp_progress_percent  # 进度百分比
realm_exp_threshold   # 境界经验阈值
```

## 📊 监控和维护

### 1. 持续集成
```yaml
# CI配置示例
data_contract_tests:
  script:
    - python3 test_data_contract_consistency.py
    - python3 static_field_dependency_analyzer.py
    - python3 run_data_contract_tests.py
  artifacts:
    reports:
      - data_contract_report.txt
      - field_dependency_report.txt
```

### 2. 定期审查
- **月度审查**: 检查数据契约的健康状况
- **版本发布**: 重大版本前的全面审查
- **重构后**: 代码重构后的契约验证

### 3. 质量指标
- **契约覆盖率**: 数据接口的测试覆盖百分比
- **一致性得分**: 跨层数据一致性评分
- **问题趋势**: 数据契约问题的历史趋势

## 🎯 具体实施指南

### 极简修仙项目实施要点

1. **立即修复的问题**
   - ✅ exp_threshold KeyError已修复
   - ✅ UI数据转换逻辑已完善
   - ✅ 契约测试已建立

2. **持续监控项目**
   - status字段的使用情况
   - 新增字段的数据流一致性
   - 模板格式的字段依赖

3. **预防措施**
   - 所有数据接口变更必须运行契约测试
   - 使用静态分析工具检查依赖关系
   - 定期运行完整的数据契约测试套件

## 📚 参考资料

- [数据契约设计模式](https://martinfowler.com/articles/datacontract.html)
- [API设计最佳实践](https://restfulapi.net/)
- [Python类型注解指南](https://docs.python.org/3/library/typing.html)

---

**版本**: 1.0
**最后更新**: 2025-01-18
**维护者**: 极简修仙开发团队