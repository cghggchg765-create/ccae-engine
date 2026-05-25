# CCAE 全面改进实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 AI 配置体验、增强数据可视化、完善系统功能、修复已知问题

**Architecture:** 采用左侧列表 + 右侧详情布局管理 AI 供应商，引入 Chart.js 实现数据可视化，保持现有 Flask + SQLite 架构不变

**Tech Stack:** Python Flask, SQLite, 原生 JavaScript, Chart.js (新增)

---

## 文件结构

### 新建文件
```
backend/
  api/
    ai_providers.py          # AI供应商管理API（新建）
  services/
    provider_config.py       # 供应商配置数据模型（新建）

frontend/
  js/
    charts.js                # Chart.js 图表封装（新建）
  lib/
    chart.min.js             # Chart.js 库文件（新建）

data/
  .ccae/
    config.json              # AI供应商配置存储（新建）
```

### 修改文件
```
backend/
  database.py                # 添加 ai_providers 表
  app.py                     # 注册新蓝图
  api/dashboard.py           # 增强看板API

frontend/
  js/app.js                  # 重构设置页面、添加图表
  index.html                 # 引入 Chart.js
  css/style.css              # 新增样式
```

---

## Phase 1: AI 配置重构

### Task 1: 创建供应商配置数据模型

**Files:**
- Create: `backend/services/provider_config.py`

- [ ] **Step 1: 创建供应商配置模块**

