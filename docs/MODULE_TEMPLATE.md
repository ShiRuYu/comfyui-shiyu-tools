# ComfyUI Shiyu Tools — 模块模板

本文档为新增业务模块提供标准模板。新增模块时，请直接复制此模板。

---

## 模块目录结构

```
ModuleName/                      # 模块名，snake_case
├── __init__.py                  # 模块导出
├── module_name_repository.py    # 数据访问层
├── module_name_service.py       # 业务逻辑层
├── module_name_controller.py    # API/命令入口
└── module_name_panel.py         # UI 面板
```

---

## 模块注册

在 `kernel/registry.py` 中注册新模块：

```python
self.register(ModuleNameModule(kernel))
```

---

## 模板文件

### 1. Repository (`xxx_repository.py`)

```python
"""ModuleName Repository — 数据访问层。"""

from dataclasses import dataclass, field
from typing import Optional

from infrastructure.repository.base_repository import BaseRepository
from infrastructure.storage.storage import Storage


@dataclass
class ModuleNameEntity:
    """模块实体数据模型。"""
    id: str
    name: str
    # 在此添加业务字段
    created_at: str = ""
    updated_at: str = ""


class ModuleNameRepository(BaseRepository[ModuleNameEntity]):
    """ModuleName 数据访问。

    职责：
    - CRUD 操作
    - 数据持久化
    - 索引维护

    禁止：
    - ❌ 包含业务逻辑
    - ❌ 直接操作文件系统（通过 Storage）
    - ❌ 发出事件
    """

    def __init__(self, storage: Storage) -> None:
        super().__init__(storage, "module_name", ModuleNameEntity)
```

### 2. Service (`xxx_service.py`)

```python
"""ModuleName Service — 业务逻辑层。"""

from typing import Optional

from infrastructure.event.event_bus import EventBus
from infrastructure.command.command_bus import CommandBus

from .module_name_repository import ModuleNameEntity, ModuleNameRepository


class ModuleNameService:
    """ModuleName 业务逻辑。

    职责：
    - 业务规则校验
    - 跨 Repository 协调
    - 事件发布
    - 导入/导出

    禁止：
    - ❌ 直接操作存储
    - ❌ 直接操作 UI
    - ❌ 直接操作 ComfyUI Graph
    """

    def __init__(
        self,
        repository: ModuleNameRepository,
        event_bus: EventBus,
        command_bus: CommandBus,
    ) -> None:
        self._repo = repository
        self._event_bus = event_bus
        self._command_bus = command_bus

    def create(self, name: str, **kwargs) -> ModuleNameEntity:
        """创建新实体。"""
        # 1. 校验
        if not name or not name.strip():
            raise ValueError("name must not be empty")

        # 2. 创建实体
        import uuid
        import datetime
        entity = ModuleNameEntity(
            id=str(uuid.uuid4()),
            name=name.strip(),
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat(),
            **kwargs,
        )

        # 3. 保存
        self._repo.create(entity)

        # 4. 发布事件
        self._event_bus.emit("module_name.created", {
            "id": entity.id,
            "data": entity,
        })

        return entity

    def get_by_id(self, entity_id: str) -> Optional[ModuleNameEntity]:
        """根据 ID 获取实体。"""
        return self._repo.get_by_id(entity_id)

    def get_all(self) -> list[ModuleNameEntity]:
        """获取所有实体。"""
        return self._repo.get_all()

    def update(self, entity_id: str, **kwargs) -> Optional[ModuleNameEntity]:
        """更新实体。"""
        entity = self._repo.get_by_id(entity_id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        import datetime
        entity.updated_at = datetime.datetime.now().isoformat()
        self._repo.update(entity_id, entity)

        self._event_bus.emit("module_name.updated", {
            "id": entity_id,
            "changes": kwargs,
        })

        return entity

    def delete(self, entity_id: str) -> bool:
        """删除实体。"""
        result = self._repo.delete(entity_id)
        if result:
            self._event_bus.emit("module_name.deleted", {"id": entity_id})
        return result

    def search(self, query: str) -> list[ModuleNameEntity]:
        """搜索实体。"""
        all_items = self._repo.get_all()
        query = query.lower()
        return [
            item for item in all_items
            if query in item.name.lower()
        ]
```

