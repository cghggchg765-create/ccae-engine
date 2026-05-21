"""智能翻译服务"""

import json
import time
from database import get_db

class TranslatorService:
    """汉服专业翻译引擎"""
    
    def __init__(self):
        self.db = get_db()
        self.target_accuracy = 0.95
    
    def translate(self, text: str, target_lang: str) -> dict:
        """
        翻译文本
        返回: {translated, matched_terms, confidence, response_time_ms}
        """
        start = time.time()
        matched_terms = []
        translated = text
        
        # 1. 从语料库匹配专业术语
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM corpus WHERE status='active'")
        rows = cursor.fetchall()
        
        for row in rows:
            term = row["term_zh"]
            if term in text:
                translations = json.loads(row["translations"] or "{}")
                cultural_note = row["cultural_note"] or ""
                if target_lang in translations:
                    # 替换术语并附加文化注释
                    text = text.replace(term, translations[target_lang])
                    matched_terms.append({
                        "term": term,
                        "translated": translations[target_lang],
                        "cultural_note": cultural_note
                    })
        
        translated = text
        confidence = min(1.0, len(matched_terms) / max(1, len(text.split())) * 2)
        response_time_ms = int((time.time() - start) * 1000)
        
        # 2. 记录翻译日志
        self.db.execute("""
            INSERT INTO translation_log (source_text, target_lang, translated_text,
                matched_terms, confidence, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (text, target_lang, translated,
              json.dumps(matched_terms, ensure_ascii=False),
              confidence, response_time_ms))
        self.db.commit()
        
        return {
            "source": text,
            "target_lang": target_lang,
            "translated": translated,
            "matched_terms": matched_terms,
            "confidence": round(confidence, 2),
            "response_time_ms": response_time_ms
        }
    
    def get_corpus(self, page=1, per_page=50, category=None, keyword=None):
        """获取语料库列表"""
        cursor = self.db.cursor()
        conditions = ["1=1"]
        params = []
        
        if category:
            conditions.append("category=?")
            params.append(category)
        if keyword:
            conditions.append("term_zh LIKE ?")
            params.append(f"%{keyword}%")
        
        where = " AND ".join(conditions)
        offset = (page - 1) * per_page
        
        cursor.execute(f"""
            SELECT COUNT(*) as total FROM corpus WHERE {where}
        """, params)
        total = cursor.fetchone()["total"]
        
        cursor.execute(f"""
            SELECT * FROM corpus WHERE {where}
            ORDER BY updated_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, offset])
        items = [dict(row) for row in cursor.fetchall()]
        
        return {"total": total, "page": page, "per_page": per_page, "items": items}
    
    def add_term(self, term_zh: str, category: str, translations: dict,
                 definition="", cultural_note="", tags=""):
        """添加术语"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO corpus (term_zh, category, definition, cultural_note, tags, translations)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (term_zh, category, definition, cultural_note, tags, json.dumps(translations, ensure_ascii=False)))
        self.db.commit()
        return {"id": cursor.lastrowid, "message": "术语添加成功"}
    
    def update_term(self, term_id: int, **kwargs):
        """更新术语"""
        allowed = ["term_zh", "category", "definition", "cultural_note", "tags", "status"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "translations" in kwargs:
            updates["translations"] = json.dumps(kwargs["translations"], ensure_ascii=False)
        
        if not updates:
            return {"error": "无有效更新字段"}
        
        sets = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [term_id]
        
        cursor = self.db.cursor()
        cursor.execute(f"UPDATE corpus SET {sets}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)
        self.db.commit()
        return {"message": "术语更新成功"}
    
    def delete_term(self, term_id: int):
        """删除术语"""
        self.db.execute("DELETE FROM corpus WHERE id=?", (term_id,))
        self.db.commit()
        return {"message": "术语已删除"}
    
    def get_stats(self):
        """翻译模块统计数据"""
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM corpus WHERE status='active'")
        corpus_count = cursor.fetchone()["cnt"]
        
        cursor.execute("""
            SELECT COUNT(*) as cnt, AVG(confidence) as avg_conf,
                   AVG(response_time_ms) as avg_time
            FROM translation_log
            WHERE created_at > datetime('now', '-7 days')
        """)
        stats = cursor.fetchone()
        
        return {
            "corpus_count": corpus_count,
            "weekly_translations": stats["cnt"],
            "avg_confidence": round(stats["avg_conf"] or 0, 2),
            "avg_response_ms": round(stats["avg_time"] or 0, 0)
        }
