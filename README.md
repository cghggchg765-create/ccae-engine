# CCAE 跨文化适配引擎

> Cross-Cultural Adaptation Engine — 华裳出海核心引擎

## 项目简介

为「华裳出海 — 汉服TikTok全球运营」项目打造的跨文化适配引擎，解决汉服出海三大核心痛点：

- 🌐 **翻译不准** → 5000+汉服专业术语库 + 自动文化注释
- 🛡️ **文化踩雷** → 150+国家禁忌规则库 + 文本/图片双审核
- 🎯 **推送不精准** → 区域审美匹配 + 个性化推荐

## 技术栈

- **后端**: Python Flask + SQLite
- **前端**: 原生 HTML/CSS/JS（SPA）+ Chart.js
- **风格**: 国风+科技蓝暗色主题

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 初始化数据库
python backend/database.py

# 3. 启动服务
python run.py
```

访问 `http://127.0.0.1:5000/` （账号: admin / admin123）

## 模块说明

| 优先级 | 模块 | API端点 | 状态 |
|--------|------|---------|------|
| P0 | 智能翻译 | POST /api/translate | ✅ |
| P0 | 合规审核 | POST /api/compliance/audit/text | ✅ |
| P1 | 视觉识别 | POST /api/vision/analyze | ✅ |
| P1 | 知识库 | GET /api/knowledge | ✅ |
| P1 | AI供应商管理 | GET/POST /api/ai/providers | ✅ |
| P2 | 推荐引擎 | POST /api/recommend | ✅ |
| P2 | 数据看板 | GET /api/dashboard/overview | ✅ |

## v1.1.0 新功能

### AI 供应商管理（参考 CC Switch）

- 多供应商支持：OpenAI、DeepSeek、通义千问、自定义端点
- 4层模型映射：primary / light / balanced / strongest
- 一键切换、连接测试、配置持久化
- 配置存储：`data/.ccae/config.json`

### 数据可视化增强

- 趋势折线图：近7天翻译/审核/视觉识别量
- 模块使用占比饼图

## 文档

- [API文档](docs/API.md)
- [操作手册](docs/MANUAL.md)
- [部署说明](docs/DEPLOY.md)

## 配置文件

- `.env` — 环境变量（API密钥等）
- `data/.ccae/config.json` — AI供应商配置

## 更新日志

### v1.1.0 (2026-05-25)
- AI供应商管理（参考CC Switch设计）
- 4层模型映射
- 看板趋势图表和占比饼图
- Windows终端乱码修复
- 前端搜索防抖优化

### v1.0.0 (2026-05-21)
- 智能翻译模块
- 合规审核模块
- 视觉识别模块
- 知识库模块
- 推荐引擎
- 数据看板