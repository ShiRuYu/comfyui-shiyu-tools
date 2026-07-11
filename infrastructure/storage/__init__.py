"""Storage SPI — 存储抽象层。

提供 Storage 抽象接口及其实现：
- Storage: 抽象基类
- JsonStorage: JSON 文件实现
- MemoryStorage: 内存实现（用于测试）
"""

from .storage import Storage, StorageError, EntityNotFoundError
from .json_storage import JsonStorage
from .memory_storage import MemoryStorage

__all__ = [
    "Storage",
    "StorageError",
    "EntityNotFoundError",
    "JsonStorage",
    "MemoryStorage",
]
