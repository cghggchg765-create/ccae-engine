"""AI适配器工厂

根据环境变量配置自动选择合适的AI适配器。
遵循"Fail Fast"原则——配置错误立即抛出描述性异常。
"""

import os
import logging
from typing import Optional

from .base import AIAdapter
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class AIFactory:
    """AI适配器工厂类

    支持的提供商：
    - openai: OpenAI GPT系列
    - deepseek: DeepSeek（兼容OpenAI格式）
    - qwen: 通义千问（兼容OpenAI格式）
    - wenxin: 文心一言（需特殊适配）
    - custom: 自定义OpenAI兼容端点

    使用方法：
        adapter = AIFactory.create()
        result = adapter.translate("马面裙", "en")
    """

    # 提供商配置映射
    PROVIDER_CONFIGS = {
        "openai": {
            "default_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o-mini",
            "adapter_class": OpenAIAdapter,
        },
        "deepseek": {
            "default_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
            "adapter_class": OpenAIAdapter,  # DeepSeek兼容OpenAI格式
        },
        "qwen": {
            "default_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-turbo",
            "adapter_class": OpenAIAdapter,  # 通义千问兼容OpenAI格式
        },
        "custom": {
            "default_url": None,  # 必须由用户提供
            "default_model": None,
            "adapter_class": OpenAIAdapter,
        },
    }

    _instance: Optional[AIAdapter] = None

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60,
    ) -> Optional[AIAdapter]:
        """创建AI适配器实例

        Args:
            provider: AI提供商名称（可选，默认从环境变量读取）
            api_key: API密钥（可选，默认从环境变量读取）
            base_url: API端点（可选，默认使用提供商默认值）
            model: 模型名称（可选，默认使用提供商默认值）
            timeout: 请求超时时间（秒）

        Returns:
            AIAdapter: 配置好的适配器实例，若未配置则返回None

        Raises:
            ValueError: 配置无效时抛出
        """
        # Guard Clause: 从环境变量读取配置
        provider = provider or os.environ.get("AI_PROVIDER", "")
        api_key = api_key or os.environ.get("AI_API_KEY", "")
        base_url = base_url or os.environ.get("AI_BASE_URL", "")
        model = model or os.environ.get("AI_MODEL", "")

        # Guard Clause: 未配置时返回None（允许不使用AI）
        if not provider or not api_key:
            logger.info("[AI] 未配置AI服务，将使用规则引擎")
            return None

        # Guard Clause: 验证提供商是否支持
        provider_lower = provider.lower()
        if provider_lower not in cls.PROVIDER_CONFIGS:
            supported = list(cls.PROVIDER_CONFIGS.keys())
            raise ValueError(f"不支持的AI提供商: {provider}。支持的提供商: {supported}")

        config = cls.PROVIDER_CONFIGS[provider_lower]
        adapter_class = config["adapter_class"]

        # 使用提供商默认值（若用户未指定）
        if not base_url:
            base_url = config.get("default_url")
        if not model:
            model = config.get("default_model")

        # Guard Clause: custom提供商必须提供base_url
        if provider_lower == "custom" and not base_url:
            raise ValueError("使用custom提供商时必须配置AI_BASE_URL环境变量")

        # 创建适配器实例
        try:
            adapter = adapter_class(
                api_key=api_key,
                base_url=base_url,
                model=model,
                timeout=timeout,
            )

            logger.info(f"[AI] 已启用 {provider} ({model or adapter.get_model_name()})")

            return adapter

        except Exception as e:
            logger.error(f"[AI] 适配器创建失败: {e}")
            raise ValueError(f"AI适配器创建失败: {e}")

    @classmethod
    def get_instance(cls) -> Optional[AIAdapter]:
        """获取单例适配器实例

        懒加载模式，首次调用时创建实例。

        Returns:
            AIAdapter: 适配器实例，若未配置则返回None
        """
        if cls._instance is None:
            cls._instance = cls.create()

        return cls._instance

    @classmethod
    def reset(cls):
        """重置单例实例

        用于测试或重新加载配置。
        """
        cls._instance = None


__all__ = ["AIFactory"]