```python
"""AI供应商配置管理

参考 CC Switch 设计理念：
- 多供应商管理
- 多端点支持
- 4层模型映射
"""

import os
import json
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ModelMapping:
    """4层模型映射"""
    primary: str = ""       # 主模型（日常使用）
    light: str = ""         # 轻量模型（快速响应）
    balanced: str = ""      # 均衡模型（质量优先）
    strongest: str = ""     # 最强模型（复杂推理）


@dataclass
class Endpoint:
    """API端点配置"""
    id: str
    name: str                    # 显示名称
    base_url: str                # API端点地址
    api_key: str                 # API密钥
    model_mapping: ModelMapping  # 模型映射
    is_default: bool = False     # 是否默认端点
    status: str = "unknown"      # online/offline/unknown

    def to_dict(self):
        d = asdict(self)
        d['model_mapping'] = asdict(self.model_mapping)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        mapping = ModelMapping(**d.get('model_mapping', {}))
        return cls(
            id=d['id'],
            name=d['name'],
            base_url=d['base_url'],
            api_key=d['api_key'],
            model_mapping=mapping,
            is_default=d.get('is_default', False),
            status=d.get('status', 'unknown')
        )


@dataclass
class ProviderConfig:
    """AI供应商配置"""
    id: str
    name: str                        # 显示名称
    provider_type: str               # openai/deepseek/qwen/custom
    endpoints: List[Endpoint]        # 端点列表
    is_active: bool = False          # 是否当前使用
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self):
        d = asdict(self)
        d['endpoints'] = [e.to_dict() for e in self.endpoints]
        d.pop('created_at', None)
        d.pop('updated_at', None)
        return d

    @classmethod
    def from_dict(cls, d: dict):
        endpoints = [Endpoint.from_dict(e) for e in d.get('endpoints', [])]
        return cls(
            id=d['id'],
            name=d['name'],
            provider_type=d['provider_type'],
            endpoints=endpoints,
            is_active=d.get('is_active', False),
            created_at=d.get('created_at', ''),
            updated_at=d.get('updated_at', '')
        )


# 预设供应商配置
PRESET_PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "provider_type": "openai",
        "endpoints": [{
            "id": "default",
            "name": "官方API",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model_mapping": {
                "primary": "gpt-4o-mini",
                "light": "gpt-3.5-turbo",
                "balanced": "gpt-4o",
                "strongest": "gpt-4o"
            },
            "is_default": True
        }]
    },
    "deepseek": {
        "name": "DeepSeek",
        "provider_type": "deepseek",
        "endpoints": [{
            "id": "default",
            "name": "官方API",
            "base_url": "https://api.deepseek.com/v1",
            "api_key": "",
            "model_mapping": {
                "primary": "deepseek-chat",
                "light": "deepseek-chat",
                "balanced": "deepseek-chat",
                "strongest": "deepseek-reasoner"
            },
            "is_default": True
        }]
    },
    "qwen": {
        "name": "通义千问",
        "provider_type": "qwen",
        "endpoints": [{
            "id": "default",
            "name": "官方API",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": "",
            "model_mapping": {
                "primary": "qwen-turbo",
                "light": "qwen-turbo",
                "balanced": "qwen-plus",
                "strongest": "qwen-max"
            },
            "is_default": True
        }]
    }
}


class ProviderManager:
    """供应商配置管理器"""

    CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", ".ccae")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    def __init__(self):
        self._providers: Dict[str, ProviderConfig] = {}
        self._load()

    def _load(self):
        """从文件加载配置"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pid, pdata in data.get('providers', {}).items():
                        self._providers[pid] = ProviderConfig.from_dict(pdata)
            except Exception:
                pass

    def _save(self):
        """保存配置到文件"""
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        data = {
            'providers': {pid: p.to_dict() for pid, p in self._providers.items()},
            'updated_at': datetime.now().isoformat()
        }
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_providers(self) -> List[Dict]:
        """获取所有供应商"""
        return [p.to_dict() for p in self._providers.values()]

    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """获取单个供应商"""
        if provider_id in self._providers:
            return self._providers[provider_id].to_dict()
        return None

    def add_provider(self, provider_type: str, name: str = None) -> Dict:
        """添加供应商"""
        pid = str(uuid.uuid4())[:8]
        preset = PRESET_PROVIDERS.get(provider_type, {})

        provider = ProviderConfig(
            id=pid,
            name=name or preset.get('name', provider_type),
            provider_type=provider_type,
            endpoints=[Endpoint.from_dict(e) for e in preset.get('endpoints', [])],
            is_active=False
        )

        self._providers[pid] = provider
        self._save()
        return provider.to_dict()

    def update_provider(self, provider_id: str, **kwargs) -> Optional[Dict]:
        """更新供应商配置"""
        if provider_id not in self._providers:
            return None

        provider = self._providers[provider_id]

        if 'name' in kwargs:
            provider.name = kwargs['name']
        if 'endpoints' in kwargs:
            provider.endpoints = [Endpoint.from_dict(e) for e in kwargs['endpoints']]

        self._save()
        return provider.to_dict()

    def delete_provider(self, provider_id: str) -> bool:
        """删除供应商"""
        if provider_id in self._providers:
            del self._providers[provider_id]
            self._save()
            return True
        return False

    def activate_provider(self, provider_id: str) -> Optional[Dict]:
        """激活供应商"""
        # 取消其他供应商的激活状态
        for p in self._providers.values():
            p.is_active = False

        if provider_id in self._providers:
            self._providers[provider_id].is_active = True
            self._save()
            return self._providers[provider_id].to_dict()
        return None

    def get_active_provider(self) -> Optional[Dict]:
        """获取当前激活的供应商"""
        for p in self._providers.values():
            if p.is_active:
                return p.to_dict()
        return None

    def test_connection(self, provider_id: str, endpoint_id: str = None) -> Dict:
        """测试连接"""
        if provider_id not in self._providers:
            return {"success": False, "message": "供应商不存在"}

        provider = self._providers[provider_id]
        endpoint = None

        for e in provider.endpoints:
            if endpoint_id and e.id == endpoint_id:
                endpoint = e
                break
            elif e.is_default:
                endpoint = e

        if not endpoint:
            endpoint = provider.endpoints[0] if provider.endpoints else None

        if not endpoint or not endpoint.api_key:
            return {"success": False, "message": "未配置API密钥"}

        # 实际测试连接
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {endpoint.api_key}",
                "Content-Type": "application/json"
            }
            # 发送简单的测试请求
            response = requests.post(
                f"{endpoint.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": endpoint.model_mapping.primary,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 5
                },
                timeout=10
            )
            if response.status_code == 200:
                return {"success": True, "message": "连接成功"}
            else:
                return {"success": False, "message": f"API错误: {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "连接超时"}
        except Exception as e:
            return {"success": False, "message": f"连接失败: {str(e)}"}


# 单例
_manager = None

def get_provider_manager() -> ProviderManager:
    global _manager
    if _manager is None:
        _manager = ProviderManager()
    return _manager
```

