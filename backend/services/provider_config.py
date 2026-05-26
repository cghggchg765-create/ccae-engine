"""AI供应商配置管理模块

实现多供应商、多端点、4层模型映射的统一管理。
参考 CC Switch 设计理念，支持灵活的 AI 配置管理。

配置层次结构：
- Provider (供应商): OpenAI, DeepSeek, 通义千问等
- Endpoint (端点): 每个供应商可以有多个API端点
- ModelMapping (模型映射): 每个端点支持4层模型配置
  - primary: 主要模型，平衡性能与成本
  - light: 轻量模型，快速响应
  - balanced: 均衡模型，性价比
  - strongest: 最强模型，最高质量
"""

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """模型层级枚举

    定义4层模型映射策略：
    - PRIMARY: 主要模型，用于大多数场景
    - LIGHT: 轻量模型，用于简单任务或高频调用
    - BALANCED: 均衡模型，性价比最优
    - STRONGEST: 最强模型，用于复杂任务或高精度需求
    """
    PRIMARY = "primary"
    LIGHT = "light"
    BALANCED = "balanced"
    STRONGEST = "strongest"


class ProviderType(Enum):
    """供应商类型枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"  # 通义千问
    CUSTOM = "custom"


class EndpointStatus(Enum):
    """端点状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class ModelMapping:
    """模型映射配置

    定义端点支持的4层模型配置。
    每层可以指定不同的模型名称。

    Attributes:
        primary: 主要模型，用于大多数场景
        light: 轻量模型，快速响应
        balanced: 均衡模型，性价比
        strongest: 最强模型，最高质量
    """
    primary: str = ""
    light: str = ""
    balanced: str = ""
    strongest: str = ""

    def get_model(self, tier: ModelTier) -> str:
        """获取指定层级的模型名称

        Args:
            tier: 模型层级

        Returns:
            str: 模型名称，若未配置则回退到primary
        """
        model = getattr(self, tier.value, "")
        if not model and tier != ModelTier.PRIMARY:
            # 回退到primary
            model = self.primary
        return model

    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ModelMapping":
        """从字典创建实例"""
        return cls(
            primary=data.get("primary", ""),
            light=data.get("light", ""),
            balanced=data.get("balanced", ""),
            strongest=data.get("strongest", ""),
        )


@dataclass
class Endpoint:
    """API端点配置

    定义一个具体的API端点，包含连接信息和模型映射。

    Attributes:
        id: 端点唯一标识符
        name: 端点显示名称
        base_url: API基础URL
        api_key: API密钥（加密存储）
        model_mapping: 模型映射配置
        is_default: 是否为默认端点
        status: 端点状态
    """
    id: str
    name: str
    base_url: str
    api_key: str = ""
    model_mapping: ModelMapping = field(default_factory=ModelMapping)
    is_default: bool = False
    status: str = EndpointStatus.ACTIVE.value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（API密钥脱敏）"""
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self._mask_api_key(),
            "model_mapping": self.model_mapping.to_dict(),
            "is_default": self.is_default,
            "status": self.status,
        }

    def to_dict_full(self) -> Dict[str, Any]:
        """转换为字典（包含完整API密钥，用于保存）"""
        return {
            "id": self.id,
            "name": self.name,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "model_mapping": self.model_mapping.to_dict(),
            "is_default": self.is_default,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Endpoint":
        """从字典创建实例"""
        model_mapping = ModelMapping.from_dict(data.get("model_mapping", {}))
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            base_url=data.get("base_url", ""),
            api_key=data.get("api_key", ""),
            model_mapping=model_mapping,
            is_default=data.get("is_default", False),
            status=data.get("status", EndpointStatus.ACTIVE.value),
        )

    def _mask_api_key(self) -> str:
        """脱敏显示API密钥"""
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "****"
        return f"{self.api_key[:4]}****{self.api_key[-4:]}"


@dataclass
class ProviderConfig:
    """供应商配置

    定义一个AI供应商的完整配置。

    Attributes:
        id: 供应商唯一标识符
        name: 供应商显示名称
        provider_type: 供应商类型
        endpoints: 端点配置列表
        is_active: 是否激活使用
    """
    id: str
    name: str
    provider_type: str
    endpoints: List[Endpoint] = field(default_factory=list)
    is_active: bool = False

    def get_default_endpoint(self) -> Optional[Endpoint]:
        """获取默认端点

        Returns:
            Endpoint: 默认端点，若无则返回第一个可用端点
        """
        # 先找标记为默认的端点
        for ep in self.endpoints:
            if ep.is_default and ep.status == EndpointStatus.ACTIVE.value:
                return ep
        # 找第一个可用端点
        for ep in self.endpoints:
            if ep.status == EndpointStatus.ACTIVE.value:
                return ep
        return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（脱敏）"""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "endpoints": [ep.to_dict() for ep in self.endpoints],
            "is_active": self.is_active,
        }

    def to_dict_full(self) -> Dict[str, Any]:
        """转换为字典（完整数据，用于保存）"""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type,
            "endpoints": [ep.to_dict_full() for ep in self.endpoints],
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """从字典创建实例"""
        endpoints = [Endpoint.from_dict(ep) for ep in data.get("endpoints", [])]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            provider_type=data.get("provider_type", ProviderType.CUSTOM.value),
            endpoints=endpoints,
            is_active=data.get("is_active", False),
        )


