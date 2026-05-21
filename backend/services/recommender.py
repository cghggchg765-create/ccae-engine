"""推荐引擎与知识库服务 — 基于多维匹配算法的个性化推荐"""

import json
import time
from database import get_db


class Recommender:
    """个性化推荐引擎 — 基于多维度匹配评分"""

    def __init__(self):
        self.db = get_db()

    def recommend(self, user_profile: dict, visual_tags: dict,
                  target_region: str) -> dict:
        """基于用户画像+视觉标签+审美偏好+区域做匹配推荐"""
        cursor = self.db.cursor()

        # 1. 获取目标区域审美偏好（作为权重参考）
        cursor.execute(
            "SELECT * FROM aesthetic_preferences WHERE region=?",
            (target_region,))
        prefs = [dict(row) for row in cursor.fetchall()]

        # 2. 获取全部知识库条目（不再随机抽取）
        cursor.execute("SELECT * FROM knowledge_base")
        all_items = [dict(row) for row in cursor.fetchall()]

        if not all_items:
            return {
                "content": [],
                "products": [],
                "confidence": 0,
                "message": "知识库为空"
            }

        # 3. 为每条知识库条目计算匹配得分
        scored_items = []
        user_interests = user_profile.get("interests", [])
        user_age = user_profile.get("age", "25-34")
        visual_colors = visual_tags.get("colors", [])
        visual_patterns = visual_tags.get("patterns", [])

        for item in all_items:
            score = self._calculate_score(
                item, user_interests, user_age,
                visual_colors, visual_patterns,
                target_region, prefs
            )
            scored_items.append((score, item))

        # 4. 按得分排序，取前5条
        scored_items.sort(key=lambda x: -x[0])
        top_items = scored_items[:5]

        # 5. 构建推荐结果
        recommendations = {"content": [], "products": []}

        for score, item in top_items:
            reason = self._generate_reason(
                item, score, target_region, visual_colors, visual_patterns)
            recommendations["content"].append({
                "title": item["title_zh"],
                "category": item["category"],
                "score": round(score, 2),
                "reason": reason
            })

        # 6. 计算置信度 — 基于得分分布
        if top_items:
            scores = [s for s, _ in top_items]
            avg_score = sum(scores) / len(scores)
            # 得分0-3映射到0-1的置信度
            confidence = round(min(0.85, max(0.25, avg_score / 3.0)), 2)
        else:
            confidence = 0.0

        recommendations["confidence"] = confidence

        # 7. 记录推荐日志
        cursor.execute("""
            INSERT INTO recommend_log (user_profile, visual_tags, region,
                recommended_items)
            VALUES (?, ?, ?, ?)
        """, (json.dumps(user_profile, ensure_ascii=False),
              json.dumps(visual_tags, ensure_ascii=False),
              target_region,
              json.dumps(recommendations, ensure_ascii=False)))
        self.db.commit()

        return recommendations

    def _calculate_score(self, item: dict, interests: list, age: str,
                         colors: list, patterns: list,
                         region: str, prefs: list) -> float:
        """多维匹配得分计算（0-3分制）"""
        score = 0.0

        # 维度1：类别与兴趣匹配 (0-0.8)
        category = item.get("category", "")
        content = item.get("content_zh", "")
        title = item.get("title_zh", "")

        for interest in interests:
            if interest.lower() in category.lower():
                score += 0.4
            if interest.lower() in title.lower():
                score += 0.3
            if interest.lower() in (content or "").lower():
                score += 0.1
        score += min(0.8, score)  # 封顶

        # 维度2：视觉标签匹配 (0-0.6)
        text_to_check = f"{title} {content or ''}"
        for color in colors:
            if color in text_to_check:
                score += 0.2
                break
        for pattern in patterns:
            if pattern in text_to_check:
                score += 0.15
                break

        # 维度3：区域文化类比匹配 (0-0.8)
        analogies = json.loads(item.get("cultural_analogies", "{}") or "{}")
        if region in analogies:
            score += 0.6
        elif any(r in str(analogies) for r in [region, region[:2]]):
            score += 0.3

        # 维度4：审美偏好匹配 (0-0.5)
        for pref in prefs:
            pref_text = pref.get("preference", "").lower()
            weight = pref.get("weight", 0.5)
            # 检查偏好关键词是否出现在条目中
            pref_kws = pref_text.replace("（", " ").replace("）", " ").split()
            for kw in pref_kws:
                if len(kw) > 1 and kw in text_to_check.lower():
                    score += weight * 0.3
                    break

        # 维度5：内容丰富度加分 (0-0.3)
        if content and len(content) > 200:
            score += 0.2
        if item.get("image_url"):
            score += 0.1

        return min(3.0, score)

    def _generate_reason(self, item: dict, score: float, region: str,
                         colors: list, patterns: list) -> str:
        """生成个性化的推荐理由"""
        reasons = []

        # 检查文化类比
        analogies = json.loads(item.get("cultural_analogies", "{}") or "{}")
        if region in analogies:
            reasons.append(f"与{region}文化共鸣：{analogies[region]}")

        # 检查视觉匹配
        content = item.get("content_zh", "")
        matched_colors = [c for c in colors if c in content]
        if matched_colors:
            reasons.append(f"配色风格契合{'、'.join(matched_colors)}调性")
        matched_patterns = [p for p in patterns if p in content]
        if matched_patterns:
            reasons.append(f"包含{'、'.join(matched_patterns)}纹样元素")

        # 检查类别
        category = item.get("category", "")
        if category:
            reasons.append(f"属于{category}类热门内容")

        if not reasons:
            reasons.append(f"匹配{region}用户偏好")

        # 取前2条理由
        return "；".join(reasons[:2])

    def get_recommend_logs(self, page=1, per_page=50):
        cursor = self.db.cursor()
        offset = (page - 1) * per_page
        cursor.execute("SELECT COUNT(*) as total FROM recommend_log")
        total = cursor.fetchone()["total"]
        cursor.execute(
            "SELECT * FROM recommend_log ORDER BY created_at DESC "
            "LIMIT ? OFFSET ?",
            (per_page, offset))
        return {
            "total": total, "page": page,
            "items": [dict(r) for r in cursor.fetchall()]
        }


