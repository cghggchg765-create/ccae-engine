# CCAE 跨文化适配引擎

> Cross-Cultural Adaptation Engine — 华裳出海核心引擎

## 项目简介

为「华裳出海 — 汉服TikTok全球运营」项目打造的跨文化适配引擎，解决汉服出海三大核心痛点：

- 🌐 **翻译不准** → 5000+汉服专业术语库 + 自动文化注释
- 🛡️ **文化踩雷** → 150+国家禁忌规则库 + 文本/图片双审核
- 🎯 **推送不精准** → 区域审美匹配 + 个性化推荐

## 技术栈

- **后端**: Python Flask + SQLite
- **前端**: 原生 HTML/CSS/JS（SPA）
- **风格**: 国风+科技蓝暗色主题

## 快速开始

```bash
pip install flask flask-cors openpyxl pillow
python backend/database.py
python backend/app.py
```

访问 `http://127.0.0.1:5000/` （账号: admin / admin123）

## 模块说明

| 优先级 | 模块 | API端点 | 状态 |
|--------|------|---------|------|
| P0 | 智能翻译 | POST /api/translate | ✅ |
| P0 | 合规审核 | POST /api/compliance/audit/text | ✅ |
| P1 | 视觉识别 | POST /api/vision/analyze | ✅ |
| P1 | 知识库 | GET /api/knowledge | ✅ |
| P2 | 推荐引擎 | POST /api/recommend | ✅ |
| P2 | 数据看板 | GET /api/dashboard/overview | ✅ |

## 文档

- [API文档](docs/API.md)
- [操作手册](docs/MANUAL.md)
- [部署说明](docs/DEPLOY.md)