- [ ] **Step 2: 创建配置目录**

```bash
mkdir -p data/.ccae
```

- [ ] **Step 3: 提交**

```bash
git add backend/services/provider_config.py
git commit -m "feat: 添加AI供应商配置数据模型

- 支持 OpenAI/DeepSeek/通义千问 预设配置
- 4层模型映射 (primary/light/balanced/strongest)
- 多端点支持
- JSON文件持久化

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: 创建供应商管理API

**Files:**
- Create: `backend/api/ai_providers.py`
- Modify: `backend/app.py`

- [ ] **Step 1: 创建API蓝图**

```python
"""AI供应商管理API"""

from flask import Blueprint, request, jsonify
from services.provider_config import get_provider_manager

providers_bp = Blueprint("providers", __name__)


@providers_bp.route("/api/ai/providers", methods=["GET"])
def list_providers():
    """获取所有供应商配置"""
    manager = get_provider_manager()
    providers = manager.list_providers()
    return jsonify(providers)


@providers_bp.route("/api/ai/providers", methods=["POST"])
def add_provider():
    """添加供应商"""
    data = request.json
    provider_type = data.get("provider_type", "custom")
    name = data.get("name")

    if not provider_type:
        return jsonify({"error": "缺少 provider_type"}), 400

    manager = get_provider_manager()
    provider = manager.add_provider(provider_type, name)
    return jsonify(provider), 201


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["GET"])
def get_provider(provider_id):
    """获取单个供应商配置"""
    manager = get_provider_manager()
    provider = manager.get_provider(provider_id)
    if provider:
        return jsonify(provider)
    return jsonify({"error": "供应商不存在"}), 404


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["PUT"])
def update_provider(provider_id):
    """更新供应商配置"""
    data = request.json
    manager = get_provider_manager()
    provider = manager.update_provider(provider_id, **data)
    if provider:
        return jsonify(provider)
    return jsonify({"error": "供应商不存在"}), 404


@providers_bp.route("/api/ai/providers/<provider_id>", methods=["DELETE"])
def delete_provider(provider_id):
    """删除供应商"""
    manager = get_provider_manager()
    if manager.delete_provider(provider_id):
        return jsonify({"message": "已删除"})
    return jsonify({"error": "供应商不存在"}), 404


@providers_bp.route("/api/ai/providers/<provider_id>/activate", methods=["POST"])
def activate_provider(provider_id):
    """激活供应商"""
    manager = get_provider_manager()
    provider = manager.activate_provider(provider_id)
    if provider:
        return jsonify(provider)
    return jsonify({"error": "供应商不存在"}), 404


@providers_bp.route("/api/ai/providers/<provider_id>/test", methods=["POST"])
def test_provider(provider_id):
    """测试供应商连接"""
    data = request.json or {}
    endpoint_id = data.get("endpoint_id")
    manager = get_provider_manager()
    result = manager.test_connection(provider_id, endpoint_id)
    return jsonify(result)


@providers_bp.route("/api/ai/current", methods=["GET"])
def get_current_provider():
    """获取当前激活的供应商"""
    manager = get_provider_manager()
    provider = manager.get_active_provider()
    if provider:
        return jsonify(provider)
    return jsonify({"active": False, "message": "未激活任何供应商"})
```

- [ ] **Step 2: 注册蓝图到 app.py**

在 `backend/app.py` 中添加：

```python
from api.ai_providers import providers_bp
app.register_blueprint(providers_bp)
```

找到现有的 `app.register_blueprint` 行，在其后添加上述导入和注册。

- [ ] **Step 3: 提交**

```bash
git add backend/api/ai_providers.py backend/app.py
git commit -m "feat: 添加AI供应商管理API