class KnowledgeBase:
    """文化解读知识库"""

    def __init__(self):
        self.db = get_db()

    def search(self, keyword=None, category=None, page=1, per_page=20):
        cursor = self.db.cursor()
        conditions = ["1=1"]
        params = []
        if keyword:
            conditions.append(
                "(title_zh LIKE ? OR content_zh LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if category:
            conditions.append("category=?")
            params.append(category)

        where = " AND ".join(conditions)
        offset = (page - 1) * per_page

        cursor.execute(
            f"SELECT COUNT(*) as total FROM knowledge_base WHERE {where}",
            params)
        total = cursor.fetchone()["total"]
        cursor.execute(
            f"SELECT * FROM knowledge_base WHERE {where} "
            f"ORDER BY id LIMIT ? OFFSET ?",
            params + [per_page, offset])
        return {
            "total": total, "page": page,
            "items": [dict(r) for r in cursor.fetchall()]
        }

    def add_entry(self, category: str, title_zh: str, content_zh: str,
                  multilingual=None, image_url=None, cultural_analogies=None):
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO knowledge_base (category, title_zh, content_zh,
                multilingual, image_url, cultural_analogies)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, title_zh, content_zh,
              json.dumps(multilingual or {}, ensure_ascii=False),
              image_url,
              json.dumps(cultural_analogies or {}, ensure_ascii=False)))
        self.db.commit()
        return {"id": cursor.lastrowid, "message": "条目添加成功"}

    def update_entry(self, entry_id: int, **kwargs):
        allowed = ["category", "title_zh", "content_zh", "image_url"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if "multilingual" in kwargs:
            updates["multilingual"] = json.dumps(
                kwargs["multilingual"], ensure_ascii=False)
        if "cultural_analogies" in kwargs:
            updates["cultural_analogies"] = json.dumps(
                kwargs["cultural_analogies"], ensure_ascii=False)

        sets = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [entry_id]
        self.db.execute(
            f"UPDATE knowledge_base SET {sets} WHERE id=?", values)
        self.db.commit()
        return {"message": "条目更新成功"}

    def delete_entry(self, entry_id: int):
        self.db.execute("DELETE FROM knowledge_base WHERE id=?", (entry_id,))
        self.db.commit()
        return {"message": "条目已删除"}

    def generate_copy(self, topic: str, target_region: str) -> dict:
        """生成适配区域的短视频文案"""
        analogies = {
            "东南亚": "如纱笼般飘逸",
            "欧洲": "如维多利亚长裙般优雅",
            "北美": "堪比好莱坞红毯东方韵味",
            "日韩": "和韩服同源的东方美学",
            "中东": "东方长袍的奢华变奏",
            "拉美": "如弗拉门戈裙摆般热情",
            "全球": "独特的东方美学"
        }
        analogy = analogies.get(target_region, "独特的东方美学")

        # 根据区域偏好选择不同标签
        region_tags = {
            "东南亚": ["Hanfu", "ChineseCulture", "SoutheastAsiaStyle"],
            "欧洲": ["Hanfu", "ChineseCulture", "EuropeanFashion"],
            "北美": ["Hanfu", "ChineseCulture", "OrientalChic"],
            "日韩": ["Hanfu", "ChineseCulture", "EastAsianAesthetic"],
            "中东": ["Hanfu", "ChineseCulture", "ModestFashion"],
            "拉美": ["Hanfu", "ChineseCulture", "LatinoStyle"],
        }
        hashtags = region_tags.get(target_region,
                                   ["Hanfu", "ChineseCulture",
                                    f"{target_region}Fashion"])

        return {
            "topic": topic,
            "region": target_region,
            "short_copy": (f"探索汉服的魅力——{analogy}。{topic}，"
                          "带你领略千年华裳之美。"),
            "hashtags": [f"#{t}" for t in hashtags],
            "cultural_note": f"此内容已适配{target_region}区域文化偏好"
        }
