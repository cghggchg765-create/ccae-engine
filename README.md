# CCAE 跨文化适配引擎

<p align="center">
  <strong>Cross-Cultural Adaptation Engine</strong><br>
  <em>为「华裳出海 — 汉服TikTok全球运营」打造的核心引擎</em>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#api文档">API文档</a> •
  <a href="#更新日志">更新日志</a>
</p>

---

## 项目简介

CCAE 解决汉服出海的三大核心痛点：

| 痛点 | 解决方案 | 效果 |
|------|----------|------|
| 🌐 **翻译不准** | 5000+ 汉服专业术语库 + 自动文化注释 | 准确传达文化内涵 |
| 🛡️ **文化踩雷** | 150+ 国家禁忌规则库 + 文本/图片双审核 | 规避文化风险 |
| 🎯 **推送不精准** | 区域审美匹配 + 个性化推荐 | 提升内容转化率 |

---

## 功能特性

### 核心模块

| 模块 | 功能 | 优先级 |
|------|------|--------|
| **智能翻译** | 汉服专业术语翻译，自动附加文化注释 | P0 |
| **合规审核** | 文本/图片文化禁忌审核，覆盖150+国家 | P0 |
| **视觉识别** | 识别汉服朝代、形制、色彩、纹样 | P1 |
| **知识库** | 形制/纹样/工艺/礼仪多语知识库 | P1 |
| **AI供应商管理** | 多供应商统一管理，一键切换 | P1 |
| **推荐引擎** | 基于用户画像的个性化推荐 | P2 |
| **数据看板** | 全模块运营数据 + 可视化图表 | P2 |

### v1.1.0 新特性

#### 🤖 AI 供应商管理