- GET/POST /api/ai/providers
- PUT/DELETE /api/ai/providers/:id
- POST /api/ai/providers/:id/activate
- POST /api/ai/providers/:id/test
- GET /api/ai/current

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: 下载并引入 Chart.js

**Files:**
- Create: `frontend/lib/chart.min.js`
- Modify: `frontend/index.html`

- [ ] **Step 1: 下载 Chart.js**

```bash
cd F:/deskop/github/ccae-engine
mkdir -p frontend/lib
curl -L "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" -o frontend/lib/chart.min.js
```

如果 curl 失败，手动创建一个空文件并添加 Chart.js CDN 引用。

- [ ] **Step 2: 修改 index.html 引入 Chart.js**

在 `<head>` 部分添加：

```html
<script src="lib/chart.min.js"></script>
```

或在 body 结束前添加 CDN 引用：

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/lib/ frontend/index.html
git commit -m "feat: 引入 Chart.js 图表库

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: 创建图表封装模块

**Files:**
- Create: `frontend/js/charts.js`

- [ ] **Step 1: 创建图表模块**

```javascript
/* CCAE 图表封装模块 */

const Charts = {
  instances: {},

  // 颜色主题
  colors: {
    primary: '#3b82f6',
    success: '#22c55e',
    warning: '#eab308',
    danger: '#ef4444',
    muted: '#6b7280',
    palette: ['#3b82f6', '#22c55e', '#eab308', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']
  },

  // 销毁图表
  destroy(canvasId) {
    if (this.instances[canvasId]) {
      this.instances[canvasId].destroy();
      delete this.instances[canvasId];
    }
  },

  // 折线图 - 趋势
  line(canvasId, labels, datasets, options = {}) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    this.instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: datasets.map((ds, i) => ({
          label: ds.label,
          data: ds.data,
          borderColor: ds.color || this.colors.palette[i],
          backgroundColor: (ds.color || this.colors.palette[i]) + '20',
          fill: true,
          tension: 0.3
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: '#a0aec0' } }
        },
        scales: {
          x: { ticks: { color: '#718096' }, grid: { color: '#2d3748' } },
          y: { ticks: { color: '#718096' }, grid: { color: '#2d3748' } }
        },
        ...options
      }
    });
    return this.instances[canvasId];
  },

  // 饼图 - 占比
  pie(canvasId, labels, data, options = {}) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    this.instances[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: this.colors.palette.slice(0, data.length)
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { color: '#a0aec0' } }
        },
        ...options
      }
    });
    return this.instances[canvasId];
  },

  // 条形图 - 对比
  bar(canvasId, labels, datasets, options = {}) {
    this.destroy(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    this.instances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: datasets.map((ds, i) => ({
          label: ds.label,
          data: ds.data,
          backgroundColor: ds.color || this.colors.palette[i]
        }))
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { ticks: { color: '#718096' }, grid: { color: '#2d3748' } },
          y: { ticks: { color: '#718096' }, grid: { color: '#2d3748' } }
        },
        ...options
      }
    });
    return this.instances[canvasId];
  }
};
```

- [ ] **Step 2: 提交**

