"""OpenAI适配器

支持GPT-4o、GPT-4o-mini等模型的适配器实现。
支持文本翻译、合规审核、图像分析、文案生成等功能。
"""

import json
import base64
import logging
from typing import Optional, Dict, Any, List

import requests

from .base import AIAdapter, AIConnectionError, AIResponseError

logger = logging.getLogger(__name__)


class OpenAIAdapter(AIAdapter):
    """OpenAI GPT系列模型适配器

    支持的模型：
    - gpt-4o: 最新多模态模型，支持图像分析
    - gpt-4o-mini: 轻量级模型，性价比高
    - gpt-4-turbo: 支持视觉的GPT-4版本
    - gpt-3.5-turbo: 快速文本模型

    Attributes:
        DEFAULT_BASE_URL: OpenAI API默认端点
        DEFAULT_MODEL: 默认使用的模型
        VISION_MODELS: 支持图像分析的模型列表
    """

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"
    VISION_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-vision-preview"]

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
    ):
        """初始化OpenAI适配器

        Args:
            api_key: OpenAI API密钥
            base_url: API端点（可选，用于代理或自定义端点）
            model: 模型名称（可选，默认使用gpt-4o-mini）
            timeout: 请求超时时间（秒）
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            model=model or self.DEFAULT_MODEL,
            timeout=timeout,
        )

    def _get_default_model(self) -> str:
        """获取默认模型名称"""
        return self.DEFAULT_MODEL

    def _call_api(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """调用OpenAI Chat Completions API

        Args:
            messages: 消息列表
            temperature: 温度参数（0-2），控制随机性
            max_tokens: 最大生成token数
            response_format: 响应格式（如 {"type": "json_object"}）

        Returns:
            dict: API响应

        Raises:
            AIConnectionError: 连接失败
            AIResponseError: 响应解析失败
        """
        # Guard Clause: 验证消息列表
        if not messages:
            raise ValueError("消息列表不能为空")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # 如果要求JSON格式响应
        if response_format:
            data["response_format"] = response_format

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout,
            )

            # Fail Fast: 检查HTTP状态码
            if response.status_code != 200:
                error_msg = f"OpenAI API错误: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail.get('error', {}).get('message', response.text)}"
                except:
                    error_msg += f" - {response.text}"

                raise AIConnectionError(error_msg)

            return response.json()

        except requests.exceptions.Timeout:
            raise AIConnectionError(f"OpenAI API请求超时（{self.timeout}秒）")
        except requests.exceptions.ConnectionError as e:
            raise AIConnectionError(f"OpenAI API连接失败: {e}")
        except json.JSONDecodeError as e:
            raise AIResponseError(f"OpenAI API响应解析失败: {e}")

    def _call_vision_api(
        self, text: str, image_path: str, temperature: float = 0.5
    ) -> Dict[str, Any]:
        """调用OpenAI Vision API（图像+文本）

        Args:
            text: 文本提示
            image_path: 图像文件路径
            temperature: 温度参数

        Returns:
            dict: API响应

        Raises:
            ValueError: 模型不支持图像分析
            FileNotFoundError: 图像文件不存在
            AIConnectionError: 连接失败
            AIResponseError: 响应解析失败
        """
        # Guard Clause: 检查模型是否支持视觉
        if not self._supports_vision():
            raise ValueError(
                f"模型 {self.model} 不支持图像分析。支持的模型: {self.VISION_MODELS}"
            )

        # Guard Clause: 检查文件是否存在
        import os

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        # 读取并编码图像
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        # 获取图像格式
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/jpeg")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                    },
                ],
            }
        ]

        return self._call_api(messages, temperature=temperature)

    def _supports_vision(self) -> bool:
        """检查当前模型是否支持图像分析"""
        return any(
            vm in self.model.lower() for vm in ["gpt-4o", "gpt-4-turbo", "gpt-4-vision"]
        )

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """安全解析JSON响应

        Args:
            content: API返回的文本内容

        Returns:
            dict: 解析后的字典

        Raises:
            AIResponseError: JSON解析失败
        """
        # Guard Clause: 空内容检查
        if not content:
            raise AIResponseError("API返回空内容")

        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON块（处理markdown代码块）
        import re

        json_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        matches = re.findall(json_pattern, content)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        # 尝试查找JSON对象
        json_obj_pattern = r"\{[\s\S]*\}"
        matches = re.findall(json_obj_pattern, content)

        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass

        raise AIResponseError(f"无法解析JSON响应: {content[:200]}...")

    def translate(
        self, text: str, target_lang: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用GPT进行翻译

        Args:
            text: 待翻译的中文文本
            target_lang: 目标语言代码
            context: 翻译上下文

        Returns:
            dict: 翻译结果
        """
        # Guard Clause: 验证输入
        if not text or not text.strip():
            raise ValueError("待翻译文本不能为空")

        # 规范化语言代码
        lang_code = self._validate_language(target_lang)
        lang_name = self.LANGUAGE_MAP.get(lang_code, target_lang)

        system_prompt = f"""你是一个专业的汉服文化翻译专家，精通中文和{lang_name}。
请将用户提供的中文文本翻译成{lang_name}。

翻译要求：
1. 保持汉服专业术语的准确性（如"马面裙"、"襦裙"等）
2. 保留必要的文化背景注释（用括号标注）
3. 使用目标语言的自然表达方式
4. 返回严格的JSON格式

返回格式：
{{
    "translated": "翻译结果",
    "notes": ["文化注释1", "文化注释2"],
    "confidence": 0.95
}}"""

        user_content = f"请翻译以下中文文本：\n\n{text}"
        if context:
            user_content = f"上下文：{context}\n\n{user_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        try:
            result = self._call_api(
                messages, temperature=0.3, response_format={"type": "json_object"}
            )

            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_json_response(content)

            return {
                "translated": parsed.get("translated", text),
                "confidence": parsed.get("confidence", 0.90),
                "model": self.model,
                "provider": "OpenAI",
                "notes": parsed.get("notes", []),
                "source": text,
            }

        except (AIConnectionError, AIResponseError) as e:
            logger.error(f"[OpenAI] 翻译失败: {e}")
            raise
        except Exception as e:
            logger.error(f"[OpenAI] 翻译未知错误: {e}")
            raise AIResponseError(f"翻译失败: {e}")

    def audit_text(self, text: str, target_country: str) -> Dict[str, Any]:
        """使用GPT进行合规审核

        Args:
            text: 待审核的文本
            target_country: 目标国家/地区

        Returns:
            dict: 审核结果
        """
        # Guard Clause: 验证输入
        if not text or not text.strip():
            raise ValueError("待审核文本不能为空")
        if not target_country:
            raise ValueError("目标国家不能为空")

        system_prompt = f"""你是一个跨文化合规审核专家，熟悉全球各国的文化禁忌和敏感话题。
请分析以下文本在"{target_country}"市场是否存在文化风险。

审核维度：
1. 文化冒犯风险（如不当引用、刻板印象）
2. 宗教禁忌风险（如敏感符号、不当表述）
3. 政治敏感风险（如敏感话题、争议内容）
4. 文化挪用风险（如不当使用他国文化元素）

返回严格的JSON格式：
{{
    "risk_level": "合规" 或 "低风险" 或 "高风险",
    "reasons": ["风险原因1", "风险原因2"],
    "suggestions": ["修改建议1", "修改建议2"],
    "confidence": 0.95,
    "details": {{
        "cultural_offense": false,
        "religious_taboo": false,
        "political_sensitive": false,
        "cultural_appropriation": false
    }}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请审核以下文本：\n\n{text}"},
        ]

        try:
            result = self._call_api(
                messages, temperature=0.2, response_format={"type": "json_object"}
            )

            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_json_response(content)

            return {
                "risk_level": parsed.get("risk_level", "低风险"),
                "reasons": parsed.get("reasons", []),
                "suggestions": parsed.get("suggestions", []),
                "confidence": parsed.get("confidence", 0.85),
                "model": self.model,
                "provider": "OpenAI",
                "details": parsed.get("details", {}),
            }

        except (AIConnectionError, AIResponseError) as e:
            logger.error(f"[OpenAI] 审核失败: {e}")
            raise
        except Exception as e:
            logger.error(f"[OpenAI] 审核未知错误: {e}")
            raise AIResponseError(f"审核失败: {e}")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """使用GPT-4V进行图像分析

        Args:
            image_path: 图像文件路径

        Returns:
            dict: 分析结果
        """
        # Guard Clause: 检查模型是否支持视觉
        if not self._supports_vision():
            return {
                "error": True,
                "message": f"模型 {self.model} 不支持图像分析。请使用支持视觉的模型: {self.VISION_MODELS}",
                "provider": "OpenAI",
                "model": self.model,
            }

        # Guard Clause: 检查文件是否存在
        import os

        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        prompt = """你是一个汉服文化专家，请分析这张汉服图片。

