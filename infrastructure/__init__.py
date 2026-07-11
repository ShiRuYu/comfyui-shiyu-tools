"""Infrastructure 层 — 基础设施。

与 ComfyUI 无关的可替换基础设施：
- Storage SPI: 存储抽象
- Event|: 事件总线
- Command Bus: 命令总线
- Config: 配置管理
- Logger: 日志系统

所有基础设施都通过接口/抽象基类定义，可通过 SPI 替换实现。
"""

__all__ = []