```bash
git add frontend/js/charts.js
git commit -m "feat: 添加图表封装模块

- line(): 折线图（趋势）
- pie(): 饼图（占比）
- bar(): 条形图（对比）
- 暗色主题适配

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: 重构设置页面 - AI配置

**Files:**
- Modify: `frontend/js/app.js`

- [ ] **Step 1: 替换 renderSettings 函数**

找到 `renderSettings` 函数（约第819行），替换为：

```javascript
// === 7. 设置 ===
function renderSettings() {
  return `<h2 style="color:var(--accent);margin-bottom:20px">⚙️ 系统设置</h2>

    <div class="panel">
      <h2>🤖 AI供应商配置</h2>
      <p style="color:var(--text-muted);margin-bottom:16px;font-size:14px">
        管理多个AI供应商，支持一键切换。参考 CC Switch 设计理念。
      </p>

      <div style="display:flex;gap:16px;min-height:400px">
        <!-- 左侧供应商列表 -->
        <div style="width:200px;border-right:1px solid var(--border);padding-right:16px">
          <div id="provider-list"></div>
          <div style="margin-top:12px">
            <select id="new-provider-type" style="width:100%;margin-bottom:8px">
              <option value="openai">OpenAI</option>
              <option value="deepseek">DeepSeek</option>
              <option value="qwen">通义千问</option>
              <option value="custom">自定义</option>
            </select>
            <button class="btn btn-primary" style="width:100%" onclick="addProvider()">+ 添加供应商</button>
          </div>
        </div>

        <!-- 右侧配置详情 -->
        <div style="flex:1" id="provider-detail">
          <p style="color:var(--text-muted);text-align:center;padding:40px">选择或添加供应商</p>
        </div>
      </div>
    </div>

    <div class="panel"><h2>👥 用户管理</h2>
      <div id="user-list"></div>
      <div class="form-row" style="margin-top:12px">
        <input id="new-user" placeholder="用户名">
        <input id="new-pw" type="password" placeholder="密码">
        <select id="new-role"><option>operator</option><option>auditor</option><option>readonly</option></select>
        <button class="btn btn-primary btn-sm" onclick="addUser()">添加用户</button>
      </div>
    </div>

    <div class="panel"><h2>ℹ️ 系统信息</h2>
      <p>版本：1.1.0 | Python Flask + SQLite | 配置文件：data/.ccae/config.json</p>
    </div>`;
}
```

- [ ] **Step 2: 添加供应商管理函数**

在 `renderSettings` 函数后添加：

```javascript
// === AI供应商管理 ===
let currentProviderId = null;

async function loadProviders() {
  try {
    const providers = await safeFetch(API + "/ai/providers");
    const listEl = document.getElementById("provider-list");

    if (!providers.length) {
      listEl.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px">暂无供应商</p>';
      return;
    }

    listEl.innerHTML = providers.map(p => `
      <div class="provider-item ${p.is_active ? 'active' : ''} ${currentProviderId === p.id ? 'selected' : ''}"
           onclick="selectProvider('${p.id}')"
           style="padding:12px;margin-bottom:8px;background:${p.is_active ? 'var(--accent)' : 'var(--bg-secondary)'};
                  border-radius:6px;cursor:pointer;color:${p.is_active ? 'white' : 'var(--text)'}">
        <div style="font-weight:600">${escapeHtml(p.name)}</div>
        <div style="font-size:12px;opacity:0.7">${p.endpoints?.length || 0} 个端点</div>
        ${p.is_active ? '<span style="font-size:10px;background:rgba(255,255,255,0.2);padding:2px 6px;border-radius:4px">当前</span>' : ''}
      </div>
    `).join("");
  } catch(e) {
    toast("加载供应商失败: " + e.message, "error");
  }
}

async function addProvider() {
  const type = document.getElementById("new-provider-type").value;
  try {
    await safeFetch(API + "/ai/providers", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({provider_type: type})
    });
    loadProviders();
    toast("供应商添加成功", "success");
  } catch(e) {
    toast("添加失败: " + e.message, "error");
  }
}

async function selectProvider(providerId) {
  currentProviderId = providerId;
  loadProviders(); // 更新选中状态

  try {
    const provider = await safeFetch(API + "/ai/providers/" + providerId);
    renderProviderDetail(provider);
  } catch(e) {
    toast("加载详情失败: " + e.message, "error");
  }
}