分析维度：
1. 主色调（识别2-4种主要颜色，使用中国传统色名）
2. 纹样特征（如云纹、龙凤纹、缠枝莲等）
3. 朝代推断（商周/秦汉/魏晋/唐/宋/明/清/现代改良）
4. 形制判断（如马面裙、襦裙、深衣等）

返回严格的JSON格式：
{
    "colors": ["朱红", "金色", "藏青"],
    "patterns": ["云纹", "缠枝莲"],
    "dynasty": "明",
    "format": "马面裙",
    "confidence": 0.85,
    "description": "简要描述"
}"""

        try:
            result = self._call_vision_api(prompt, image_path, temperature=0.3)

            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_json_response(content)

            return {
                "colors": parsed.get("colors", []),
                "patterns": parsed.get("patterns", []),
                "dynasty": parsed.get("dynasty", "明"),
                "format": parsed.get("format", "马面裙"),
                "confidence": parsed.get("confidence", 0.80),
                "model": self.model,
                "provider": "OpenAI",
                "description": parsed.get("description", ""),
            }

        except (AIConnectionError, AIResponseError) as e:
            logger.error(f"[OpenAI] 图像分析失败: {e}")
            raise
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[OpenAI] 图像分析未知错误: {e}")
            raise AIResponseError(f"图像分析失败: {e}")

    def generate_copy(
        self, topic: str, style: str, region: str, keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成营销文案

        Args:
            topic: 文案主题
            style: 文案风格
            region: 目标区域
            keywords: 关键词列表

        Returns:
            dict: 生成结果
        """
        # Guard Clause: 验证输入
        if not topic:
            raise ValueError("文案主题不能为空")
        if not style:
            raise ValueError("文案风格不能为空")
        if not region:
            raise ValueError("目标区域不能为空")

        keywords_str = "、".join(keywords) if keywords else "无特殊要求"

        system_prompt = f"""你是一个汉服营销文案专家，熟悉{region}市场的文化偏好和消费习惯。
请为以下主题生成营销文案。

主题：{topic}
风格：{style}
目标市场：{region}
关键词要求：{keywords_str}

文案要求：
1. 符合目标市场的文化审美
2. 突出汉服的文化价值
3. 语言自然流畅，有感染力
4. 适当融入关键词（如有）

返回严格的JSON格式：
{{
    "content": "主文案内容",
    "variations": ["变体1", "变体2", "变体3"],
    "word_count": 150,
    "highlights": ["亮点1", "亮点2"]
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请生成{style}风格的文案"},
        ]

        try:
            result = self._call_api(
                messages, temperature=0.8, response_format={"type": "json_object"}
            )

            content = result["choices"][0]["message"]["content"]
            parsed = self._parse_json_response(content)

            return {
                "content": parsed.get("content", ""),
                "variations": parsed.get("variations", []),
                "word_count": parsed.get("word_count", 0),
                "highlights": parsed.get("highlights", []),
                "model": self.model,
                "provider": "OpenAI",
            }

        except (AIConnectionError, AIResponseError) as e:
            logger.error(f"[OpenAI] 文案生成失败: {e}")
            raise
        except Exception as e:
            logger.error(f"[OpenAI] 文案生成未知错误: {e}")
            raise AIResponseError(f"文案生成失败: {e}")

    def is_available(self) -> bool:
        """检查OpenAI服务是否可用"""
        if not super().is_available():
            return False

        try:
            # 发送一个简单的测试请求
            result = self._call_api([{"role": "user", "content": "Hi"}], max_tokens=5)
            return True
        except Exception as e:
            logger.warning(f"[OpenAI] 服务不可用: {e}")
            return False
