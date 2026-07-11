# 🧩 ComfyUI Shiyu Tools

**ComfyUI Enterprise Plugin Framework**

> 一个运行于 ComfyUI 内部的**企业级插件平台**。
>
> ❌ 不是"生成图片的 Node"
>
> ❌ 不是普通 ComfyUI 自定义节点
>
> ✅ **是类似 VSCode Plugin / JetBrains Plugin / Chrome Extension 的插件框架**
>
> ✅ 目标是**增强 Workflow 开发效率**

---

## 核心架构

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

### 8 大设计原则

| # | 原则 | 说明 |
|---|------|------|
| 1 | **Core 层隔离** | 只有 `core/` 允许调用 ComfyUI API（`app.graph`, `app.canvas`, `queue` 等），ComfyUI 升级只改 Core |
| 2 | **Storage SPI** | 不直接 `open()/save()`，通过 `Storage` 接口，未来可切换 JSON → SQLite → Cloud |
| 3 | **Repository 模式** | 业务层通过 `PromptRepository`、`GroupRepository` 访问数据，不知道底层是什么存储 |
| 4 | **Service 层** | 所有业务逻辑放在 Service，Controller 和 UI 不直接操作数据 |
| 5 | **事件驱动** | 修改统一广播事件，Sidebar/History/Search 各自监听，模块间零硬耦合 |
| 6 | **Command 模式** | 所有修改操作走 Command，天然支持 Undo/Redo |
| 7 | **生命周期管理** | `Install → Initialize → Load → Ready → Dispose`，所有模块统一 `PluginModule` 接口 |
| 8 | **UI Service** | 所有 UI 窗口统一管理，模块不能自己创建窗口 |

---

## 项目结构

```
comfyui-shiyu-tools/
│
├── __init__.py                    # ComfyUI 插件入口 (NODE_CLASS_MAPPINGS)
├── shiyu_tools.py                 # 插件主启动器 (bootstrap)
│
├── kernel/                        # 插件内核
│   ├── kernel.py                  # PluginKernel — 全局单例
│   ├── lifecycle.py               # 生命周期管理
│   ├── module.py                  # PluginModule 抽象基类
│   ├── registry.py                # 模块注册表
│   └── permission.py             # 权限控制
│
├── core/                          # ★ 唯一允许调用 ComfyUI API 的层
│   ├── comfyui_bridge.py          # ComfyUI Bridge
│   ├── graph_adapter.py           # Graph 适配器
│   └── extension_adapter.py       # Extension 适配器
│
├── infrastructure/                # 基础设施（与 ComfyUI 无关）
│   ├── storage/                   # Storage SPI (JsonStorage, MemoryStorage)
│   ├── repository/                # Repository (Base, Prompt, Group)
│   ├── event/                     # EventBus (发布/订阅)
│   ├── command/                   # CommandBus (命令模式)
│   ├── config/                    # 配置管理
│   └── logger/                    # 日志系统
│
├── services/                      # 业务层 (四层架构)
│   ├── prompt/                    # Prompt Center
│   │   ├── prompt_service.py      #   业务逻辑
│   │   └── prompt_controller.py   #   API/命令入口
│   └── node_group/                # Node Group Center
│       ├── group_service.py       #   业务逻辑
│       └── group_controller.py    #   API/命令入口
│
├── ui/                            # UI 层
│   ├── framework/                 # UI Framework (Sidebar, Toolbar, Inspector, Dialog, Toast)
│   ├── prompt/                    # Prompt Panel
│   └── node_group/                # Group Panel
│
├── web/                           # 前端 JS 扩展
├── docs/                          # 文档
│   ├── ARCHITECTURE.md            # 完整架构文档
│   ├── DEVELOPMENT.md             # 开发规范
│   └── MODULE_TEMPLATE.md         # 模块模板
└── tests/                         # 测试 (52 个单元测试)
    ├── unit/
    │   ├── kernel/
    │   ├── infrastructure/
    │   └── services/
    └── integration/
```

---

## 当前内置模块

### 📝 Prompt Center

Prompt 不是字符串，而是 **Document**（包含元数据、正反向 Prompt、标签、变量、版本历史）。

| 功能 | 状态 |
|------|------|
| CRUD | ✅ |
| 标签管理 | ✅ |
| 搜索（名称/内容/标签） | ✅ |
| 收藏 | ✅ |
| 导入/导出 | ✅ |
| 版本历史 | ✅ |
| 历史版本恢复 | ✅ |

### 📂 Node Group Center

Group 不是 UI 上的矩形，而是 **Business Object**（树结构、折叠、锁定、节点映射）。

| 功能 | 状态 |
|------|------|
| CRUD | ✅ |
| 树结构管理 | ✅ |
| 折叠/展开 | ✅ |
| 锁定/解锁 | ✅ |
| 节点添加/移除 | ✅ |
| 节点定位 | ✅ |
| 统计信息 | ✅ |

---

## 如何新增一个模块

遵循统一模板：

```
ModuleName/
├── ModuleNameRepository.py    # 数据访问
├── ModuleNameService.py       # 业务逻辑
├── ModuleNameController.py    # API/命令入口
└── ModuleNamePanel.py         # UI
```

详见 [docs/MODULE_TEMPLATE.md](./docs/MODULE_TEMPLATE.md)。

1. 复制模板目录
2. 全局替换 `ModuleName` → `YourModule`
3. 在 `shiyu_tools.py` 中注册模块
4. 编写测试

---

## 未来扩展路径

| 模块 | 说明 |
|------|------|
| Workflow Manager | Workflow 版本管理、模板、分享 |
| LoRA Manager | LoRA 资源管理、标签、搜索 |
| Model Manager | Checkpoint/VAE 管理 |
| Execution Engine | 批量执行、队列管理 |
| Template Center | Prompt 模板库 |
| Statistics Dashboard | 使用统计、性能分析 |
| History Manager | 操作历史、回滚 |

每个模块都遵循 `Repository → Service → Controller → UI` 四层架构。

---

## 开发

```bash
# 安装测试依赖
pip install -e ".[test]"

# 运行测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=. --cov-report=term
```

---

## 许可证

MIT © ShiRuYu
