"""统一AI大模型服务

支持多种AI提供商，通过注入项目数据实现智能处理。
""" 

import os
import json
import logging
from typing import Optional, Dict, Any, List

from database import get_db
from services.ai.factory import AIFactory
from services.ai.base import AIAdapter

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self._adapter = None
        self._enabled = None

    @property
    def adapter(self):
        if self._adapter is None and self._enabled is None:
            self._adapter = AIFactory.get_instance()
            self._enabled = self._adapter is not None
        return self._adapter

    @property
    def enabled(self):
        if self._enabled is None:
            _ = self.adapter
        return self._enabled or False

    def _get_db(self):
        return get_db()

    def _load_project_data(self, data_type, limit=100):
        db = self._get_db()
        cursor = db.cursor()
        try:
            if data_type == "corpus":
                cursor.execute("SELECT term_zh, category, definition, cultural_note, translations FROM corpus WHERE status='active' LIMIT ?", (limit,))
                return json.dumps([dict(row) for row in cursor.fetchall()], ensure_ascii=False, indent=2)
            elif data_type == "rules":
                cursor.execute("SELECT country, category, keywords, risk_level, reason, suggestion FROM compliance_rules WHERE status='active' LIMIT ?", (limit,))
                return json.dumps([dict(row) for row in cursor.fetchall()], ensure_ascii=False, indent=2)
            elif data_type == "knowledge":
                cursor.execute("SELECT category, title_zh, content_zh FROM knowledge_base LIMIT ?", (limit,))
                return json.dumps([dict(row) for row in cursor.fetchall()], ensure_ascii=False, indent=2)
            elif data_type == "aesthetic":
                cursor.execute("SELECT region, category, preference, weight FROM aesthetic_preferences LIMIT ?", (limit,))
                return json.dumps([dict(row) for row in cursor.fetchall()], ensure_ascii=False, indent=2)
            return "" 
        except Exception as e:
            logger.error(f"[AI] 加载项目数据失败: {e}")
            return "" 

    def translate(self, text, target_lang, context=None):
        if not self.enabled or not self.adapter:
            return None
        if not text or not text.strip():
            return None
        try:
            result = self.adapter.translate(text, target_lang, context)
            if result and "translated" in result:
                result["data_source"] = "ai_with_corpus" 
            return result
        except Exception as e:
            logger.error(f"[AI] 翻译失败: {e}")
            return None

    def audit_text(self, text, target_country):
        if not self.enabled or not self.adapter:
            return None
        if not text or not text.strip() or not target_country:
            return None
        try:
            result = self.adapter.audit_text(text, target_country)
            if result and "risk_level" in result:
                result["data_source"] = "ai_with_rules" 
            return result
        except Exception as e:
            logger.error(f"[AI] 审核失败: {e}")
            return None

    def analyze_image(self, image_path, image_description=None):
        if not self.enabled or not self.adapter:
            return None
        try:
            result = self.adapter.analyze_image(image_path)
            if result and not result.get("error"):
                result["data_source"] = "ai_vision" 
                return result
        except Exception as e:
            logger.error(f"[AI] 图像分析失败: {e}")
        return None

    def generate_copy(self, topic, region, style="优雅"):
        if not self.enabled or not self.adapter:
            return None
        if not topic:
            return None
        try:
            result = self.adapter.generate_copy(topic, style, region)
            if result and "content" in result:
                result["data_source"] = "ai_with_knowledge" 
            return result
        except Exception as e:
            logger.error(f"[AI] 文案生成失败: {e}")
            return None

    def recommend(self, user_profile, visual_tags, region):
        if not self.enabled or not self.adapter:
            return None
        return None

    def chat(self, question, context=None):
        if not self.enabled or not self.adapter:
            return None
        if not question or not question.strip():
            return None
        return None

    def get_status(self):
        if not self.enabled:
            return {"enabled": False, "message": "AI服务未配置"} 
        return {
            "enabled": True,
            "provider": self.adapter.get_provider_name() if self.adapter else "unknown",
            "model": self.adapter.get_model_name() if self.adapter else "unknown",
        }


_ai_service = None

def get_ai_service():
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service