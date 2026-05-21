"""视觉识别与审美匹配服务 — 基于Pillow图像分析的规则引擎"""

import json
import time
import hashlib
import os
from PIL import Image, ImageStat
from database import get_db
from config import Config


# ---- 色彩映射：RGB范围 → 中文色彩名 ----
COLOR_MAP = [
    # (中文名, R_min, R_max, G_min, G_max, B_min, B_max)
    ("朱红", 180, 255, 30, 80, 20, 70),
    ("大红", 200, 255, 20, 60, 20, 60),
    ("暗红", 120, 180, 20, 50, 20, 50),
    ("金色", 200, 255, 160, 220, 40, 100),
    ("明黄", 220, 255, 200, 255, 30, 100),
    ("藏青", 10, 50, 30, 80, 100, 180),
    ("靛蓝", 20, 60, 40, 100, 120, 220),
    ("天蓝", 100, 180, 160, 220, 200, 255),
    ("墨绿", 10, 60, 80, 140, 40, 90),
    ("翠绿", 30, 100, 140, 220, 60, 140),
    ("紫色", 100, 160, 20, 80, 120, 200),
    ("雪白", 230, 255, 230, 255, 230, 255),
    ("米白", 220, 245, 210, 240, 190, 220),
    ("玄黑", 0, 35, 0, 35, 0, 35),
    ("深灰", 60, 120, 60, 120, 60, 120),
    ("浅粉", 220, 255, 160, 210, 180, 220),
    ("藕荷", 180, 220, 150, 190, 160, 200),
    ("月白", 210, 240, 220, 245, 235, 255),
    ("秋香", 160, 200, 140, 180, 60, 110),
    ("茶色", 120, 170, 80, 130, 50, 90),
]

# ---- 朝代/形制分类规则（基于色彩分布特征） ----
# 规则按优先级排列，命中第一个即返回
DYNASTY_RULES = [
    # (朝代, 形制候选列表, 色彩特征条件)
    ("唐", ["齐胸襦裙", "大袖衫", "圆领袍", "诃子裙"],
     {"bright_ratio": (0.3, 1.0), "warm_ratio": (0.4, 1.0),
      "desc": "唐代尚艳丽的红、黄、金等暖色，饱和度高"}),
    ("宋", ["褙子", "百迭裙", "两片裙", "直裰"],
     {"bright_ratio": (0.1, 0.35), "warm_ratio": (0.1, 0.5),
      "desc": "宋代尚淡雅素净，低饱和度冷色调为主"}),
    ("明", ["马面裙", "袄裙", "补服", "披风"],
     {"bright_ratio": (0.2, 0.5), "warm_ratio": (0.3, 0.6),
      "desc": "明代配色端庄典雅，红蓝金搭配讲究等级"}),
    ("魏晋", ["交领襦裙", "杂裾垂髾服", "大袖衫"],
     {"bright_ratio": (0.06, 0.25), "warm_ratio": (0.1, 0.5),
      "desc": "魏晋尚清雅飘逸，色彩朴素自然"}),
    ("秦汉", ["深衣", "曲裾", "直裾"],
     {"bright_ratio": (0.05, 0.3), "warm_ratio": (0.1, 0.5),
      "desc": "秦汉以玄黑、赤红为主，庄重肃穆"}),
    ("清", ["旗装", "氅衣", "马褂"],
     {"bright_ratio": (0.2, 0.55), "warm_ratio": (0.2, 0.7),
      "desc": "清代繁复华丽，刺绣密集，色彩丰富"}),
    ("现代改良", ["改良旗袍", "新中式", "汉元素"],
     {"bright_ratio": (0.15, 0.7), "warm_ratio": (0.2, 0.8),
      "desc": "现代改良融合传统与现代审美"}),
]

