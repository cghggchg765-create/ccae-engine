# CCAE 跨文化适配引擎 API 文档 v1.1.0

## 概述

CCAE（Cross-Cultural Adaptation Engine，跨文化适配引擎）为汉服出海项目提供汉服专业翻译、文化禁忌合规审核、视觉识别、审美匹配、知识库、个性化推荐等全栈API服务。

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
| **P0** | 合规 | `/api/compliance/audit/text` | POST | 文本合规审核 |
| **P0** | 合规 | `/api/compliance/audit/image` | POST | 图片合规审核 |
| **P0** | 合规 | `/api/compliance/rules` | GET/POST | 规则库管理 |
| **P1** | 视觉 | `/api/vision/analyze` | POST | 汉服视觉识别 |
| **P1** | 视觉 | `/api/vision/aesthetic-match` | POST | 区域审美匹配 |
| **P1** | 知识库 | `/api/knowledge` | GET/POST | 知识库管理 |
| **P1** | 知识库 | `/api/knowledge/generate-copy` | POST | 文案生成 |
| **P1** | AI供应商 | `/api/ai/providers` | GET/POST | 供应商列表/添加 |
| **P1** | AI供应商 | `/api/ai/providers/:id` | GET/PUT/DELETE | 供应商详情/更新/删除 |
| **P1** | AI供应商 | `/api/ai/providers/:id/activate` | POST | 激活供应商 |
| **P1** | AI供应商 | `/api/ai/providers/:id/test` | POST | 测试连接 |
| **P1** | AI供应商 | `/api/ai/current` | GET | 当前激活供应商 |
| **P2** | 推荐 | `/api/recommend` | POST | 个性化推荐 |
| **P2** | 看板 | `/api/dashboard/overview` | GET | 数据总览 |
| **P2** | 看板 | `/api/dashboard/daily` | GET | 每日趋势数据 |
| **P2** | 权限 | `/api/users` | GET/POST | 用户管理 |

---

## P1 — AI 供应商管理模块（v1.1.0 新增）

### GET /api/ai/providers

获取所有供应商配置列表。

**响应示例：**

```json
{
  "success": true,
  "count": 3,
  "data": [
    {
      "id": "openai",
      "name": "OpenAI",
      "provider_type": "openai",
      "is_active": false,
      "endpoints": [{
        "id": "openai-default",
        "name": "OpenAI 官方",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "is_default": true,
        "status": "active",
        "model_mapping": {
          "primary": "gpt-4o-mini",
          "light": "gpt-4o-mini",
          "balanced": "gpt-4o",
          "strongest": "gpt-4o"
        }
      }]
    }
  ]
}
```

### POST /api/ai/providers

添加新供应商。

**请求参数：**

```json
{
  "provider_type": "openai",
  "name": "我的OpenAI"
}
```

**支持类型**: `openai` / `deepseek` / `qwen` / `custom`

### PUT /api/ai/providers/:id

更新供应商配置。

**请求参数：**

```json
{
  "endpoints": [{
    "id": "default",
    "name": "默认端点",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-xxxxxxxx",
    "model_mapping": {
      "primary": "gpt-4o-mini",
      "light": "gpt-3.5-turbo",
      "balanced": "gpt-4o",
      "strongest": "gpt-4o"
    },
    "is_default": true
  }]
}
```

### POST /api/ai/providers/:id/activate

激活指定供应商（取消其他供应商激活状态）。

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": "openai",
    "name": "OpenAI",
    "is_active": true
  }
}
```

### POST /api/ai/providers/:id/test

测试供应商 API 连接。

**请求参数（可选）：**

```json
{
  "endpoint_id": "openai-default"
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "连接成功",
  "latency_ms": 150
}
```

### GET /api/ai/current

获取当前激活的供应商配置。

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": "openai",
    "name": "OpenAI",
    "is_active": true,
    "endpoints": [...]
  }
}
```

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
      "cultural_note": "马面裙为最具辨识度的汉服单品..."
    }
  ],
  "confidence": 0.67,
  "response_time_ms": 1
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
    "suggestion": "建议移除与伊斯兰教义冲突的元素"
  }],
  "status": "review"
}
```

**风险等级**: `合规` / `低风险` / `高风险`

---

## P2 — 数据看板模块

### GET /api/dashboard/overview

全模块数据总览。

**响应示例：**

```json
{
  "corpus_count": 22,
  "rules_count": 18,
  "monthly_translations": 150,
  "avg_translation_confidence": 0.85,
  "monthly_audits": 80,
  "pass_rate": 0.75,
  "high_risk_rate": 0.10,
  "vision_analyses": 30,
  "knowledge_entries": 10
}
```

### GET /api/dashboard/daily

获取近30天每日趋势数据（用于图表）。

**响应示例：**

```json
{
  "translations": [
    {"day": "2026-05-01", "translations": 5, "avg_conf": 0.85},
    {"day": "2026-05-02", "translations": 8, "avg_conf": 0.90}
  ],
  "audits": [
    {"day": "2026-05-01", "passed": 3, "high_risk": 1},
    {"day": "2026-05-02", "passed": 5, "high_risk": 0}
  ]
}
```

---

## 4层模型映射说明

CCAE 参考 CC Switch 设计理念，定义了 4 层模型映射标准：

| 层级 | 设计用途 | 典型模型 |
|------|----------|----------|
| **Primary** | 日常主要使用 | gpt-4o-mini, deepseek-chat, qwen-turbo |
| **Light** | 简单任务、快速响应 | gpt-3.5-turbo, deepseek-chat, qwen-turbo |
| **Balanced** | 复杂任务、质量优先 | gpt-4o, deepseek-chat, qwen-plus |
| **Strongest** | 最复杂推理 | gpt-4o, deepseek-reasoner, qwen-max |

---

## 部署说明

```bash
cd ccae-engine
pip install -r requirements.txt
python backend/database.py   # 初始化数据库+种子数据
python run.py                # 启动服务（端口5000）
```

管理后台: `http://127.0.0.1:5000/`（默认账号: admin / admin123）