function renderProviderDetail(provider) {
  const el = document.getElementById("provider-detail");
  const endpoint = provider.endpoints?.[0] || {};
  const mapping = endpoint.model_mapping || {};

  el.innerHTML = `
    <h3 style="margin-bottom:16px">${escapeHtml(provider.name)}</h3>

    <div class="form-row">
      <label style="min-width:100px">API端点</label>
      <input id="ep-url" value="${escapeHtml(endpoint.base_url || '')}" placeholder="https://api.openai.com/v1" style="flex:1">
    </div>

    <div class="form-row">
      <label style="min-width:100px">API密钥</label>
      <input id="ep-key" type="password" value="${escapeHtml(endpoint.api_key || '')}" placeholder="sk-xxxxxxxx" style="flex:1">
    </div>

    <h4 style="margin:16px 0 12px">4层模型映射</h4>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div>
        <label style="font-size:12px;color:var(--text-muted)">主模型 (Primary)</label>
        <input id="model-primary" value="${escapeHtml(mapping.primary || '')}" placeholder="gpt-4o-mini">
      </div>
      <div>
        <label style="font-size:12px;color:var(--text-muted)">轻量模型 (Light)</label>
        <input id="model-light" value="${escapeHtml(mapping.light || '')}" placeholder="gpt-3.5-turbo">
      </div>
      <div>
        <label style="font-size:12px;color:var(--text-muted)">均衡模型 (Balanced)</label>
        <input id="model-balanced" value="${escapeHtml(mapping.balanced || '')}" placeholder="gpt-4o">
      </div>
      <div>
        <label style="font-size:12px;color:var(--text-muted)">最强模型 (Strongest)</label>
        <input id="model-strongest" value="${escapeHtml(mapping.strongest || '')}" placeholder="gpt-4o">
      </div>
    </div>

    <div class="form-row" style="margin-top:16px">
      <button class="btn btn-success" onclick="saveProvider('${provider.id}')">💾 保存</button>
      <button class="btn btn-outline" onclick="testProvider('${provider.id}')">🔗 测试连接</button>
      <button class="btn btn-primary" onclick="activateProvider('${provider.id}')" ${provider.is_active ? 'disabled' : ''}>
        ${provider.is_active ? '✓ 当前使用' : '设为当前'}
      </button>
      <button class="btn btn-danger" onclick="deleteProvider('${provider.id}')">删除</button>
    </div>
    <div id="provider-status" style="margin-top:8px"></div>
  `;
}