### 3. Controller (`xxx_controller.py`)

```python
"""ModuleName Controller — API/命令入口。"""

from infrastructure.command.command_bus import CommandBus
from infrastructure.command.commands import Command

from .module_name_service import ModuleNameService


class CreateModuleNameCommand(Command):
    """创建 ModuleName 的命令。"""
    def __init__(self, name: str, **kwargs):
        super().__init__()
        self.name = name
        self.kwargs = kwargs


class ModuleNameController:
    """ModuleName 控制器。

    职责：
    - 接收命令（UI、快捷键、右键菜单等来源）
    - 调用 Service 执行
    - 返回结果

    禁止：
    - ❌ 包含业务逻辑
    - ❌ 直接访问 Repository
    """

    def __init__(
        self,
        service: ModuleNameService,
        command_bus: CommandBus,
    ) -> None:
        self._service = service
        self._command_bus = command_bus

        # 注册命令处理器
        self._command_bus.register(
            CreateModuleNameCommand,
            self._handle_create,
        )

    def _handle_create(self, command: CreateModuleNameCommand) -> dict:
        """处理创建命令。"""
        entity = self._service.create(command.name, **command.kwargs)
        return {"success": True, "data": entity}
```

### 4. UI Panel (`xxx_panel.py`)

```python
"""ModuleName UI Panel。"""

from ui.framework.sidebar import SidebarPanel


class ModuleNamePanel(SidebarPanel):
    """ModuleName 侧边栏面板。

    职责：
    - 渲染列表/树形视图
    - 响应用户操作（点击、右键、拖拽）
    - 通过 Controller 发送命令

    禁止：
    - ❌ 直接调用 Service
    - ❌ 直接操作 Repository
    - ❌ 包含业务逻辑
    """

    def __init__(self, controller: ModuleNameController) -> None:
        super().__init__()
        self._controller = controller
        self._title = "Module Name"
        self._icon = "module_icon"
```

### 5. 模块入口 (`__init__.py`)

```python
"""ModuleName 模块。"""

from kernel.module import PluginModule

from .module_name_repository import ModuleNameRepository
from .module_name_service import ModuleNameService
from .module_name_controller import ModuleNameController
from .module_name_panel import ModuleNamePanel


class ModuleNameModule(PluginModule):
    """ModuleName 模块 — 模块描述。"""

    def __init__(self, kernel) -> None:
        super().__init__("module_name", kernel)

    def initialize(self) -> None:
        """初始化：创建各层实例。"""
        storage = self._kernel.get_storage()
        event_bus = self._kernel.get_event_bus()
        command_bus = self._kernel.get_command_bus()
        ui_service = self._kernel.get_ui_service()

        # 1. Repository
        repository = ModuleNameRepository(storage)

        # 2. Service
        service = ModuleNameService(repository, event_bus, command_bus)

        # 3. Controller
        controller = ModuleNameController(service, command_bus)

        # 4. UI
        panel = ModuleNamePanel(controller)
        ui_service.register_panel("module_name", panel)

        # 保存引用
        self._repository = repository
        self._service = service
        self._controller = controller
        self._panel = panel

    def load(self) -> None:
        """加载：从存储加载数据。"""
        self._repository.load()

    def start(self) -> None:
        """启动：注册 UI。"""
        self._panel.show()

    def stop(self) -> None:
        """停止：隐藏 UI。"""
        self._panel.hide()

    def destroy(self) -> None:
        """销毁：清理资源。"""
        self._repository.save()
```

---

## 快速开始

复制整个目录并替换 `ModuleName` / `module_name` 即可开始新模块：

```bash
# 从 services/ 目录执行
cp -r template_module module_name
cd module_name
# 全局替换 ModuleName → YourModuleName
# 全局替换 module_name → your_module_name
```
