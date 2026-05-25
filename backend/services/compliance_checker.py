"""文化禁忌合规审核服务 — 真实图像内容分析版（AI优先，规则引擎fallback）"""

import json
import time
import hashlib
import os
from PIL import Image
from database import get_db
from services.ai_service import get_ai_service

# ---- 高危色彩模式映射 ----
# 基于色彩分布的组合来推断可能的敏感符号
SENSITIVE_COLOR_PATTERNS = {
    "nazi_flag": {
        "colors": ["大红", "雪白", "玄黑"],
        "red_ratio": (0.3, 0.7),
        "white_ratio": (0.1, 0.3),
        "black_ratio": (0.05, 0.25),
        "risk": "高风险",
        "hint": "红底+白色圆形+黑色图案组合疑似纳粹相关符号",
        "countries": ["德国", "欧洲", "全球"],
    },
    "rising_sun": {
        "colors": ["雪白", "大红"],
        "red_ratio": (0.1, 0.4),
        "white_ratio": (0.4, 0.8),
        "risk": "高风险",
        "hint": "白底+放射状红色条纹疑似旭日旗图案",
        "countries": ["日本", "韩国", "东亚", "全球"],
    },
    "islamic_taboo": {
        "colors": ["金色", "大红", "墨绿"],
        "has_cross_pattern": True,
        "risk": "高风险",
        "hint": "疑似包含十字架等宗教符号",
        "countries": ["沙特阿拉伯", "阿联酋", "中东", "全球"],
    },
    "native_appropriation": {
        "colors": ["茶色", "大红", "金色"],
        "earthy_ratio": (0.3, 0.7),
        "risk": "高风险",
        "hint": "羽饰/图腾柱风格配色疑似文化挪用风险",
        "countries": ["美国", "北美", "全球"],
    },
}