参考 [CC Switch](https://github.com/2187262974-cmd/cc-switch) 设计理念：

```
┌─────────────────────────────────────────────────────┐
│  AI 供应商配置                                      │
├──────────────┬──────────────────────────────────────┤
│ 供应商列表   │  配置详情                            │
│              │                                      │
│ ┌──────────┐ │  API 端点: https://api.openai.com/v1 │
│ │ OpenAI   │ │  API 密钥: sk-****xxxx               │
│ │ 1 个端点  │ │                                      │
│ └──────────┘ │  4层模型映射:                        │
│              │  ┌─────────────┬──────────────────┐  │
│ ┌──────────┐ │  │ Primary    │ gpt-4o-mini      │  │
│ │ DeepSeek │ │  │ Light      │ gpt-3.5-turbo    │  │
│ │ 1 个端点  │ │  │ Balanced   │ gpt-4o           │  │
│ └──────────┘ │  │ Strongest  │ gpt-4o           │  │
│              │  └─────────────┴──────────────────┘  │
│ [+ 添加]     │  [保存] [测试] [激活] [删除]        │
└──────────────┴──────────────────────────────────────┘
```

**支持供应商**：
- **OpenAI** — GPT-4o 系列
- **DeepSeek** — 深度求索
- **通义千问** — 阿里云
- **自定义** — 任意 OpenAI 兼容端点

**4层模型映射**：

| 层级 | 用途 | OpenAI | DeepSeek | 通义千问 |
|------|------|--------|----------|----------|
| Primary | 日常使用 | gpt-4o-mini | deepseek-chat | qwen-turbo |
| Light | 快速响应 | gpt-3.5-turbo | deepseek-chat | qwen-turbo |
| Balanced | 质量优先 | gpt-4o | deepseek-chat | qwen-plus |
| Strongest | 复杂推理 | gpt-4o | deepseek-reasoner | qwen-max |

#### 📊 数据可视化

- **趋势折线图**：近7天翻译量、审核量、视觉识别量
- **模块占比饼图**：各 API 调用占比

---

## 快速开始

### 环境要求

- Python 3.9+
- 现代浏览器（支持 ES6）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/2187262974-cmd/ccae-engine.git
cd ccae-engine

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate   # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python backend/database.py

# 5. 启动服务
python run.py
```

### 访问

- **管理后台**: http://127.0.0.1:5000/
- **API 文档**: http://127.0.0.1:5000/api
- **默认账号**: admin / admin123

---

## 使用指南

### 1. 智能翻译

```
输入: "她穿着马面裙和云肩，上面绣着精美的云纹。"
目标: 英语

输出:
  翻译: "She wears Mamian Qun (Horse-Face Skirt) and Cloud Collar..."
  匹配术语:
    - 马面裙 → Mamian Qun (Horse-Face Skirt)
      文化注释: 最具辨识度的汉服单品，非'马面'之意...
    - 云肩 → Cloud Collar (Yunjian)
      文化注释: 云肩象征吉祥如意，唐代已有雏形...
```

### 2. 合规审核

```
输入: "这款汉服使用猪皮材质，搭配酒类主题纹样。"
目标国家: 沙特阿拉伯

输出:
  风险等级: 高风险
  匹配规则: 宗教禁忌
  原因: 含宗教禁忌元素，可能引发穆斯林消费者强烈反感
  建议: 移除与伊斯兰教义冲突的元素，替换为几何纹样或植物纹样
```

### 3. AI 供应商配置

1. 进入「⚙️ 系统设置」
2. 点击左侧供应商或「+ 添加供应商」
3. 填写 API 端点和密钥
4. 配置 4 层模型映射
5. 点击「测试连接」验证
6. 点击「设为当前」激活

---

## API 文档

### Base URL

```
http://127.0.0.1:5000
```

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/translate` | POST | 智能翻译 |
| `/api/compliance/audit/text` | POST | 文本合规审核 |
| `/api/compliance/audit/image` | POST | 图片合规审核 |
| `/api/vision/analyze` | POST | 视觉识别 |
| `/api/ai/providers` | GET/POST | 供应商管理 |
| `/api/ai/providers/:id/activate` | POST | 激活供应商 |
| `/api/dashboard/overview` | GET | 数据总览 |

### 示例

**翻译**:
```bash
curl -X POST http://127.0.0.1:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "马面裙", "target_lang": "en"}'
```

**合规审核**:
```bash
curl -X POST http://127.0.0.1:5000/api/compliance/audit/text \
  -H "Content-Type: application/json" \
  -d '{"text": "猪皮材质", "country": "沙特阿拉伯"}'
```

**AI 供应商列表**:
```bash
curl http://127.0.0.1:5000/api/ai/providers
```

---

## 项目结构

```
ccae-engine/
├── backend/                    # 后端服务
│   ├── app.py                  # Flask 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库模型
│   ├── api/                    # API 路由
│   │   ├── translate.py        # 翻译 API
│   │   ├── compliance.py       # 合规 API
│   │   ├── vision.py           # 视觉 API
│   │   ├── knowledge.py        # 知识库 API
│   │   ├── dashboard.py        # 看板 API
│   │   └── ai_providers.py    # AI 供应商 API
│   └── services/               # 业务逻辑
│       ├── translator.py       # 翻译引擎
│       ├── compliance_checker.py
│       ├── vision_analyzer.py
│       ├── provider_config.py  # AI 供应商配置
│       └── recommender.py
├── frontend/                   # 前端界面
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js              # 主应用逻辑
│       └── charts.js           # 图表封装
├── data/                       # 数据存储
│   ├── ccae.db                 # SQLite 数据库
│   └── .ccae/
│       └── config.json         # AI 供应商配置
├── docs/                       # 文档
│   ├── API.md
│   ├── MANUAL.md
│   └── DEPLOY.md
├── requirements.txt
└── run.py                      # 启动入口
```

---

## 配置说明

### 环境变量 (.env)

```bash
# 安全配置
CCAE_SECRET_KEY=your-secret-key

# AI 配置（可选，通过管理界面配置更方便）
AI_PROVIDER=openai
AI_API_KEY=sk-xxxxxxxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini

# 功能开关
DEBUG=false
CORS_ENABLED=true
```

### AI 供应商配置 (data/.ccae/config.json)

通过管理界面自动生成，包含：
- 供应商列表和端点配置
- 4 层模型映射
- 激活状态

---

## 技术栈

| 类型 | 技术 |
|------|------|
| 后端框架 | Python Flask |
| 数据库 | SQLite |
| 前端 | 原生 HTML/CSS/JavaScript |
| 图表 | Chart.js |
| UI 风格 | 国风 + 科技蓝暗色主题 |

---

## 更新日志

### v1.1.0 (2026-05-25)

**新增功能**:
- AI 供应商管理（参考 CC Switch 设计）
- 4 层模型映射（primary/light/balanced/strongest）
- 看板趋势折线图和占比饼图

**Bug 修复**:
- 修复 Windows 终端中文输出乱码
- 添加 python-dotenv 自动加载 .env

**性能优化**:
- 前端搜索输入防抖（300ms）

### v1.0.0 (2026-05-21)

- 智能翻译模块
- 合规审核模块
- 视觉识别模块
- 知识库模块
- 推荐引擎
- 数据看板

---

## 贡献

欢迎提交 Issue 和 Pull Request。

---

## 许可证

MIT License

---

<p align="center">
  <sub>为汉服出海贡献力量 🌸</sub>
</p>
