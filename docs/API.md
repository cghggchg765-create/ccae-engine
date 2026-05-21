# CCAE跨文化适配引擎 API 文档 v1.0

## 概述

CCAE（Cross-Cultural Adaptation Engine）为华裳出海项目核心引擎，提供汉服专业翻译、文化禁忌合规审核、视觉识别、审美匹配、知识库、个性化推荐等全栈API服务。

- **Base URL**: `http://127.0.0.1:5000`
- **数据格式**: JSON（请求/响应）
- **编码**: UTF-8
- **鉴权**: 预留 Token 鉴权（当前开发阶段开放）

---

## API 端点一览

| 优先级 | 模块 | 端点 | 方法 | 说明 |
|--------|------|------|------|------|
| **P0** | 翻译 | `/api/translate` | POST | 汉服专业翻译 |
| **P0** | 翻译 | `/api/corpus` | GET/POST | 语料库管理 |
| **P0** | 翻译 | `/api/corpus/:id` | PUT/DELETE | 术语编辑/删除 |
| **P0** | 翻译 | `/api/translate/stats` | GET | 翻译统计 |
| **P0** | 合规 | `/api/compliance/audit/text` | POST | 文本合规审核 |
| **P0** | 合规 | `/api/compliance/audit/image` | POST | 图片合规审核 |
| **P0** | 合规 | `/api/compliance/rules` | GET/POST | 规则库管理 |
| **P0** | 合规 | `/api/compliance/rules/:id` | PUT/DELETE | 规则编辑/删除 |
| **P0** | 合规 | `/api/compliance/logs` | GET | 审核日志 |
| **P0** | 合规 | `/api/compliance/stats` | GET | 审核统计 |
| **P1** | 视觉 | `/api/vision/analyze` | POST | 汉服视觉识别 |
| **P1** | 视觉 | `/api/vision/aesthetic-match` | POST | 区域审美匹配 |
| **P1** | 视觉 | `/api/vision/preferences` | GET/POST | 审美偏好管理 |
| **P1** | 知识库 | `/api/knowledge` | GET/POST | 知识库管理 |
| **P1** | 知识库 | `/api/knowledge/generate-copy` | POST | 文案生成 |
| **P2** | 推荐 | `/api/recommend` | POST | 个性化推荐 |
| **P2** | 推荐 | `/api/recommend/logs` | GET | 推荐日志 |
| **P2** | 看板 | `/api/dashboard/overview` | GET | 数据总览 |
| **P2** | 看板 | `/api/users` | GET/POST | 用户管理 |

---

## P0 — 智能翻译模块

### POST /api/translate

汉服专业翻译，优先匹配语料库术语并自动附加文化注释。

**请求参数：**

```json
{
  "text": "她穿着马面裙和云肩，上面绣着精美的云纹。",
  "target_lang": "en"
}
```

**支持语种**: `en` / `ja` / `ko` / `es` / `fr` / `ar`

**响应示例：**

```json
{
  "source": "她穿着马面裙...",
  "target_lang": "en",
  "translated": "她穿着Mamian Qun (Horse-Face Skirt)和Cloud Collar...",
  "matched_terms": [
    {
      "term": "马面裙",
      "translated": "Mamian Qun (Horse-Face Skirt)",
      "cultural_note": "马面裙为最具辨识度的汉服单品，非'马面'之意..."
    }
  ],
  "confidence": 0.67,
  "response_time_ms": 1
}
```

### GET /api/corpus

语料库分页查询。

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码（默认1） |
| per_page | int | 每页条数（默认50） |
| category | string | 分类筛选（形制/纹样/工艺/礼仪/朝代） |
| keyword | string | 关键词搜索 |

### POST /api/corpus

添加术语。

```json
{
  "term_zh": "缂丝",
  "category": "工艺",
  "definition": "通经断纬的高级丝织工艺",
  "cultural_note": "一寸缂丝一寸金，非遗",
  "tags": "[\"非遗\",\"丝织\"]",
  "translations": {
    "en": "Kesi Silk Tapestry",
    "ja": "綴織（けし）"
  }
}
```

---

## P0 — 文化禁忌合规审核模块

### POST /api/compliance/audit/text

文本合规审核，基于150+国家规则库。

**请求参数：**

```json
{
  "text": "这款汉服使用猪皮材质，搭配酒类主题纹样。",
  "country": "沙特阿拉伯"
}
```

**响应示例：**

```json
{
  "content_type": "text",
  "target_country": "沙特阿拉伯",
  "risk_level": "高风险",
  "matched_rules_count": 1,
  "matched_rules": [{
    "category": "宗教禁忌",
    "risk_level": "高风险",
    "reason": "含宗教禁忌元素，可能引发穆斯林消费者强烈反感",
    "suggestion": "建议移除与伊斯兰教义冲突的元素，替换为几何纹样或植物纹样"
  }],
  "reasons": ["含宗教禁忌元素..."],
  "suggestions": ["建议移除..."],
  "response_time_ms": 0,
  "status": "review"
}
```

**风险等级**: `合规` / `低风险` / `高风险`

### POST /api/compliance/audit/image

图片合规审核，识别敏感纹样/宗教符号。

```json
{
  "image_path": "/images/hanfu_pattern.png",
  "country": "德国"
}
```

### GET /api/compliance/rules

规则库查询。参数: `country`, `category`, `page`

### POST /api/compliance/rules

添加规则。

```json
{
  "country": "沙特阿拉伯",
  "category": "宗教禁忌",
  "keywords": ["猪", "猪肉", "酒精"],
  "reason": "含宗教禁忌元素",
  "suggestion": "移除冲突元素",
  "risk_level": "高风险"
}
```

---

## P1 — 视觉识别模块

### POST /api/vision/analyze

识别汉服朝代/形制/色彩/纹样。

**响应示例：**

```json
{
  "dynasty": "明",
  "format": "马面裙",
  "colors": ["红色", "金色", "藏青"],
  "patterns": ["云纹", "缠枝莲"],
  "confidence": 0.88,
  "response_time_ms": 1
}
```

### POST /api/vision/aesthetic-match

匹配区域审美偏好。

```json
{
  "visual_tags": {"colors": ["红色","金色"], "patterns": ["云纹"]},
  "region": "北美"
}
```

---

## P1 — 知识库模块

### POST /api/knowledge/generate-copy

生成适配区域的短视频文案。

```json
{
  "topic": "马面裙穿搭",
  "region": "东南亚"
}
```

**响应：**

```json
{
  "short_copy": "探索汉服的魅力——如纱笼般飘逸。马面裙穿搭，带你领略千年华裳之美。",
  "hashtags": ["#Hanfu", "#ChineseCulture", "#东南亚Fashion"],
  "cultural_note": "此内容已适配东南亚区域文化偏好"
}
```

---

## P2 — 其他API

### GET /api/dashboard/overview

全模块数据总览（语料库数、规则数、翻译量、审核通过率、高风险率等）。

### POST /api/recommend

个性化推荐（基于用户画像+视觉标签+审美偏好）。

---

## 部署说明

```bash
cd ccae-engine
pip install flask flask-cors openpyxl pillow
python backend/database.py   # 初始化数据库+种子数据
python backend/app.py        # 启动服务（端口5000）
```

管理后台: `http://127.0.0.1:5000/`（默认账号: admin / admin123）
