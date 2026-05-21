"""AI大模型适配层

提供统一的多AI提供商接入能力，支持：
- OpenAI (GPT-4o, GPT-4o-mini)
- DeepSeek (deepseek-chat, deepseek-coder)
- 通义千问 (qwen-turbo, qwen-plus, qwen-max)
- 文心一言 (ERNIE系列)
- Claude (claude-3-opus, claude-3-sonnet)

所有适配器遵循统一的接口规范，支持热切换。
"""

from .base import AIAdapter
from .factory import AIFactory

__all__ = ["AIAdapter", "AIFactory"]