async function saveProvider(providerId) {
  const data = {
    endpoints: [{
      id: "default",
      name: "默认端点",
      base_url: document.getElementById("ep-url").value,
      api_key: document.getElementById("ep-key").value,
      model_mapping: {
        primary: document.getElementById("model-primary").value,
        light: document.getElementById("model-light").value,
        balanced: document.getElementById("model-balanced").value,
        strongest: document.getElementById("model-strongest").value
      },
      is_default: true
    }]
  };

  try {
    await safeFetch(API + "/ai/providers/" + providerId, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
    toast("配置已保存", "success");
  } catch(e) {
    toast("保存失败: " + e.message, "error");
  }
}

async function testProvider(providerId) {
  const status = document.getElementById("provider-status");
  status.innerHTML = '<span style="color:var(--text-muted)">测试中...</span>';

  try {
    const result = await safeFetch(API + "/ai/providers/" + providerId + "/test", {method: "POST"});
    if (result.success) {
      status.innerHTML = '<span style="color:var(--success)">✓ ' + escapeHtml(result.message) + '</span>';
      toast("连接成功", "success");
    } else {
      status.innerHTML = '<span style="color:var(--danger)">✗ ' + escapeHtml(result.message) + '</span>';
    }
  } catch(e) {
    status.innerHTML = '<span style="color:var(--danger)">✗ 测试失败</span>';
  }
}

async function activateProvider(providerId) {
  try {
    await safeFetch(API + "/ai/providers/" + providerId + "/activate", {method: "POST"});
    toast("已切换到此供应商", "success");
    loadProviders();
    selectProvider(providerId);
  } catch(e) {
    toast("切换失败: " + e.message, "error");
  }
}

async function deleteProvider(providerId) {
  if (!confirm("确认删除此供应商？")) return;
  try {
    await safeFetch(API + "/ai/providers/" + providerId, {method: "DELETE"});
    currentProviderId = null;
    loadProviders();
    document.getElementById("provider-detail").innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">选择或添加供应商</p>';
    toast("已删除", "success");
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}
```

- [ ] **Step 3: 修改 loadPage 函数中的 settings 加载**

找到 `case "settings"` 行，修改为：

```javascript
case "settings": content.innerHTML = renderSettings(); await loadProviders(); await loadUsers(); break;
```

- [ ] **Step 4: 提交**

```bash
git add frontend/js/app.js
git commit -m "feat: 重构AI配置页面

- 左侧列表 + 右侧详情布局
- 供应商管理（添加/编辑/删除）
- 4层模型映射配置
- 连接测试
- 一键切换

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Phase 2: 数据可视化增强

### Task 6: 增强看板 - 添加趋势图表

**Files:**
- Modify: `frontend/js/app.js`

- [ ] **Step 1: 修改 renderDashboard 函数**

找到 `renderDashboard` 函数，在统计卡片后添加图表区域：

```javascript
async function renderDashboard() {
  let stats = {};
  try {
    stats = await safeFetch(API+"/dashboard/overview");
  } catch(e) {
    console.error("加载统计数据失败:", e);
  }

  return `
    <h2 style="color:var(--accent);margin-bottom:20px">📊 数据看板</h2>

    <div class="stats-grid">
      <div class="stat-card"><div class="label">语料库术语</div><div class="value">${escapeHtml(stats.corpus_count||0)}</div></div>
      <div class="stat-card"><div class="label">合规规则</div><div class="value">${escapeHtml(stats.rules_count||0)}</div></div>
      <div class="stat-card"><div class="label">30天翻译量</div><div class="value">${escapeHtml(stats.monthly_translations||0)}</div></div>
      <div class="stat-card"><div class="label">翻译准确率</div><div class="value success">${escapeHtml(((stats.avg_translation_confidence||0)*100).toFixed(0))}%</div></div>
      <div class="stat-card"><div class="label">审核通过率</div><div class="value success">${escapeHtml(((stats.pass_rate||0)*100).toFixed(0))}%</div></div>
      <div class="stat-card"><div class="label">高风险率</div><div class="value danger">${escapeHtml(((stats.high_risk_rate||0)*100).toFixed(0))}%</div></div>
    </div>

    <!-- 图表区域 -->
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-top:20px">
      <div class="panel">
        <h3>📈 近30天趋势</h3>
        <div style="height:250px"><canvas id="trend-chart"></canvas></div>
      </div>
      <div class="panel">
        <h3>🎯 模块使用占比</h3>
        <div style="height:250px"><canvas id="usage-chart"></canvas></div>
      </div>
    </div>

    <div class="panel"><h2>⚡ 模块状态</h2>
      <table><tr><th>模块</th><th>优先级</th><th>状态</th><th>API端点</th></tr>
        <tr><td>🌐 智能翻译</td><td>P0</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/translate</td></tr>
        <tr><td>🛡️ 合规审核</td><td>P0</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/compliance/audit/text</td></tr>
        <tr><td>👁️ 视觉识别</td><td>P1</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/vision/analyze</td></tr>
        <tr><td>📚 知识库</td><td>P1</td><td><span class="badge badge-pass">运行中</span></td><td>GET /api/knowledge</td></tr>
        <tr><td>🎯 推荐引擎</td><td>P2</td><td><span class="badge badge-review">开发中</span></td><td>POST /api/recommend</td></tr>
      </table>
    </div>`;
}
```

- [ ] **Step 2: 添加图表渲染函数**

在 renderDashboard 后添加：

```javascript
async function renderDashboardCharts() {
  try {
    // 获取趋势数据
    const daily = await safeFetch(API + "/dashboard/daily");

    // 渲染趋势图
    if (daily.translations && daily.translations.length > 0) {
      const labels = daily.translations.map(d => d.day.slice(5)); // MM-DD
      const transData = daily.translations.map(d => d.translations);
      const auditData = daily.audits.map(d => (d.passed || 0) + (d.high_risk || 0));

      Charts.line('trend-chart', labels, [
        { label: '翻译量', data: transData, color: '#3b82f6' },
        { label: '审核量', data: auditData, color: '#22c55e' }
      ]);
    }

    // 获取概览数据渲染饼图
    const stats = await safeFetch(API + "/dashboard/overview");
    Charts.pie('usage-chart',
      ['翻译', '审核', '视觉识别'],
      [stats.monthly_translations || 1, stats.monthly_audits || 1, stats.vision_analyses || 1]
    );
  } catch(e) {
    console.error("图表渲染失败:", e);
  }
}
```

- [ ] **Step 3: 修改 loadPage 中的 dashboard 加载**

```javascript
case "dashboard": content.innerHTML = await renderDashboard(); setTimeout(renderDashboardCharts, 100); break;
```

- [ ] **Step 4: 提交**

```bash
git add frontend/js/app.js
git commit -m "feat: 看板添加趋势图表和占比饼图

- 近30天翻译/审核趋势折线图
- 模块使用占比饼图
- 使用 Chart.js 渲染

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Phase 3: Bug修复与优化

### Task 7: 修复Windows终端中文输出乱码

**Files:**
- Modify: `run.py`
- Modify: `backend/database.py`

- [ ] **Step 1: 在 run.py 添加编码设置**

在 `run.py` 文件开头添加：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CCAE Cross-Cultural Adaptation Engine — Entry Point"""

import sys
import io

# 修复Windows终端中文输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

- [ ] **Step 2: 修复 database.py 中的中文输出**

找到 database.py 中的 print 语句，将中文改为英文或使用 ASCII 安全字符。

- [ ] **Step 3: 提交**

```bash
git add run.py backend/database.py
git commit -m "fix: 修复Windows终端中文输出乱码

- 强制使用UTF-8编码
- 替换特殊Unicode字符

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: 添加 python-dotenv 支持

**Files:**
- Modify: `requirements.txt`
- Modify: `run.py`

- [ ] **Step 1: 更新 requirements.txt**

添加：
```
python-dotenv>=1.0.0
```

- [ ] **Step 2: 在 run.py 加载 .env**

在 run.py 的 main 函数开头添加：

```python
def main():
    # 加载 .env 文件
    from dotenv import load_dotenv
    load_dotenv()

    args = parse_args()
    # ... 其余代码
```

- [ ] **Step 3: 提交**

```bash
git add requirements.txt run.py
git commit -m "fix: 添加python-dotenv支持自动加载.env

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: 添加前端防抖优化

**Files:**
- Modify: `frontend/js/app.js`

- [ ] **Step 1: 添加防抖函数**

在 app.js 开头的工具函数区域添加：

```javascript
/**
 * 防抖函数
 */
function debounce(func, wait = 300) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
```

- [ ] **Step 2: 应用到搜索输入**

找到 `loadCorpus` 调用处，将：
```javascript
oninput="loadCorpus()"
```
改为：
```javascript
oninput="debounce(loadCorpus, 300)()"
```

对其他搜索输入也做同样处理。

- [ ] **Step 3: 提交**

```bash
git add frontend/js/app.js
git commit -m "perf: 添加前端搜索防抖优化

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: 整体测试与提交

- [ ] **Step 1: 启动服务测试**

```bash
cd F:/deskop/github/ccae-engine
source venv/Scripts/activate
pip install -r requirements.txt
python run.py
```

- [ ] **Step 2: 验证功能**

- 访问 http://127.0.0.1:5000/
- 检查看板图表是否正常
- 进入设置页面测试 AI 供应商管理
- 测试添加、保存、测试连接、激活功能

- [ ] **Step 3: 最终提交**

```bash
git add -A
git commit -m "release: CCAE v1.1.0 - AI配置重构与可视化增强

主要更新：
- AI供应商管理（参考CC Switch设计）
- 4层模型映射（primary/light/balanced/strongest）
- 看板趋势图表和占比饼图
- Windows终端乱码修复
- 前端搜索防抖优化

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## 验收清单

- [ ] AI配置页面左侧列表正常显示
- [ ] 可添加/编辑/删除供应商
- [ ] 模型映射配置保存成功
- [ ] 连接测试功能正常
- [ ] 供应商切换后状态持久化
- [ ] 看板图表正常渲染
- [ ] Windows终端无乱码
- [ ] 搜索输入有防抖效果