class ComplianceChecker:
    """文化禁忌合规审核引擎（AI优先，规则引擎fallback）"""

    CATEGORIES = ["文化冒犯", "宗教禁忌", "政治敏感", "文化挪用"]
    RISK_LEVELS = ["合规", "低风险", "高风险"]

    # 项目数据目录基准路径
    PROJECT_DATA_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data"
    )

    def __init__(self):
        self.target_accuracy = {"text": 0.98, "image": 0.95}
        self.ai = get_ai_service()

    def _get_db(self):
        """获取数据库连接（线程安全）"""
        return get_db()

    # ========== 文本审核（AI优先，规则引擎fallback） ==========

    def audit_text(self, text: str, target_country: str) -> dict:
        """文本合规审核（AI优先，规则引擎fallback）"""
        start = time.time()
        
        # 1. 尝试AI审核
        if self.ai and self.ai.enabled:
            ai_result = self.ai.audit_text(text, target_country)
            if ai_result:
                response_time_ms = int((time.time() - start) * 1000)
                content_hash = hashlib.md5(text.encode()).hexdigest()
                
                db = self._get_db()
                db.execute(
                    """INSERT INTO audit_log (content_type, content_hash, target_country,
                        risk_level, matched_rules, reason, suggestion, response_time_ms)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "text",
                        content_hash,
                        target_country,
                        ai_result.get("risk_level", "低风险"),
                        json.dumps(ai_result.get("matched_rules", []), ensure_ascii=False),
                        "; ".join(ai_result.get("reasons", [])) if ai_result.get("reasons") else None,
                        "; ".join(ai_result.get("suggestions", [])) if ai_result.get("suggestions") else None,
                        response_time_ms,
                    ),
                )
                db.commit()
                
                return {
                    "content_type": "text",
                    "target_country": target_country,
                    "risk_level": ai_result.get("risk_level", "低风险"),
                    "matched_rules_count": len(ai_result.get("matched_rules", [])),
                    "matched_rules": ai_result.get("matched_rules", []),
                    "reasons": ai_result.get("reasons", []),
                    "suggestions": ai_result.get("suggestions", []),
                    "response_time_ms": response_time_ms,
                    "status": "pass" if ai_result.get("risk_level") == "合规" else "review",
                    "ai_used": True,
                }
        
        # 2. Fallback到规则引擎
        matched_rules = []
        risk_level = "合规"
        reasons = []
        suggestions = []

        db = self._get_db()
        cursor = db.cursor()
        cursor.execute(
            """SELECT * FROM compliance_rules
            WHERE (country=? OR country='全球') AND status='active'""",
            (target_country,),
        )

        rules = cursor.fetchall()

        for rule in rules:
            keywords = json.loads(rule["keywords"] or "[]")
            for kw in keywords:
                if kw and kw in text:
                    matched_rules.append(dict(rule))
                    reasons.append(rule["reason"])
                    suggestions.append(rule["suggestion"])
                    break

        if matched_rules:
            has_high = any(r["risk_level"] == "高风险" for r in matched_rules)
            risk_level = "高风险" if has_high else "低风险"

        response_time_ms = int((time.time() - start) * 1000)

        content_hash = hashlib.md5(text.encode()).hexdigest()
        db.execute(
            """INSERT INTO audit_log (content_type, content_hash, target_country,
                risk_level, matched_rules, reason, suggestion, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "text",
                content_hash,
                target_country,
                risk_level,
                json.dumps(matched_rules, ensure_ascii=False),
                "; ".join(reasons) if reasons else None,
                "; ".join(suggestions) if suggestions else None,
                response_time_ms,
            ),
        )
        db.commit()

        return {
            "content_type": "text",
            "target_country": target_country,
            "risk_level": risk_level,
            "matched_rules_count": len(matched_rules),
            "matched_rules": matched_rules,
            "reasons": reasons,
            "suggestions": suggestions,
            "response_time_ms": response_time_ms,
            "status": "pass" if risk_level == "合规" else "review",
            "ai_used": False,
        }

    # ========== 图片审核（基于真实图像内容分析） ==========

    def audit_image(self, image_path: str, target_country: str) -> dict:
        """图片合规审核 — 基于真实图像色彩分析与规则库模式匹配（AI优先，规则引擎fallback）"""
        start = time.time()
        matched_rules = []
        risk_level = "合规"
        reasons = []

        db = self._get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT * FROM compliance_rules
            WHERE (country=? OR country='全球') AND status='active' AND pattern IS NOT NULL
        """,
            (target_country,),
        )

        rules = cursor.fetchall()

        # 尝试读取真实图片进行分析
        color_profile = None
        try:
            img = self._load_image(image_path)
            color_profile = self._analyze_color_profile(img)
        except (FileNotFoundError, IOError, OSError):
            pass  # 图片不可读时回退到文件名检查

        # ---- 第1层：高危色彩模式检测 ----
        if color_profile:
            for pattern_id, pattern_def in SENSITIVE_COLOR_PATTERNS.items():
                if (
                    target_country not in pattern_def["countries"]
                    and "全球" not in pattern_def["countries"]
                ):
                    continue

                if self._match_color_pattern(color_profile, pattern_def):
                    matched_rules.append(
                        {
                            "id": f"color-{pattern_id}",
                            "country": target_country,
                            "category": "政治敏感"
                            if "nazi" in pattern_id
                            else "文化冒犯",
                            "risk_level": pattern_def["risk"],
                            "reason": pattern_def["hint"],
                            "suggestion": "建议人工复核图片内容，确认是否存在敏感符号",
                            "keywords": "[]",
                        }
                    )
                    reasons.append(pattern_def["hint"])

        # ---- 第2层：规则库纹样/符号模式匹配 ----
        for rule in rules:
            pattern = rule["pattern"] or ""
            keywords = json.loads(rule["keywords"] or "[]")

            matched = False

            # 2a: 色彩分析+纹样关键词匹配
            if color_profile and pattern:
                matched = self._match_pattern_vs_colors(
                    pattern, color_profile["color_names"], target_country
                )

            # 2b: 规则关键词与色彩名匹配
            if color_profile and not matched:
                for kw in keywords:
                    if kw and any(kw in cn for cn in color_profile["color_names"]):
                        matched = True
                        break

            # 2c: 回退 — 文件名中匹配（保留兼容性）
            if not matched:
                path_lower = image_path.lower()
                for kw in keywords:
                    if kw and kw.lower() in path_lower:
                        matched = True
                        break

            if matched:
                matched_rules.append(dict(rule))
                reasons.append(rule["reason"])

        if matched_rules:
            has_high = any(r.get("risk_level") == "高风险" for r in matched_rules)
            risk_level = "高风险" if has_high else "低风险"

        response_time_ms = int((time.time() - start) * 1000)

        content_hash = hashlib.md5(image_path.encode()).hexdigest()
        db.execute(
            """
            INSERT INTO audit_log (content_type, content_hash, target_country,
                risk_level, matched_rules, reason, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "image",
                content_hash,
                target_country,
                risk_level,
                json.dumps(matched_rules, ensure_ascii=False),
                "; ".join(reasons) if reasons else None,
                response_time_ms,
            ),
        )
        db.commit()

        return {
            "content_type": "image",
            "target_country": target_country,
            "risk_level": risk_level,
            "matched_rules_count": len(matched_rules),
            "matched_rules": matched_rules,
            "reasons": reasons,
            "response_time_ms": response_time_ms,
            "status": "pass" if risk_level == "合规" else "review",
            "analysis_method": "color_profile" if color_profile else "filename",
        }

    # ========== 图像分析辅助方法 ==========

    def _validate_path(self, path: str) -> str:
        """
        验证路径安全性，防止路径遍历攻击
        只允许访问项目data目录下的文件
        """
        # 获取绝对路径
        abs_path = os.path.abspath(path)
        
        # 检查是否在允许的目录范围内
        if not abs_path.startswith(self.PROJECT_DATA_DIR):
            raise ValueError(f"路径遍历攻击检测：不允许访问 {abs_path}，仅限项目data目录")
        
        # 检查是否存在路径遍历字符
        if ".." in path or "~" in path:
            raise ValueError(f"路径遍历攻击检测：路径包含非法字符 {path}")
        
        return abs_path

    def _load_image(self, path: str) -> Image.Image:
        """加载图片，支持相对路径和绝对路径，带路径验证"""
        # 先验证路径安全性
        validated_path = self._validate_path(path)
        
        if os.path.isfile(validated_path):
            return Image.open(validated_path).convert("RGB")

        # 如果验证后的路径不存在，尝试其他候选路径（也在data目录下）
        candidates = [
            validated_path,
            os.path.join(self.PROJECT_DATA_DIR, path),
        ]

        for p in candidates:
            # 再次验证每个候选路径
            try:
                validated_p = self._validate_path(p)
                if os.path.isfile(validated_p):
                    return Image.open(validated_p).convert("RGB")
            except ValueError:
                continue  # 跳过非法路径

        raise FileNotFoundError(f"图片文件未找到: {path}")

    def _analyze_color_profile(self, img: Image.Image) -> dict:
        """分析图片色彩轮廓"""
        small = img.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())

        total = len(pixels)

        # 统计各色系占比
        red_count = green_count = blue_count = 0
        white_count = black_count = 0

        for r, g, b in pixels:
            brightness = (r + g + b) / 3
            if brightness > 220:
                white_count += 1
            elif brightness < 35:
                black_count += 1
            else:
                if r > g + 15 and r > b + 15:
                    red_count += 1
                elif g > r + 15 and g > b + 15:
                    green_count += 1
                elif b > r + 15 and b > g + 15:
                    blue_count += 1

        # 提取主色调名
        color_names = self._extract_color_names(img)

        return {
            "red_ratio": red_count / total,
            "green_ratio": green_count / total,
            "blue_ratio": blue_count / total,
            "white_ratio": white_count / total,
            "black_ratio": black_count / total,
            "color_names": color_names,
        }

    def _extract_color_names(self, img: Image.Image) -> list:
        """提取主色调中文名"""
        small = img.resize((40, 40), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())

        bucket = {}
        for r, g, b in pixels:
            key = (r // 48 * 48, g // 48 * 48, b // 48 * 48)
            bucket[key] = bucket.get(key, 0) + 1

        sorted_colors = sorted(bucket.items(), key=lambda x: -x[1])

        color_map = [
            ("大红", 180, 255, 0, 80, 0, 80),
            ("朱红", 160, 220, 40, 100, 40, 100),
            ("金色", 190, 255, 150, 220, 30, 100),
            ("雪白", 230, 255, 230, 255, 230, 255),
            ("玄黑", 0, 50, 0, 50, 0, 50),
            ("藏青", 0, 60, 30, 90, 100, 200),
            ("墨绿", 0, 70, 70, 150, 30, 100),
            ("紫色", 90, 170, 20, 90, 110, 210),
            ("茶色", 110, 180, 70, 140, 40, 100),
            ("明黄", 210, 255, 190, 255, 30, 110),
        ]

        names = []
        seen = set()
        for (r, g, b), _ in sorted_colors[:5]:
            best = None
            best_d = float("inf")
            for name, rn_min, rn_max, gn_min, gn_max, bn_min, bn_max in color_map:
                cr = (rn_min + rn_max) / 2
                cg = (gn_min + gn_max) / 2
                cb = (bn_min + bn_max) / 2
                d = ((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2) ** 0.5
                if d < best_d:
                    best_d = d
                    best = name
            if best and best not in seen:
                names.append(best)
                seen.add(best)

        return names[:4]

    def _match_color_pattern(self, profile: dict, pattern_def: dict) -> bool:
        """检查色彩轮廓是否匹配高危模式"""
        if "colors" in pattern_def:
            required_colors = set(pattern_def["colors"])
            detected_colors = set(profile.get("color_names", []))
            # 需要有颜色重叠
            if not required_colors & detected_colors:
                return False

        # 检查各色比例阈值
        for ratio_key, (lo, hi) in [
            ("red_ratio", pattern_def.get("red_ratio")),
            ("white_ratio", pattern_def.get("white_ratio")),
            ("black_ratio", pattern_def.get("black_ratio")),
            ("earthy_ratio", pattern_def.get("earthy_ratio")),
        ]:
            if ratio_key is not None and lo is not None:
                val = profile.get(ratio_key, 0)
                if not (lo <= val <= hi):
                    return False

        return True

    def _match_pattern_vs_colors(
        self, pattern: str, color_names: list, country: str
    ) -> bool:
        """将纹样描述与色彩特征进行模糊匹配"""
        pattern_lower = pattern.lower() if pattern else ""
        colors_lower = " ".join(color_names).lower()

        # 检查纹样关键词是否与色彩特征存在关联
        taboo_keywords = {
            "纳粹": ["大红", "雪白", "玄黑"],
            "万字符": ["大红", "金色", "玄黑"],
            "菊花": ["明黄", "金色", "雪白"],
            "十字架": ["金色", "雪白", "玄黑"],
            "图腾": ["茶色", "大红", "玄黑"],
        }

        for keyword, associated_colors in taboo_keywords.items():
            if keyword in pattern_lower:
                # 检查是否有关联色
                for ac in associated_colors:
                    if ac in colors_lower:
                        return True

        return False

# ========== 规则库管理（保持不变） ==========

    def get_rules(self, page=1, per_page=50, country=None, category=None):
        """获取规则列表 - 使用安全的参数化查询"""
        db = self._get_db()
        cursor = db.cursor()
        conditions = ["1=1"]
        params = []
        if country:
            conditions.append("country=?")
            params.append(country)
        if category:
            conditions.append("category=?")
            params.append(category)

        where = " AND ".join(conditions)
        offset = (page - 1) * per_page

        cursor.execute(
            f"SELECT COUNT(*) as total FROM compliance_rules WHERE {where}",
            params)
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"SELECT * FROM compliance_rules WHERE {where} "
            f"ORDER BY risk_level DESC, id LIMIT ? OFFSET ?",
            params + [per_page, offset])
        items = [dict(row) for row in cursor.fetchall()]
        return {"total": total, "page": page, "items": items}

    def add_rule(
        self,
        country: str,
        category: str,
        keywords: list,
        reason: str,
        suggestion: str,
        risk_level="高风险",
        pattern=None,
        region=None,
    ):
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO compliance_rules (country, region, category, keywords,
                pattern, risk_level, reason, suggestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                country,
                region,
                category,
                json.dumps(keywords, ensure_ascii=False),
                pattern,
                risk_level,
                reason,
                suggestion,
            ),
        )
        self.db.commit()
        return {"id": cursor.lastrowid, "message": "规则添加成功"}

    def update_rule(self, rule_id: int, **kwargs):
        allowed = ["country", "region", "category", "keywords", "pattern",
                   "risk_level", "reason", "suggestion", "status"]
        updates = {}
        for k, v in kwargs.items():
            if k in allowed:
                updates[k] = (json.dumps(v, ensure_ascii=False)
                             if k == "keywords" else v)

        if not updates:
            return {"error": "无有效字段"}

        sets = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [rule_id]
        db = self._get_db()
        db.execute(
            f"UPDATE compliance_rules SET {sets}, "
            f"updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values)
        db.commit()
        return {"message": "规则更新成功"}

    def delete_rule(self, rule_id: int):
        db = self._get_db()
        db.execute("DELETE FROM compliance_rules WHERE id=?", (rule_id,))
        db.commit()
        return {"message": "规则已删除"}

    def get_audit_logs(self, page=1, per_page=50, risk_level=None):
        """获取审核日志 - 使用安全的参数化查询"""
        db = self._get_db()
        cursor = db.cursor()
        conditions = ["1=1"]
        params = []
        if risk_level:
            conditions.append("risk_level=?")
            params.append(risk_level)

        where = " AND ".join(conditions)
        offset = (page - 1) * per_page

        cursor.execute(
            f"SELECT COUNT(*) as total FROM audit_log WHERE {where}", params)
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"SELECT * FROM audit_log WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [per_page, offset])
        items = [dict(row) for row in cursor.fetchall()]
        return {"total": total, "page": page, "items": items}

    def get_stats(self):
        db = self._get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) as cnt FROM compliance_rules WHERE status='active'")
        rules_count = cursor.fetchone()["cnt"]
        cursor.execute("""
            SELECT risk_level, COUNT(*) as cnt FROM audit_log
            WHERE created_at > datetime('now', '-30 days')
            GROUP BY risk_level
        """)
        risk_stats = {row["risk_level"]: row["cnt"]
                      for row in cursor.fetchall()}
        total_audited = sum(risk_stats.values())
        pass_rate = risk_stats.get("合规", 0) / max(1, total_audited)

        return {
            "rules_count": rules_count,
            "monthly_audits": total_audited,
            "pass_rate": round(pass_rate, 2),
            "risk_distribution": risk_stats
        }
