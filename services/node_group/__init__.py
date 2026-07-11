"""Node Group Center 模块。

四层架构：
- GroupRepository（数据访问）
- GroupService（业务逻辑）
- GroupController（API/命令入口）
- GroupPanel（UI，在 ui/node_group 中）
"""

from .group_service import GroupService
from .group_controller import GroupController

__all__ = ["GroupService", "GroupController"]