# ---- 纹样关键词（基于色彩分布推断） ----
PATTERN_HINTS = {
    "红色主调+金色点缀": ["云纹", "龙凤纹", "缠枝莲"],
    "蓝色主调+白色": ["云纹", "海水江崖", "梅兰竹菊"],
    "金色主调+红色": ["龙凤纹", "云纹", "八宝纹"],
    "绿色主调+花卉": ["缠枝莲", "牡丹纹", "卷草纹"],
    "素色为主": ["暗纹", "提花", "素面"],
    "多色繁复": ["百花纹", "八仙纹", "博古纹"],
}


class VisionAnalyzer:
    """汉服视觉识别引擎 — 基于图像分析的规则分类器"""

    DYNASTIES = Config.DYNASTIES
    FORMATS = Config.FORMATS
    REGIONS = Config.REGIONS

    def __init__(self):
        self.db = get_db()

    # ========== 主识别方法 ==========

    def analyze(self, image_path: str) -> dict:
        """识别汉服朝代/形制/色彩/纹样 — 基于真实图像分析"""
        start = time.time()

        # 尝试读取真实图片文件
        try:
            img = self._load_image(image_path)
            dominant_colors = self._extract_dominant_colors(img, n=6)
            color_names = self._map_colors(dominant_colors)
            bright_ratio, warm_ratio, saturation = self._compute_color_stats(img)
            result = self._classify(color_names, bright_ratio, warm_ratio, saturation)
        except (FileNotFoundError, IOError, OSError) as e:
            # 图片不可读时，基于文件名做启发式推断
            color_names, result = self._fallback_classify(image_path)

        response_time_ms = int((time.time() - start) * 1000)

        # 记录日志
        image_hash = hashlib.md5(image_path.encode()).hexdigest()
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO vision_log (image_hash, dynasty, format, colors, patterns,
                confidence, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (image_hash, result["dynasty"], result["format"],
              json.dumps(result["colors"], ensure_ascii=False),
              json.dumps(result["patterns"], ensure_ascii=False),
              result["confidence"], response_time_ms))
        self.db.commit()

        result["response_time_ms"] = response_time_ms
        return result

    # ========== 图像加载与分析 ==========

    def _load_image(self, path: str) -> Image.Image:
        """加载图片，支持相对路径和绝对路径"""
        if not os.path.isabs(path):
            # 尝试多个可能的基础路径
            candidates = [
                path,
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.abspath(__file__)))), path),
            ]
        else:
            candidates = [path]

        for p in candidates:
            if os.path.isfile(p):
                return Image.open(p).convert("RGB")

        raise FileNotFoundError(f"图片文件未找到: {path} (尝试了 {candidates})")

    def _extract_dominant_colors(self, img: Image.Image, n: int = 6) -> list:
        """提取主色调 — 缩小后采样取前N个高频色"""
        small = img.resize((50, 50), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())

        # 量化：将颜色归并到更粗的bucket
        bucket = {}
        for r, g, b in pixels:
            key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
            bucket[key] = bucket.get(key, 0) + 1

        sorted_colors = sorted(bucket.items(), key=lambda x: -x[1])
        return [color for color, _ in sorted_colors[:n]]

    def _map_colors(self, rgb_list: list) -> list:
        """将RGB值映射为中文色彩名"""
        names = []
        seen = set()
        for r, g, b in rgb_list:
            best_name = None
            best_dist = float("inf")
            for name, r_min, r_max, g_min, g_max, b_min, b_max in COLOR_MAP:
                # 检查RGB是否落在范围内
                center_r = (r_min + r_max) / 2
                center_g = (g_min + g_max) / 2
                center_b = (b_min + b_max) / 2
                dist = ((r - center_r) ** 2 + (g - center_g) ** 2 +
                        (b - center_b) ** 2) ** 0.5
                if dist < best_dist:
                    best_dist = dist
                    best_name = name
            if best_name and best_name not in seen:
                names.append(best_name)
                seen.add(best_name)
        return names[:4]  # 最多4种色

    def _compute_color_stats(self, img: Image.Image) -> tuple:
        """计算色彩统计：亮度比例、暖色比例、平均饱和度"""
        small = img.resize((100, 100), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())

        total = len(pixels)
        bright_count = 0
        warm_count = 0
        total_sat = 0

        for r, g, b in pixels:
            # 亮度 = (R+G+B)/3
            brightness = (r + g + b) / 3
            if brightness > 150:
                bright_count += 1

            # 暖色判定：R相对G和B偏高
            if r > g + 20 and r > b + 20:
                warm_count += 1

            # 饱和度简化计算
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            if max_c > 0:
                total_sat += (max_c - min_c) / max_c

        return (
            bright_count / total,       # bright_ratio
            warm_count / total,          # warm_ratio
            total_sat / total            # avg_saturation
        )

    def _classify(self, color_names: list, bright_ratio: float,
                  warm_ratio: float, saturation: float) -> dict:
        """基于色彩特征进行朝代/形制/纹样分类"""
        # 匹配朝代规则
        dynasty = None
        candidates = []

        for d_name, d_candidates, conditions in DYNASTY_RULES:
            br_min, br_max = conditions["bright_ratio"]
            wr_min, wr_max = conditions["warm_ratio"]
            if br_min <= bright_ratio <= br_max and wr_min <= warm_ratio <= wr_max:
                dynasty = d_name
                candidates = d_candidates
                break

        # 无匹配时默认
        if dynasty is None:
            dynasty = "明"
            candidates = ["马面裙", "袄裙"]

        # 选取形制（基于饱和度微调）
        if saturation > 0.5:
            fmt = candidates[0]  # 高饱和偏华丽形制
        elif saturation < 0.2:
            fmt = candidates[-1]  # 低饱和偏素雅形制
        else:
            fmt = candidates[min(1, len(candidates) - 1)]

        # 推断纹样
        patterns = self._infer_patterns(color_names, bright_ratio, saturation)

        # 置信度基于规则匹配质量
        # 匹配到的规则越精确，置信度越高
        dist_from_center = min(
            abs(bright_ratio - (br_min + br_max) / 2) +
            abs(warm_ratio - (wr_min + wr_max) / 2)
            for _, _, c in DYNASTY_RULES
            if (br_min := c["bright_ratio"][0]) is not None
        )
        confidence = round(max(0.55, min(0.92, 0.92 - dist_from_center * 0.5)), 2)

        return {
            "dynasty": dynasty,
            "format": fmt,
            "colors": color_names if color_names else ["红色", "金色", "藏青"],
            "patterns": patterns,
            "confidence": confidence
        }

    def _infer_patterns(self, color_names: list, bright_ratio: float,
                        saturation: float) -> list:
        """根据色彩特征推断可能的纹样"""
        colors_str = "、".join(color_names)

        if saturation > 0.45 and "红" in colors_str:
            return ["云纹", "缠枝莲", "龙凤纹"]
        elif saturation > 0.45:
            return ["百花纹", "牡丹纹", "云纹"]
        elif bright_ratio < 0.25:
            return ["暗纹", "提花", "素面"]
        elif "蓝" in colors_str and "白" in colors_str:
            return ["云纹", "海水江崖", "梅兰竹菊"]
        elif "金" in colors_str:
            return ["云纹", "八宝纹", "龙凤纹"]
        elif "绿" in colors_str:
            return ["缠枝莲", "卷草纹", "牡丹纹"]
        else:
            return ["云纹", "缠枝莲", "暗纹"]

    def _fallback_classify(self, image_path: str) -> tuple:
        """图片不可读时的回退方案 — 基于文件名推断"""
        path_lower = image_path.lower()
        color_names = []

        # 从文件名提取色彩提示
        for cn_name, _, _, _, _, _, _ in COLOR_MAP:
            if cn_name in path_lower:
                color_names.append(cn_name)

        if not color_names:
            color_names = ["红色", "金色", "藏青"]

        result = {
            "dynasty": "明",
            "format": "马面裙",
            "colors": color_names[:4],
            "patterns": ["云纹", "缠枝莲"],
            "confidence": 0.45  # 回退时置信度较低
        }
        return color_names, result

    # ========== 审美匹配（保持不变，算法优化） ==========

    def match_aesthetic(self, visual_tags: dict, target_region: str) -> dict:
        """匹配区域审美偏好"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT * FROM aesthetic_preferences
            WHERE region=? OR region='全球'
        """, (target_region,))

        prefs = cursor.fetchall()
        color_prefs = []
        pattern_prefs = []
        style_prefs = []

        for p in prefs:
            if p["category"] == "色彩":
                color_prefs.append({"preference": p["preference"],
                                    "weight": p["weight"]})
            elif p["category"] == "纹样":
                pattern_prefs.append({"preference": p["preference"],
                                      "weight": p["weight"]})
            elif p["category"] == "风格":
                style_prefs.append({"preference": p["preference"],
                                    "weight": p["weight"]})

        # 改进匹配：实际比对visual_tags与偏好的关键词重叠
        input_colors = visual_tags.get("colors", [])
        input_patterns = visual_tags.get("patterns", [])

        color_match = self._calculate_match_v2(input_colors, color_prefs)
        pattern_match = self._calculate_match_v2(input_patterns, pattern_prefs)

        return {
            "region": target_region,
            "color_match": color_match,
            "pattern_match": pattern_match,
            "overall_match": round((color_match + pattern_match) / 2, 2),
            "recommendations": {
                "colors": [p["preference"] for p in color_prefs[:3]],
                "patterns": [p["preference"] for p in pattern_prefs[:3]],
                "styles": [p["preference"] for p in style_prefs[:3]]
            }
        }

    def _calculate_match(self, tags: list, prefs: list) -> float:
        """简化匹配（向后兼容）"""
        if not prefs:
            return 0.5
        score = sum(p["weight"] for p in prefs[:3])
        return round(min(1.0, score), 2)

    def _calculate_match_v2(self, tags: list, prefs: list) -> float:
        """改进版匹配：实际比对各偏好与标签的关键词重叠度"""
        if not prefs:
            return 0.5
        if not tags:
            return sum(p["weight"] for p in prefs) / len(prefs) * 0.3

        total_weight = 0
        matched_weight = 0

        for p in prefs:
            pref_text = p["preference"].lower()
            weight = p["weight"]
            total_weight += weight

            # 检查是否有任何标签与偏好匹配
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in pref_text or any(
                        kw in tag_lower for kw in pref_text.split("、")):
                    matched_weight += weight * 0.8  # 部分匹配
                    break
                elif any(kw in pref_text for kw in tag_lower.split("、")):
                    matched_weight += weight * 0.6
                    break

        if total_weight == 0:
            return 0.5

        return round(min(1.0, matched_weight / total_weight), 2)

    # ---- 审美库管理 ----

    def get_preferences(self, region=None):
        cursor = self.db.cursor()
        if region:
            cursor.execute(
                "SELECT * FROM aesthetic_preferences WHERE region=? "
                "ORDER BY category", (region,))
        else:
            cursor.execute(
                "SELECT * FROM aesthetic_preferences "
                "ORDER BY region, category")
        return [dict(row) for row in cursor.fetchall()]

    def add_preference(self, region: str, category: str, preference: str,
                       weight=0.5, notes=""):
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO aesthetic_preferences (region, category, preference,
                weight, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (region, category, preference, weight, notes))
        self.db.commit()
        return {"id": cursor.lastrowid, "message": "偏好添加成功"}

    def delete_preference(self, pref_id: int):
        self.db.execute("DELETE FROM aesthetic_preferences WHERE id=?",
                        (pref_id,))
        self.db.commit()
        return {"message": "偏好已删除"}

    def get_vision_stats(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM vision_log")
        total = cursor.fetchone()["cnt"]
        cursor.execute("""
            SELECT AVG(confidence) as avg FROM vision_log
            WHERE created_at > datetime('now', '-7 days')
        """)
        avg = cursor.fetchone()["avg"]
        return {
            "total_analyzed": total,
            "avg_confidence_7d": round(avg or 0, 2)
        }
