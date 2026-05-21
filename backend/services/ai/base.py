"""AI大模型适配器基类

定义所有AI适配器必须实现的统一接口。
遵循"Parse Don't Validate"原则——数据在边界处解析并验证，
内部逻辑可信任数据状态。
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AIAdapterError(Exception):
    """AI适配器基础异常类"""

    pass


class AIConnectionError(AIAdapterError):
    """AI服务连接异常"""

    pass


class AIResponseError(AIAdapterError):
    """AI响应解析异常"""

    pass


class AIAdapter(ABC):
    """AI大模型适配器抽象基类

    所有AI提供商适配器必须继承此类并实现所有抽象方法。
    遵循"Fail Fast"原则——无效状态立即抛出描述性异常。

    Attributes:
        api_key: API密钥
        base_url: API基础URL（可选，用于自定义端点）
        model: 模型名称（可选，使用提供商默认模型）
        timeout: 请求超时时间（秒）
    """

    # 语言映射表：语言代码 → 中文名称
    LANGUAGE_MAP = {
        "en": "英语",
        "ja": "日语",
        "ko": "韩语",
        "es": "西班牙语",
        "fr": "法语",
        "ar": "阿拉伯语",
        "de": "德语",
        "ru": "俄语",
        "pt": "葡萄牙语",
        "it": "意大利语",
    }

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化AI适配器

        Args:
            api_key: API密钥（必须提供）
            base_url: API基础URL（可选）
            model: 模型名称（可选）
            timeout: 请求超时时间（秒），默认30秒

        Raises:
            ValueError: api_key为空时抛出
        """
        # Guard Clause: 提前验证必需参数
        if not api_key or not api_key.strip():
            raise ValueError("API密钥不能为空")

        self.api_key = api_key.strip()
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self._provider_name = self.__class__.__name__.replace("Adapter", "")

    @abstractmethod
    def translate(
        self, text: str, target_lang: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """翻译文本

        将中文文本翻译为目标语言，保持汉服专业术语准确性。

        Args:
            text: 待翻译的中文文本
            target_lang: 目标语言代码（如 'en', 'ja', 'ko'）
            context: 翻译上下文（可选，用于提升翻译质量）

        Returns:
            dict: 翻译结果，包含以下字段：
                - translated: 翻译后的文本
                - confidence: 置信度（0.0-1.0）
                - model: 使用的模型名称
                - notes: 文化注释列表（可选）
                - source: 原文（可选）

        Raises:
            AIConnectionError: API连接失败
            AIResponseError: 响应解析失败
        """
        pass

    @abstractmethod
    def audit_text(self, text: str, target_country: str) -> Dict[str, Any]:
        """文本合规审核

        分析文本在目标国家/地区的文化合规性。

        Args:
            text: 待审核的文本
            target_country: 目标国家/地区（如 '德国', '日本'）

        Returns:
            dict: 审核结果，包含以下字段：
                - risk_level: 风险等级（"合规"/"低风险"/"高风险"）
                - reasons: 风险原因列表
                - suggestions: 修改建议列表
                - confidence: 审核置信度（0.0-1.0）
                - model: 使用的模型名称

        Raises:
            AIConnectionError: API连接失败
            AIResponseError: 响应解析失败
        """
        pass

    @abstractmethod
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """图像分析（多模态能力）

        分析汉服图像的色彩、纹样、朝代等特征。
        注意：仅支持多模态模型（如GPT-4o、Claude-3等）。

        Args:
            image_path: 图像文件路径

        Returns:
            dict: 分析结果，包含以下字段：
                - colors: 主色调列表
                - patterns: 纹样列表
                - dynasty: 推断的朝代
                - format: 推断的形制
                - confidence: 分析置信度（0.0-1.0）
                - model: 使用的模型名称
                - error: 错误信息（如不支持多模态）

        Raises:
            AIConnectionError: API连接失败
            AIResponseError: 响应解析失败
            FileNotFoundError: 图像文件不存在
        """
        pass

    @abstractmethod
    def generate_copy(
        self, topic: str, style: str, region: str, keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成营销文案

        根据主题、风格和目标区域生成汉服营销文案。

        Args:
            topic: 文案主题（如 "春季新品马面裙"）
            style: 文案风格（如 "典雅", "活泼", "国潮"）
            region: 目标区域（如 "北美", "日韩"）
            keywords: 关键词列表（可选，用于SEO优化）

        Returns:
            dict: 生成结果，包含以下字段：
                - content: 主文案
                - variations: 文案变体列表
                - model: 使用的模型名称
                - word_count: 字数统计

        Raises:
            AIConnectionError: API连接失败
            AIResponseError: 响应解析失败
        """
        pass

    def is_available(self) -> bool:
        """检查AI服务是否可用

        执行简单的健康检查，验证API密钥和连接状态。

        Returns:
            bool: True表示可用，False表示不可用
        """
        # Guard Clause: API密钥必须存在
        if not self.api_key:
            return False

        try:
            # 子类可重写此方法实现更详细的健康检查
            return True
        except Exception as e:
            logger.warning(f"[{self._provider_name}] 健康检查失败: {e}")
            return False

    def get_provider_name(self) -> str:
        """获取提供商名称

        Returns:
            str: AI提供商名称
        """
        return self._provider_name

    def get_model_name(self) -> str:
        """获取当前使用的模型名称

        Returns:
            str: 模型名称，如未指定则返回默认模型
        """
        return self.model or self._get_default_model()

    @abstractmethod
    def _get_default_model(self) -> str:
        """获取提供商默认模型名称

        Returns:
            str: 默认模型名称
        """
        pass

    def _validate_language(self, lang_code: str) -> str:
        """验证并规范化语言代码

        Args:
            lang_code: 语言代码（如 'en', 'EN', '英语'）

        Returns:
            str: 规范化的语言代码

        Raises:
            ValueError: 不支持的语言代码
        """
        # Guard Clause: 空值检查
        if not lang_code:
            raise ValueError("语言代码不能为空")

        # 规范化为小写
        normalized = lang_code.lower().strip()

        # 检查是否支持
        if normalized not in self.LANGUAGE_MAP:
            # 尝试反向查找（中文名 → 代码）
            for code, name in self.LANGUAGE_MAP.items():
                if name == lang_code:
                    return code

            raise ValueError(
                f"不支持的语言: {lang_code}。"
                f"支持的语言: {list(self.LANGUAGE_MAP.keys())}"
            )

        return normalized

    def _build_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """构建错误响应（统一格式）

        Args:
            error_type: 错误类型
            message: 错误消息

        Returns:
            dict: 标准化的错误响应
        """
        return {
            "error": True,
            "error_type": error_type,
            "message": message,
            "provider": self._provider_name,
            "model": self.get_model_name(),
        }
