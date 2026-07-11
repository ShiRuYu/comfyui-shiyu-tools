# ComfyUI Shiyu Tools — 架构文档

## 项目定位

**comfyui-shiyu-tools** 是一个运行于 ComfyUI 内部的**企业级插件平台**。

- ❌ 不是"生成图片的 Node"
- ❌ 不是普通 ComfyUI 自定义节点
- ✅ **是类似 VSCode Plugin、JetBrains Plugin、Chrome Extension 的插件框架**
- ✅ 目标是**增强 Workflow 开发效率**

---

## 一、整体架构

```
                         ComfyUI Runtime
                                │
        ┌───────────────────────┴────────────────────────┐
        │                                                │
     Python Backend                               Frontend (JS)
        │                                                │
        └──────────────────── Plugin Kernel ─────────────┘
                               │
        ┌───────────────┬──────────────┬─────────────────┐
        │               │              │
    Prompt Center   NodeGroup      Workflow Center
        │               │              │
        └───────────────┼──────────────┘
                        │
                Storage Service
                        │
                Event / Command Bus
                        │
               ComfyUI Extension API
```

这里的真正核心不是 Prompt，而是 **Plugin Kernel**。以后所有模块都挂在这里。

---

## 二、分层架构

```
comfyui-shiyu-tools/
│
├── __init__.py                 # ComfyUI 插件入口 (NODE_CLASS_MAPPINGS)
├── shiyu_tools.py              # 插件主启动器 (PluginKernel 初始化)
│
├── kernel/                     # ★ 插件内核（唯一直接依赖 ComfyUI 的层之一）
│   ├── kernel.py               # PluginKernel — 全局单例，所有模块的注册中枢
│   ├── lifecycle.py            # 生命周期管理 (Install→Init→Load→Ready→Dispose)
│   ├── module.py               # PluginModule 抽象基类 — 所有业务模块必须继承
│   ├── registry.py             # 模块注册表
│   └── permission.py           # 权限控制
│
├── core/                       # ★ Core 层（唯一允许调用 ComfyUI API 的层）
│   ├── comfyui_bridge.py       # ComfyUI Bridge — 封装 app.graph, app.canvas, queue, nodes, extensions
│   ├── graph_adapter.py        # Graph 操作适配器
│   └── extension_adapter.py    # Extension 注册适配器
│
├── infrastructure/             # 基础设施层（与 ComfyUI 无关）
│   ├── storage/                # Storage SPI
│   │   ├── storage.py          # Storage 抽象基类
│   │   ├── json_storage.py     # JSON 文件存储实现
│   │   └── memory_storage.py   # 内存存储实现（用于测试）
│   ├── repository/             # Repository 模式
│   │   ├── base_repository.py  # BaseRepository 基类
│   │   ├── prompt_repository.py
│   │   └── group_repository.py
│   ├── event/                  # 事件系统
│   │   ├── event_bus.py        # EventBus — 发布/订阅
│   │   └── events.py           # 内置事件定义
│   ├── command/                # 命令系统
│   │   ├── command_bus.py      # CommandBus — 命令调度
│   │   └── commands.py         # 内置命令定义
│   ├── config/                 # 配置管理
│   │   └── config.py
│   └── logger/                 # 日志系统
│       └── logger.py
│
├── services/                   # 业务层
│   ├── prompt/                 # Prompt Center
│   │   ├── prompt_service.py   # 业务逻辑
│   │   └── prompt_controller.py # API/命令入口
│   └── node_group/             # Node Group Center
│       ├── group_service.py    # 业务逻辑
│       └── group_controller.py # API/命令入口
│
├── ui/                         # UI 层
│   ├── framework/              # UI 框架
│   │   ├── sidebar.py
│   │   ├── toolbar.py
│   │   ├── inspector.py
│   │   ├── dialog.py
│   │   └── toast.py
│   ├── prompt/                 # Prompt UI
│   │   └── prompt_panel.py
│   └── node_group/             # Node Group UI
│       └── group_panel.py
│
├── web/                        # 前端 JS 扩展
│   └── ...
│
└── tests/                      # 测试
    ├── unit/
    └── integration/
```

---

## 三、核心原则

### 原则 1：Core 是唯一依赖 ComfyUI 的层

```
✅ 正确
Prompt → Core → ComfyUI Graph

❌ 错误
Prompt → ComfyUI Graph  (直接操作)
```

整个插件中，只有 `core/` 目录下的代码允许调用 ComfyUI 的 API：

- `app.graph`
- `app.canvas`
- `api`
- `queue`
- `nodes`
- `extensions`

当 ComfyUI 升级导致 API 变化时，**只需要修改 `core/` 层**。

### 原则 2：Storage SPI

```
✅ 正确
PromptRepository → Storage (接口) → JsonStorage / SqliteStorage / CloudStorage

❌ 错误
PromptRepository → open() / save()  (直接操作文件)
```

业务模块**不知道数据保存在哪里**，只通过 `Storage` 接口访问。

### 原则 3：Repository 模式

所有业务模块都不直接操作 JSON 文件，统一通过 Repository 访问数据：

- `PromptRepository`
- `GroupRepository`
- `WorkflowRepository`（后续）
- `LoraRepository`（后续）

更换存储实现（JSON → SQLite → Cloud）时，**无需修改业务代码**。

### 原则 4：Service 层

```
✅ 正确
Controller → Service → Repository

❌ 错误
Controller → Repository (绕过业务逻辑)
Controller → JSON (直接读文件)
```

所有业务逻辑（标签管理、搜索、收藏、导入导出、版本控制等）**必须放在 Service 层**。

