# ComfyUI Shiyu Tools — 开发规范

## 一、代码规范

### 1.1 Python 规范

- **Python 版本**: 3.10+
- **代码风格**: 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **类型注解**: 所有函数和方法必须有完整类型注解
- **Docstring**: 使用 Google Style Docstring

```python
def create_prompt(
    name: str,
    positive: str,
    negative: str = "",
    tags: list[str] | None = None,
) -> PromptDocument:
    """创建一个新的 Prompt。

    Args:
        name: Prompt 名称
        positive: 正向 Prompt
        negative: 负向 Prompt（可选）
        tags: 标签列表（可选）

    Returns:
        创建的 PromptDocument 实例

    Raises:
        ValidationError: 当 name 为空或 positive 为空时
        DuplicateError: 当同名 Prompt 已存在时
    """
    ...
```

### 1.2 导入规范

```python
# 标准库
import json
import os
from dataclasses import dataclass, field
from typing import Optional
from abc import ABC, abstractmethod

# 第三方库（不直接依赖 ComfyUI）

# 项目内部
from kernel.module import PluginModule
from infrastructure.storage import Storage
```

### 1.3 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `PromptService`, `EventBus` |
| 函数/方法 | snake_case | `create_prompt()`, `get_by_id()` |
| 变量 | snake_case | `prompt_list`, `group_tree` |
| 常量 | UPPER_SNAKE_CASE | `MAX_GROUP_DEPTH`, `DEFAULT_COLOR` |
| 私有 | 前缀 `_` | `_validate_prompt()` |
| 模块名 | snake_case | `prompt_service.py` |

---

## 二、分层依赖规则

### 2.1 依赖方向（严格单向）

```
ui/       →  services/   →  infrastructure/   →  core/
                            (可以一步跨，但不能反向)
↑                              ↓
└──────────────────────────────┘
     通过事件/命令解耦
```

### 2.2 各层允许的导入

| 层 | 可以导入 | 禁止导入 |
|----|----------|----------|
| `kernel/` | ComfyUI API, `core/` | 业务模块 |
| `core/` | ComfyUI API | 业务模块, `infrastructure/` |
| `infrastructure/` | 标准库, 第三方库 | ComfyUI API, `core/`, 业务模块 |
| `services/` | `infrastructure/` | ComfyUI API, `core/` |
| `ui/` | `services/`, `infrastructure/` | ComfyUI API, `core/` |

### 2.3 跨模块通信

- **同级模块之间禁止直接调用**（如 Prompt → NodeGroup）
- 必须通过 **EventBus** 或 **CommandBus** 通信

---

## 三、命名规范

### 3.1 文件命名

| 内容 | 文件名 |
|------|--------|
| Repository | `xxx_repository.py` |
| Service | `xxx_service.py` |
| Controller | `xxx_controller.py` |
| Panel/UI | `xxx_panel.py` |

### 3.2 类命名

| 内容 | 类名 |
|------|------|
| Repository | `XxxRepository` |
| Service | `XxxService` |
| Controller | `XxxController` |
| Panel | `XxxPanel` |
| 命令 | `XxxCommand` |
| 事件 | `XxxEvent` |

### 3.3 事件命名

```
{模块}.{动作}
例如：
- prompt.created
- prompt.updated
- group.deleted
- group.node.added
```

---

## 四、Repository 规范

### 4.1 Repository 方法命名

| 方法 | 说明 |
|------|------|
| `get_by_id(id)` | 根据 ID 获取 |
| `get_all()` | 获取所有 |
| `find(**filters)` | 条件查询 |
| `save(entity)` | 保存（创建或更新） |
| `create(entity)` | 创建新实体 |
| `update(id, data)` | 更新实体 |
| `delete(id)` | 删除实体 |
| `count()` | 计数 |
| `exists(id)` | 判断是否存在 |

### 4.2 Repository 禁止做的事

- ❌ 直接操作文件系统
- ❌ 包含业务逻辑（如标签解析、搜索算法）
- ❌ 发出事件
- ❌ 创建 UI 元素

---

## 五、Service 规范

### 5.1 Service 方法命名

| 方法 | 说明 |
|------|------|
| `create_xxx()` | 创建资源 |
| `update_xxx()` | 更新资源 |
| `delete_xxx()` | 删除资源 |
| `get_xxx()` | 获取资源 |
| `search_xxx()` | 搜索资源 |
| `import_xxx()` | 导入资源 |
| `export_xxx()` | 导出资源 |
| `validate_xxx()` | 验证资源 |

### 5.2 Service 职责

- ✅ 业务逻辑实现
- ✅ 数据校验
- ✅ 事件发布
- ✅ 跨 Repository 事务协调
- ❌ 直接操作存储
- ❌ 直接操作 Graph
- ❌ 创建 UI

---

## 六、Controller 规范

### 6.1 Controller 职责

- ✅ 接收命令（来自 UI、快捷键、右键菜单）
- ✅ 调用 Service 执行
- ✅ 处理结果返回
- ❌ 包含业务逻辑（转发给 Service）
- ❌ 直接访问 Repository

---

## 七、UI 规范

### 7.1 UI 组件类型

| 组件 | 说明 |
|------|------|
| `Sidebar` | 侧边栏容器 |
| `Toolbar` | 工具栏 |
| `Inspector` | 属性检查器 |
| `Dialog` | 模态对话框 |
| `Popup` | 弹出菜单 |
| `Toast` | 短暂消息提示 |

### 7.2 UI 组件规范

- 所有 UI 必须经过 UI Framework 注册和管理
- 模块不能自己创建独立窗口
- UI 事件通过 `Command` 发送给 `Controller`，**不能直接调用业务方法**

---

## 八、测试规范

### 8.1 测试目录结构

```
tests/
├── unit/
│   ├── kernel/
│   ├── core/
│   ├── infrastructure/
│   │   ├── test_storage.py
│   │   ├── test_event_bus.py
│   │   └── test_command_bus.py
│   └── services/
│       ├── test_prompt_service.py
│       └── test_group_service.py
└── integration/
    └── test_plugin_lifecycle.py
```

### 8.2 测试原则

- 每个 Repository 必须有单元测试（可用 MemoryStorage 替代真实存储）
- 每个 Service 必须有单元测试
- 每个事件/命令必须有测试
- Repository 和 Service **必须可以脱离 ComfyUI 运行测试**

---

## 九、Git 提交规范

### 9.1 提交信息格式

```
<type>(<scope>): <subject>

<body>
```

### 9.2 Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 |
| `docs` | 文档 |
| `refactor` | 重构 |
| `test` | 测试 |
| `chore` | 构建/工具链 |

### 9.3 示例

```
feat(prompt): add prompt CRUD operations

Implement Create/Read/Update/Delete for PromptDocument.
Each operation emits corresponding events through EventBus.