# ============================================================================
# 预设供应商配置
# ============================================================================

PRESET_PROVIDERS: List[Dict[str, Any]] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "provider_type": ProviderType.OPENAI.value,
        "endpoints": [
            {
                "id": "openai-default",
                "name": "OpenAI 官方",
                "base_url": "https://api.openai.com/v1",
                "api_key": "",  # 用户配置
                "model_mapping": {
                    "primary": "gpt-4o-mini",
                    "light": "gpt-4o-mini",
                    "balanced": "gpt-4o",
                    "strongest": "gpt-4o",
                },
                "is_default": True,
                "status": EndpointStatus.ACTIVE.value,
            }
        ],
        "is_active": False,
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "provider_type": ProviderType.DEEPSEEK.value,
        "endpoints": [
            {
                "id": "deepseek-default",
                "name": "DeepSeek 官方",
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "",
                "model_mapping": {
                    "primary": "deepseek-chat",
                    "light": "deepseek-chat",
                    "balanced": "deepseek-chat",
                    "strongest": "deepseek-reasoner",
                },
                "is_default": True,
                "status": EndpointStatus.ACTIVE.value,
            }
        ],
        "is_active": False,
    },
    {
        "id": "qwen",
        "name": "通义千问",
        "provider_type": ProviderType.QWEN.value,
        "endpoints": [
            {
                "id": "qwen-default",
                "name": "阿里云 DashScope",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
                "model_mapping": {
                    "primary": "qwen-turbo",
                    "light": "qwen-turbo",
                    "balanced": "qwen-plus",
                    "strongest": "qwen-max",
                },
                "is_default": True,
                "status": EndpointStatus.ACTIVE.value,
            }
        ],
        "is_active": False,
    },
]


# ============================================================================
# 供应商管理器
# ============================================================================

