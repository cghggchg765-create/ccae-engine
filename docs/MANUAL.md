# CCAE 跨文化适配引擎 操作手册

## 系统概述

CCAE（Cross-Cultural Adaptation Engine，跨文化适配引擎）为汉服 TikTok 全球运营提供：

1. **智能翻译** — 5000+汉服专业术语库，中→英/日/韩/西/法/阿，自动附加文化注释
2. **合规审核** — 150+国家文化禁忌规则库，文本/图片双渠道审核
3. **视觉识别** — 识别汉服朝代/形制/色彩/纹样
4. **审美匹配** — 六大区域审美偏好库
5. **知识库** — 形制/纹样/工艺/礼仪多语知识库
6. **文案生成** — 适配区域文化的短视频文案
7. **个性化推荐** — 基于用户画像+视觉标签的内容推荐
8. **数据看板** — 全模块运营数据 + 可视化图表
9. **AI供应商管理** — 多供应商统一管理，一键切换

---

## 快速启动

### 环境要求

- Python 3.9+
- pip

### 安装

```bash
# 1. 安装依赖
cd ccae-engine
pip install -r requirements.txt

# 2. 初始化数据库
python backend/database.py

# 3. 启动服务
python run.py
```

服务默认运行在 `http://127.0.0.1:5000`

### 管理后台

- 地址: `http://127.0.0.1:5000/`
- 默认账号: `admin` / `admin123`

---

## 模块操作指南

### 1. 智能翻译模块

**测试翻译**：
1. 在左侧导航点击「🌐 智能翻译」
2. 在文本框中输入中文汉服文案
3. 选择目标语种
4. 点击「翻译」按钮
5. 查看翻译结果、匹配术语、文化注释

**管理语料库**：
- 搜索：输入关键词或选择分类筛选项
- 添加术语：点击「+ 添加术语」，填写中文、分类、各语种译文、文化注释
- 编辑/删除：点击表格中的「编辑」「删除」按钮

### 2. 合规审核模块

**文本审核**：
1. 点击「🛡️ 合规审核」
2. 输入待审核文案
3. 选择目标国家
4. 点击「审核」
5. 查看风险等级、匹配规则、风险原因、修改建议

**管理规则库**：
- 添加规则：点击「+ 添加规则」，填写国家、类别、敏感词（逗号分隔）、风险等级、原因、建议
- 删除规则：点击表格中的「删除」按钮

### 3. 视觉识别模块

- 输入图片路径，点击「识别」获取朝代、形制、色彩、纹样信息
- 「🎨 区域审美库」可管理各区域色彩/纹样/风格偏好

### 4. 知识库模块

- 「📖 知识检索」：搜索知识库条目
- 「✍️ 文案生成」：输入主题+目标区域，生成适配短视频文案

### 5. 数据看板

首页展示：
- 关键指标：语料库数、规则数、30天翻译量、准确率、审核通过率等
- **趋势图表**：近7天翻译/审核/视觉识别量折线图
- **模块占比**：各API使用占比饼图

### 6. AI 供应商管理（v1.1.0 新增）

点击「⚙️ 系统设置」，进入 AI 供应商配置：

**供应商列表**（左侧）：
- 显示已配置的供应商（OpenAI、DeepSeek、通义千问等）
- 绿色标记当前激活的供应商
- 点击「+ 添加供应商」新增

**配置详情**（右侧）：
- **API 端点**：供应商 API 地址
- **API 密钥**：输入密钥（显示为 ****）
- **4层模型映射**：
  - Primary（主模型）：日常使用
  - Light（轻量模型）：快速响应
  - Balanced（均衡模型）：质量优先
  - Strongest（最强模型）：复杂推理

**操作按钮**：
- 「保存」：保存配置到本地文件
- 「测试连接」：验证 API 是否可用
- 「设为当前」：激活该供应商
- 「删除」：删除供应商

### 7. 系统设置

- 用户管理：添加/删除操作员、审核员、只读用户

---

## API调用示例

### Python

```python
import requests

# 翻译
r = requests.post("http://127.0.0.1:5000/api/translate", json={
    "text": "她穿着马面裙和云肩。",
    "target_lang": "en"
})
print(r.json())

# 合规审核
r = requests.post("http://127.0.0.1:5000/api/compliance/audit/text", json={
    "text": "这款汉服使用猪皮材质。",
    "country": "沙特阿拉伯"
})
print(r.json())

# AI 供应商管理
r = requests.get("http://127.0.0.1:5000/api/ai/providers")
print(r.json())
```

### JavaScript

```javascript
// 翻译
fetch("/api/translate", {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({text: "马面裙", target_lang: "en"})
}).then(r => r.json()).then(console.log)

// AI 供应商列表
fetch("/api/ai/providers").then(r => r.json()).then(console.log)
```

---

## 数据管理

### 批量导入

支持通过API批量导入或直接操作SQLite数据库：

```bash
# 查看数据
sqlite3 data/ccae.db "SELECT * FROM corpus LIMIT 10;"
```

### 数据导出

可通过Dashboard API获取JSON数据导出：

```bash
curl http://127.0.0.1:5000/api/dashboard/overview
```

---

## 项目结构

```
ccae-engine/
├── backend/
│   ├── app.py                # 主应用入口
│   ├── config.py             # 配置文件
│   ├── database.py           # 数据库模型+初始化
│   ├── api/                  # API路由层
│   │   ├── translate.py      # 翻译API
│   │   ├── compliance.py     # 合规API
│   │   ├── vision.py         # 视觉API
│   │   ├── knowledge.py      # 知识库API
│   │   ├── dashboard.py      # 看板+权限API
│   │   └── ai_providers.py  # AI供应商管理API
│   └── services/             # 业务逻辑层
│       ├── translator.py     # 翻译引擎
│       ├── compliance_checker.py  # 合规引擎
│       ├── vision_analyzer.py     # 视觉识别
│       ├── provider_config.py     # AI供应商配置
│       └── recommender.py    # 推荐+知识库
├── frontend/                 # Web管理后台
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js            # 主应用逻辑
│       └── charts.js         # 图表封装
├── data/
│   ├── ccae.db               # SQLite数据库
│   └── .ccae/
│       └── config.json       # AI供应商配置
└── docs/
    ├── API.md                # API文档
    ├── MANUAL.md             # 操作手册（本文件）
    └── DEPLOY.md             # 部署说明
```

---

## 配置文件说明

### .env 环境变量

```bash
CCAE_SECRET_KEY=your-secret-key
AI_PROVIDER=openai          # 当前AI供应商（可选）
AI_API_KEY=sk-xxxx         # API密钥（可选）
AI_BASE_URL=https://...    # API端点（可选）
AI_MODEL=gpt-4o-mini        # 模型名称（可选）
```

### data/.ccae/config.json

AI供应商配置存储，包含：
- 供应商列表（id, name, provider_type）
- 端点配置（base_url, api_key, model_mapping）
- 激活状态（is_active）