### 原则 5：事件驱动

```
✅ 正确
Prompt Saved 事件 → 广播
    ├── Sidebar 监听 → 刷新列表
    ├── History 监听 → 记录变更
    ├── Search 监听 → 更新索引
    └── Statistics 监听 → 更新统计

❌ 错误
PromptService.save() → Sidebar.refresh()  (硬耦合)
```

### 原则 6：Command 模式

所有修改操作统一走 Command：

```
✅ 正确
CreatePromptCommand → CommandBus → PromptService.create()

❌ 错误
UI 直接调用 PromptRepository.save()
```

天然支持：
- **Undo / Redo**
- **操作日志**
- **权限校验**
- **批量操作**

### 原则 7：生命周期管理

```
Install → Initialize → Load → Ready → Dispose
```

所有模块统一实现 `PluginModule` 接口：

```python
class PluginModule:
    def initialize(self, kernel): ...
    def load(self): ...
    def start(self): ...
    def stop(self): ...
    def destroy(self): ...
```

### 原则 8：UI Service

所有 UI 窗口统一管理，模块**不能自己创建窗口**。

```
✅ 正确
PromptModule → UiService.sidebar.add("prompt", PromptPanel)

❌ 错误
PromptPanel.__init__ → 自己创建 QWidget
```

---

## 四、业务模块模板

每个业务模块遵循统一结构：

```
ModuleName/
├── ModuleNameRepository.py    # 数据访问
├── ModuleNameService.py       # 业务逻辑
├── ModuleNameController.py    # API/命令入口
└── ModuleNamePanel.py         # UI
```

详见 [MODULE_TEMPLATE.md](./MODULE_TEMPLATE.md)。

---

## 五、事件总线设计

### 内置事件

| 事件 | 说明 | 数据 |
|------|------|------|
| `prompt.created` | Prompt 创建 | `{prompt_id, prompt_data}` |
| `prompt.updated` | Prompt 更新 | `{prompt_id, changes}` |
| `prompt.deleted` | Prompt 删除 | `{prompt_id}` |
| `prompt.saved` | Prompt 保存 | `{prompt_id}` |
| `group.created` | Group 创建 | `{group_id, group_data}` |
| `group.updated` | Group 更新 | `{group_id, changes}` |
| `group.deleted` | Group 删除 | `{group_id}` |
| `group.node.added` | 节点加入分组 | `{group_id, node_ids}` |
| `group.node.removed` | 节点移出分组 | `{group_id, node_ids}` |
| `plugin.initialized` | 插件初始化完成 | `{version}` |
| `plugin.before_shutdown` | 插件即将关闭 | `{}` |

---

## 六、命令总线设计

### 内置命令

| 命令 | 说明 |
|------|------|
| `CreatePromptCommand` | 创建 Prompt |
| `UpdatePromptCommand` | 更新 Prompt |
| `DeletePromptCommand` | 删除 Prompt |
| `CreateGroupCommand` | 创建 Group |
| `UpdateGroupCommand` | 更新 Group |
| `DeleteGroupCommand` | 删除 Group |
| `MoveGroupCommand` | 移动 Group 位置 |
| `CollapseGroupCommand` | 折叠/展开 Group |
| `AddNodeToGroupCommand` | 添加节点到 Group |
| `RemoveNodeFromGroupCommand` | 从 Group 移除节点 |
| `LocateGroupCommand` | 定位 Group |

---

## 七、Node Group 数据模型

```python
@dataclass
class NodeGroup:
    id: str                    # 唯一标识
    name: str                  # 组名
    color: str                 # 颜色
    parent: Optional[str]      # 父组 ID
    children: List[str]        # 子组 ID 列表
    node_ids: List[str]        # 包含的节点 ID 列表
    collapsed: bool            # 是否折叠
    enabled: bool              # 是否启用
    locked: bool               # 是否锁定
    visible: bool              # 是否可见
    metadata: GroupMetadata    # 元数据
    tags: List[str]            # 标签

@dataclass
class GroupMetadata:
    owner: str                 # 创建者
    description: str           # 描述
    create_time: str           # 创建时间
    update_time: str           # 更新时间
    icon: str                  # 图标
    color: str                 # 颜色
    shortcut: str              # 快捷键
    favorite: bool             # 是否收藏
```

---

## 八、Prompt 数据模型

Prompt 不是字符串，而是 **Document**：

```python
@dataclass
class PromptDocument:
    id: str
    metadata: PromptMetadata
    positive: str              # Positive Prompt
    negative: str              # Negative Prompt
    tags: List[str]            # 标签
    variables: Dict[str, str]  # 变量（模板用）
    history: List[PromptVersion]  # 历史版本
    created_at: str
    updated_at: str

@dataclass
class PromptMetadata:
    name: str
    description: str
    category: str
    favorite: bool
    shortcut: str
    author: str
    icon: str
```

---

## 九、扩展路径

后续可采用这套架构扩展：

| 模块 | 说明 |
|------|------|
| Workflow Manager | Workflow 版本管理、模板、分享 |
| LoRA Manager | LoRA 资源管理、标签、搜索 |
| Model Manager | Checkpoint/VAE 管理 |
| Execution Engine | 批量执行、队列管理 |
| Template Center | Prompt 模板库 |
| Statistics Dashboard | 使用统计、性能分析 |
| History Manager | 操作历史、回滚 |

每个模块都遵循：

```
ModuleName/
├── ModuleNameRepository.py
├── ModuleNameService.py
├── ModuleNameController.py
└── ModuleNamePanel.py
```