class ProviderManager:
    """供应商管理器

    管理所有AI供应商配置，提供增删改查和激活操作。

    功能：
    - 列出所有供应商
    - 获取/添加/更新/删除供应商
    - 激活供应商
    - 获取当前激活的供应商
    - 测试连接

    配置存储路径: data/.ccae/config.json
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化管理器

        Args:
            config_path: 配置文件路径，默认为 data/.ccae/config.json
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 默认路径
            base_dir = Path(__file__).parent.parent.parent
            self.config_path = base_dir / "data" / ".ccae" / "config.json"

        self._providers: Dict[str, ProviderConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    providers_data = data.get("providers", [])
                    for p_data in providers_data:
                        provider = ProviderConfig.from_dict(p_data)
                        self._providers[provider.id] = provider
                logger.info(f"[ProviderManager] 已加载 {len(self._providers)} 个供应商配置")
            except Exception as e:
                logger.error(f"[ProviderManager] 加载配置失败: {e}")
                self._init_default_config()
        else:
            self._init_default_config()

    def _init_default_config(self) -> None:
        """初始化默认配置"""
        for preset in PRESET_PROVIDERS:
            provider = ProviderConfig.from_dict(preset)
            self._providers[provider.id] = provider
        self._save_config()
        logger.info("[ProviderManager] 已初始化默认供应商配置")

    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "providers": [p.to_dict_full() for p in self._providers.values()],
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("[ProviderManager] 配置已保存")
        except Exception as e:
            logger.error(f"[ProviderManager] 保存配置失败: {e}")
            raise

    def list_providers(self, include_sensitive: bool = False) -> List[Dict[str, Any]]:
        """列出所有供应商

        Args:
            include_sensitive: 是否包含敏感信息（如完整API密钥）

        Returns:
            List[Dict]: 供应商列表
        """
        if include_sensitive:
            return [p.to_dict_full() for p in self._providers.values()]
        return [p.to_dict() for p in self._providers.values()]

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """获取单个供应商

        Args:
            provider_id: 供应商ID

        Returns:
            Dict: 供应商配置，不存在则返回None
        """
        provider = self._providers.get(provider_id)
        if provider:
            return provider.to_dict()
        return None

    def get_provider_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """获取供应商配置对象（内部使用）

        Args:
            provider_id: 供应商ID

        Returns:
            ProviderConfig: 供应商配置对象
        """
        return self._providers.get(provider_id)

    def add_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加供应商

        支持两种模式：
        1. 从预设创建：只传 provider_type，自动使用预设配置
        2. 自定义创建：传完整数据（id, name, provider_type, endpoints）

        Args:
            provider_data: 供应商数据

        Returns:
            Dict: 添加后的供应商配置

        Raises:
            ValueError: 数据验证失败
        """
        provider_type = provider_data.get("provider_type")

        # 模式1：从预设创建
        if provider_type and not provider_data.get("id"):
            preset = None
            for p in PRESET_PROVIDERS:
                if p["provider_type"] == provider_type:
                    preset = p.copy()
                    break

            if not preset:
                raise ValueError(f"不支持的供应商类型: {provider_type}")

            # 检查是否已存在
            if preset["id"] in self._providers:
                raise ValueError(f"供应商 '{preset['id']}' 已存在")

            provider = ProviderConfig.from_dict(preset)
            self._providers[provider.id] = provider
            self._save_config()

            logger.info(f"[ProviderManager] 已从预设添加供应商: {provider.name}")
            return provider.to_dict()

        # 模式2：自定义创建
        if not provider_data.get("id"):
            raise ValueError("供应商ID不能为空")
        if not provider_data.get("name"):
            raise ValueError("供应商名称不能为空")
        if provider_data["id"] in self._providers:
            raise ValueError(f"供应商ID '{provider_data['id']}' 已存在")

        provider = ProviderConfig.from_dict(provider_data)
        self._providers[provider.id] = provider
        self._save_config()

        logger.info(f"[ProviderManager] 已添加供应商: {provider.name}")
        return provider.to_dict()

    def update_provider(self, provider_id: str, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新供应商

        Args:
            provider_id: 供应商ID
            provider_data: 更新数据

        Returns:
            Dict: 更新后的供应商配置

        Raises:
            ValueError: 供应商不存在
        """
        if provider_id not in self._providers:
            raise ValueError(f"供应商 '{provider_id}' 不存在")

        # 保留ID，更新其他字段
        provider_data["id"] = provider_id
        provider = ProviderConfig.from_dict(provider_data)
        self._providers[provider_id] = provider
        self._save_config()

        logger.info(f"[ProviderManager] 已更新供应商: {provider.name}")
        return provider.to_dict()

    def delete_provider(self, provider_id: str) -> bool:
        """删除供应商

        Args:
            provider_id: 供应商ID

        Returns:
            bool: 是否删除成功

        Raises:
            ValueError: 供应商不存在或是预设供应商
        """
        if provider_id not in self._providers:
            raise ValueError(f"供应商 '{provider_id}' 不存在")

        # 检查是否是预设供应商
        preset_ids = [p["id"] for p in PRESET_PROVIDERS]
        if provider_id in preset_ids:
            raise ValueError(f"预设供应商 '{provider_id}' 不能删除，只能禁用")

        del self._providers[provider_id]
        self._save_config()

        logger.info(f"[ProviderManager] 已删除供应商: {provider_id}")
        return True

    def activate_provider(self, provider_id: str) -> Dict[str, Any]:
        """激活供应商

        同时会取消其他供应商的激活状态。

        Args:
            provider_id: 供应商ID

        Returns:
            Dict: 激活后的供应商配置

        Raises:
            ValueError: 供应商不存在或无可用端点
        """
        if provider_id not in self._providers:
            raise ValueError(f"供应商 '{provider_id}' 不存在")

        provider = self._providers[provider_id]

        # 检查是否有可用端点
        if not provider.get_default_endpoint():
            raise ValueError(f"供应商 '{provider_id}' 无可用端点")

        # 取消其他供应商的激活状态
        for pid, p in self._providers.items():
            p.is_active = (pid == provider_id)

        self._save_config()

        logger.info(f"[ProviderManager] 已激活供应商: {provider.name}")
        return provider.to_dict()

    def get_active_provider(self) -> Optional[Dict[str, Any]]:
        """获取当前激活的供应商

        Returns:
            Dict: 激活的供应商配置，若无则返回None
        """
        for provider in self._providers.values():
            if provider.is_active:
                return provider.to_dict_full()  # 返回完整数据用于API调用
        return None

    def get_active_provider_config(self) -> Optional[ProviderConfig]:
        """获取当前激活的供应商配置对象（内部使用）

        Returns:
            ProviderConfig: 激活的供应商配置对象
        """
        for provider in self._providers.values():
            if provider.is_active:
                return provider
        return None

    def test_connection(self, provider_id: str, endpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """测试供应商连接

        Args:
            provider_id: 供应商ID
            endpoint_id: 端点ID（可选，默认使用默认端点）

        Returns:
            Dict: 测试结果
                - success: 是否成功
                - message: 结果消息
                - latency: 响应延迟（毫秒）
        """
        import time
        import requests

        provider = self._providers.get(provider_id)
        if not provider:
            return {"success": False, "message": f"供应商 '{provider_id}' 不存在"}

        # 获取端点
        endpoint = None
        if endpoint_id:
            for ep in provider.endpoints:
                if ep.id == endpoint_id:
                    endpoint = ep
                    break
        else:
            endpoint = provider.get_default_endpoint()

        if not endpoint:
            return {"success": False, "message": "无可用端点"}

        if not endpoint.api_key:
            return {"success": False, "message": "API密钥未配置"}

        # 测试连接
        try:
            start_time = time.time()

            # 发送一个简单的测试请求
            headers = {
                "Authorization": f"Bearer {endpoint.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": endpoint.model_mapping.primary or "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            }

            response = requests.post(
                f"{endpoint.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=10,
            )

            latency = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                # 更新端点状态
                endpoint.status = EndpointStatus.ACTIVE.value
                self._save_config()
                return {
                    "success": True,
                    "message": "连接成功",
                    "latency": latency,
                }
            else:
                error_msg = f"API返回错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', '')}"
                except:
                    pass

                endpoint.status = EndpointStatus.ERROR.value
                self._save_config()
                return {
                    "success": False,
                    "message": error_msg,
                    "latency": latency,
                }

        except requests.exceptions.Timeout:
            endpoint.status = EndpointStatus.ERROR.value
            self._save_config()
            return {"success": False, "message": "连接超时"}
        except requests.exceptions.ConnectionError as e:
            endpoint.status = EndpointStatus.ERROR.value
            self._save_config()
            return {"success": False, "message": f"连接失败: {str(e)[:100]}"}
        except Exception as e:
            endpoint.status = EndpointStatus.ERROR.value
            self._save_config()
            return {"success": False, "message": f"测试失败: {str(e)[:100]}"}

    def get_model_for_tier(self, tier: ModelTier = ModelTier.PRIMARY) -> Optional[str]:
        """获取当前激活供应商的指定层级模型

        Args:
            tier: 模型层级

        Returns:
            str: 模型名称，若无激活供应商则返回None
        """
        provider = self.get_active_provider_config()
        if not provider:
            return None

        endpoint = provider.get_default_endpoint()
        if not endpoint:
            return None

        return endpoint.model_mapping.get_model(tier)


# ============================================================================
# 单例管理
# ============================================================================

_provider_manager: Optional[ProviderManager] = None


def get_provider_manager(config_path: Optional[str] = None) -> ProviderManager:
    """获取供应商管理器单例

    Args:
        config_path: 配置文件路径（仅首次调用时有效）

    Returns:
        ProviderManager: 供应商管理器实例
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager(config_path)
    return _provider_manager


def reset_provider_manager() -> None:
    """重置供应商管理器单例（用于测试）"""
    global _provider_manager
    _provider_manager = None


__all__ = [
    "ModelTier",
    "ProviderType",
    "EndpointStatus",
    "ModelMapping",
    "Endpoint",
    "ProviderConfig",
    "PRESET_PROVIDERS",
    "ProviderManager",
    "get_provider_manager",
    "reset_provider_manager",
]
