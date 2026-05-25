/* CCAE管理后台主逻辑 */

const API = "/api";
const LANGUAGES = {en:"英语", ja:"日语", ko:"韩语", es:"西班牙语", fr:"法语", ar:"阿拉伯语"};
const CATEGORIES = ["形制","纹样","工艺","礼仪","朝代"];
const REGIONS = ["北美","欧洲","日韩","东南亚","中东","拉美","全球"];
const TABOO_CATS = ["文化冒犯","宗教禁忌","政治敏感","文化挪用"];

// === 安全工具函数 ===

/**
 * 获取CSRF Token（从meta标签或cookie）
 * @returns {string} - CSRF Token或空字符串
 */
function getCsrfToken() {
  // 从meta标签获取
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  // 从cookie获取
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : "";
}

/**
 * 输入验证：检查文本长度和基本有效性
 * @param {string} text - 待验证文本
 * @param {number} minLen - 最小长度
 * @param {number} maxLen - 最大长度
 * @param {string} fieldName - 字段名称（用于错误提示）
 * @returns {object} - {valid: boolean, error: string|null}
 */
function validateInput(text, minLen = 1, maxLen = 5000, fieldName = "输入") {
  if (!text || typeof text !== "string") {
    return { valid: false, error: `${fieldName}不能为空` };
  }
  const trimmed = text.trim();
  if (trimmed.length < minLen) {
    return { valid: false, error: `${fieldName}长度不能少于${minLen}个字符` };
  }
  if (trimmed.length > maxLen) {
    return { valid: false, error: `${fieldName}长度不能超过${maxLen}个字符` };
  }
  return { valid: true, error: null, value: trimmed };
}

/**
 * 设置按钮加载状态
 * @param {HTMLElement|string} btnOrId - 按钮元素或ID
 * @param {boolean} loading - 是否处于加载状态
 * @param {string} loadingText - 加载时显示的文字
 */
function setButtonLoading(btnOrId, loading, loadingText = "处理中...") {
  const btn = typeof btnOrId === "string" ? document.getElementById(btnOrId) : btnOrId;
  if (!btn) return;
  if (loading) {
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = loadingText;
    btn.classList.add("btn-loading");
  } else {
    btn.disabled = false;
    btn.textContent = btn.dataset.originalText || btn.textContent;
    btn.classList.remove("btn-loading");
  }
}

/**
 * 统一的安全fetch封装，自动处理状态码、CSRF和错误
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @returns {Promise<object>} - 返回JSON数据
 * @throws {Error} - HTTP错误或网络错误
 */
async function safeFetch(url, options = {}) {
  // 自动添加CSRF Token到POST/PUT/DELETE请求
  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PUT", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      options.headers = options.headers || {};
      options.headers["X-CSRF-Token"] = csrfToken;
    }
  }
  
  const res = await fetch(url, options);
  
  // 状态码验证
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // 根据状态码提供友好错误信息
    const friendlyErrors = {
      400: "请求参数错误",
      401: "未授权，请重新登录",
      403: "权限不足",
      404: "资源不存在",
      429: "请求过于频繁，请稍后再试",
      500: "服务器内部错误",
      502: "服务暂时不可用",
      503: "服务维护中"
    };
    const friendlyMsg = friendlyErrors[res.status] || `HTTP ${res.status}`;
    throw new Error(err.error || friendlyMsg);
  }
  
  return res.json();
}

/**
 * HTML转义函数，防止XSS攻击
 * @param {string} str - 待转义字符串
 * @returns {string} - 转义后的安全字符串
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/\//g, "&#x2F;"); // 防止闭合标签攻击
}

/**
 * 防抖函数 - 延迟执行函数，避免频繁调用
 * @param {Function} func - 待防抖的函数
 * @param {number} wait - 延迟时间（毫秒），默认300ms
 * @returns {Function} - 防抖后的函数
 */
function debounce(func, wait = 300) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// === 导航 ===
document.querySelectorAll("#nav-menu li[data-page]").forEach(el => {
  el.onclick = () => {
    document.querySelectorAll("#nav-menu li[data-page]").forEach(e => e.classList.remove("active"));
    el.classList.add("active");
    loadPage(el.dataset.page);
  };
});

// === 页面加载 ===
async function loadPage(page) {
  const content = document.getElementById("content");
  content.innerHTML = "<div class='panel'><p style='text-align:center;color:var(--text-muted);padding:40px'>加载中...</p></div>";
  try {
    switch(page) {
      case "dashboard":
        content.innerHTML = await renderDashboard();
        setTimeout(renderDashboardCharts, 100);
        break;
      case "translate": content.innerHTML = renderTranslate(); await loadCorpus(); break;
      case "compliance": content.innerHTML = renderCompliance(); await loadRules(); break;
      case "vision": content.innerHTML = renderVision(); await loadPreferences(); break;
      case "knowledge": content.innerHTML = renderKnowledge(); await loadKnowledge(); break;
      case "recommend": content.innerHTML = renderRecommend(); break;
      case "settings": content.innerHTML = renderSettings(); await loadProviders(); await loadUsers(); break;
    }
  } catch(e) {
    content.innerHTML = `<div class='panel'><p style='color:var(--danger)'>加载失败: ${escapeHtml(e.message)}</p></div>`;
  }
}

// === 1. 数据看板 ===
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
      <div class="stat-card"><div class="label">视觉识别量</div><div class="value">${escapeHtml(stats.vision_analyses||0)}</div></div>
      <div class="stat-card"><div class="label">知识库条目</div><div class="value">${escapeHtml(stats.knowledge_entries||0)}</div></div>
    </div>

    <!-- 图表区域 -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px">
      <div class="panel">
        <h2>📈 趋势分析（近7天）</h2>
        <div style="height:300px">
          <canvas id="trend-chart"></canvas>
        </div>
      </div>
      <div class="panel">
        <h2>📊 模块使用占比</h2>
        <div style="height:300px">
          <canvas id="usage-chart"></canvas>
        </div>
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

/**
 * 渲染看板图表
 * 获取每日数据并渲染趋势图和饼图
 */
async function renderDashboardCharts() {
  try {
    const data = await safeFetch(API + "/dashboard/daily");

    // 渲染趋势折线图
    if (data.daily_stats && data.daily_stats.length > 0) {
      const labels = data.daily_stats.map(d => d.date);
      const translationsData = data.daily_stats.map(d => d.translations || 0);
      const auditsData = data.daily_stats.map(d => d.audits || 0);
      const visionData = data.daily_stats.map(d => d.vision_analyses || 0);

      Charts.line('trend-chart', labels, [
        { label: '翻译量', data: translationsData, color: '#3b82f6' },
        { label: '审核量', data: auditsData, color: '#22c55e' },
        { label: '视觉识别', data: visionData, color: '#eab308' }
      ]);
    } else {
      // 无数据时显示空图表
      Charts.line('trend-chart', ['无数据'], [{ label: '暂无数据', data: [0] }]);
    }

    // 渲染占比饼图
    if (data.usage_summary) {
      const usageLabels = ['翻译', '审核', '视觉识别', '知识库查询'];
      const usageData = [
        data.usage_summary.translations || 0,
        data.usage_summary.audits || 0,
        data.usage_summary.vision_analyses || 0,
        data.usage_summary.knowledge_queries || 0
      ];

      Charts.pie('usage-chart', usageLabels, usageData);
    } else {
      // 无数据时显示空图表
      Charts.pie('usage-chart', ['暂无数据'], [1]);
    }
  } catch(e) {
    console.error("加载图表数据失败:", e);
    // 显示错误提示
    const trendContainer = document.getElementById('trend-chart');
    const usageContainer = document.getElementById('usage-chart');
    if (trendContainer) {
      trendContainer.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">加载趋势数据失败</p>';
    }
    if (usageContainer) {
      usageContainer.parentElement.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:40px">加载占比数据失败</p>';
    }
  }
}

// === 2. 智能翻译 ===
function renderTranslate() {
  return `
    <h2 style="color:var(--accent);margin-bottom:20px">🌐 智能翻译模块</h2>
    
    <div class="panel"><h2>📝 翻译测试</h2>
      <div class="form-row">
        <textarea id="trans-input" placeholder="输入需要翻译的汉服相关文本（中文）..." style="flex:2"></textarea>
        <select id="trans-lang" style="min-width:100px">
          ${Object.entries(LANGUAGES).map(([k,v])=>`<option value="${k}">${v}</option>`).join("")}
        </select>
        <button class="btn btn-primary" onclick="doTranslate()">翻译</button>
      </div>
      <div id="trans-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px;white-space:pre-wrap;font-size:14px"></div>
    </div>
    
    <div class="panel"><h2>📖 语料库管理 (共<span id="corpus-total">0</span>条)</h2>
      <div class="form-row">
        <input id="corpus-search" placeholder="搜索术语..." oninput="debounce(loadCorpus)()">
        <select id="corpus-cat" onchange="loadCorpus()">
          <option value="">全部分类</option>
          ${CATEGORIES.map(c=>`<option value="${c}">${c}</option>`).join("")}
        </select>
        <button class="btn btn-primary" onclick="showAddTerm()">+ 添加术语</button>
      </div>
      <div id="add-term-form" style="display:none;margin-bottom:16px;padding:16px;border:1px solid var(--border);border-radius:8px">
        <h3>新增术语</h3>
        <div class="form-row">
          <input id="new-term" placeholder="中文术语">
          <select id="new-cat">${CATEGORIES.map(c=>`<option>${c}</option>`).join("")}</select>
        </div>
        <div class="form-row"><input id="new-def" placeholder="释义（可选）" style="flex:1"></div>
        <div class="form-row"><input id="new-note" placeholder="文化注释（可选）" style="flex:1"></div>
        <div class="form-row" id="new-translations">
          ${Object.entries(LANGUAGES).map(([k,v])=>`<input placeholder="${v}译文" data-lang="${k}" style="flex:1">`).join("")}
        </div>
        <button class="btn btn-success" onclick="addTerm()">确认添加</button>
        <button class="btn btn-outline" onclick="document.getElementById('add-term-form').style.display='none'">取消</button>
      </div>
      <div style="overflow-x:auto">
        <table><thead><tr><th>ID</th><th>术语</th><th>分类</th><th>文化注释</th><th>操作</th></tr></thead>
        <tbody id="corpus-table"></tbody></table>
      </div>
      <div id="corpus-pager" style="margin-top:12px;text-align:center"></div>
    </div>`;
}

async function loadCorpus(page=1) {
  const kw = document.getElementById("corpus-search")?.value || "";
  const cat = document.getElementById("corpus-cat")?.value || "";
  try {
    const data = await safeFetch(`${API}/corpus?page=${page}&keyword=${encodeURIComponent(kw)}&category=${encodeURIComponent(cat)}`);
    document.getElementById("corpus-total").textContent = data.total;
    document.getElementById("corpus-table").innerHTML = data.items.map(i => `
      <tr>
        <td>${escapeHtml(i.id)}</td>
        <td><b>${escapeHtml(i.term_zh)}</b></td>
        <td>${escapeHtml(i.category)}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(i.cultural_note||"-")}</td>
        <td><button class="btn btn-sm btn-outline" onclick="editTerm(${escapeHtml(i.id)})">编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTerm(${escapeHtml(i.id)})">删除</button></td>
      </tr>`).join("");
  } catch(e) {
    toast("加载语料库失败: " + e.message, "error");
  }
}

async function doTranslate() {
  const text = document.getElementById("trans-input").value;
  const lang = document.getElementById("trans-lang").value;
  
  // 输入验证
  const validation = validateInput(text, 1, 5000, "翻译文本");
  if (!validation.valid) {
    document.getElementById("trans-result").innerHTML = `<span style="color:var(--danger)">${escapeHtml(validation.error)}</span>`;
    return;
  }
  
  // 设置加载状态
  const btn = document.querySelector("button[onclick='doTranslate()']");
  setButtonLoading(btn, true, "翻译中...");
  
  try {
    const data = await safeFetch(API+"/translate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: validation.value, target_lang: lang})
    });
    // 使用escapeHtml防止XSS
    document.getElementById("trans-result").innerHTML = 
      `<b>翻译结果：</b>${escapeHtml(data.translated)}<br>\
       <b>准确率：</b>${(data.confidence*100).toFixed(0)}% &nbsp;|&nbsp;\
       <b>耗时：</b>${escapeHtml(String(data.response_time_ms))}ms<br>\
       <b>匹配术语：</b>${escapeHtml(data.matched_terms.map(t=>t.term).join(", ")||"无")}<br>\
       ${data.matched_terms.map(t=>`<small>📌 ${escapeHtml(t.term)}: ${escapeHtml(t.cultural_note||"")}</small><br>`).join("")}`;
  } catch(e) {
    document.getElementById("trans-result").innerHTML = `<span style="color:var(--danger)">翻译失败: ${escapeHtml(e.message)}</span>`;
  } finally {
    setButtonLoading(btn, false);
  }
}

function showAddTerm() { document.getElementById("add-term-form").style.display="block"; }

async function addTerm() {
  const term_zh = document.getElementById("new-term").value;
  const category = document.getElementById("new-cat").value;
  const definition = document.getElementById("new-def").value;
  const cultural_note = document.getElementById("new-note").value;
  const translations = {};
  document.querySelectorAll("#new-translations input").forEach(inp => {
    if(inp.value) translations[inp.dataset.lang] = inp.value;
  });
  
  // 输入验证
  const termValidation = validateInput(term_zh, 1, 100, "中文术语");
  if (!termValidation.valid) return toast(termValidation.error, "error");
  
  const btn = document.querySelector("button[onclick='addTerm()']");
  setButtonLoading(btn, true, "添加中...");
  
  try {
    await safeFetch(API+"/corpus", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({term_zh: termValidation.value, category, definition, cultural_note, translations})
    });
    document.getElementById("add-term-form").style.display="none";
    loadCorpus();
    toast("术语添加成功", "success");
  } catch(e) {
    toast("添加失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

async function deleteTerm(id) {
  if(!confirm("确认删除？")) return;
  try {
    await safeFetch(API+"/corpus/"+id, {method: "DELETE"});
    loadCorpus();
    toast("已删除", "success");
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}

// ---- 术语编辑弹窗 ----
async function editTerm(id) {
  try {
    const data = await safeFetch(API+"/corpus?page=1&per_page=100");
    const term = data.items.find(t => t.id === id);
    if (!term) return toast("术语未找到", "error");
    showEditModal({
      title: "编辑术语",
      fields: [
        {label:"中文术语", name:"term_zh", value:term.term_zh, type:"text"},
        {label:"分类", name:"category", value:term.category, type:"select", options:CATEGORIES},
        {label:"释义", name:"definition", value:term.definition||"", type:"text"},
        {label:"文化注释", name:"cultural_note", value:term.cultural_note||"", type:"text"},
        {label:"标签（逗号分隔）", name:"tags", value:typeof term.tags==="string"?term.tags:JSON.parse(term.tags||"[]").join(","), type:"text"},
      ],
      translations: typeof term.translations==="string"?JSON.parse(term.translations):(term.translations||{}),
      onSave: async (formData) => {
        const body = {};
        for (const [k,v] of formData) { body[k] = v; }
        try {
          await safeFetch(API+"/corpus/"+id, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
          });
          loadCorpus();
          toast("术语更新成功", "success");
          closeModal();
        } catch(e) {
          toast("更新失败: " + e.message, "error");
        }
      }
    });
  } catch(e) {
    toast("加载术语失败: " + e.message, "error");
  }
}

// ---- 通用编辑弹窗 ----
function showEditModal({title, fields, translations, onSave}) {
  let html = `<div class="modal-overlay" id="edit-modal" onclick="if(event.target===this)closeModal()">
    <div class="modal-content"><h2>${title}</h2><div class="modal-body">`;
  
  for (const f of fields) {
    if (f.type === "select") {
      html += `<label>${f.label}</label><select name="${f.name}">${f.options.map(o=>`<option value="${o}" ${o===f.value?"selected":""}>${o}</option>`).join("")}</select>`;
    } else {
      html += `<label>${f.label}</label><input name="${f.name}" value="${escapeHtml(f.value)}" type="${f.type||"text"}">`;
    }
  }
  
  if (translations) {
    html += `<h3 style="margin-top:16px">多语种翻译</h3>`;
    for (const [lang, name] of Object.entries(LANGUAGES)) {
      html += `<label>${name} (${lang})</label><input name="trans_${lang}" value="${escapeHtml(translations[lang]||"")}">`;
    }
  }
  
  html += `</div><div class="modal-footer">
    <button class="btn btn-success" id="modal-save-btn">保存</button>
    <button class="btn btn-outline" onclick="closeModal()">取消</button>
  </div></div></div>`;
  
  const div = document.createElement("div");
  div.innerHTML = html;
  document.body.appendChild(div);
  
  document.getElementById("modal-save-btn").onclick = async () => {
    const formData = new Map();
    document.querySelectorAll("#edit-modal input, #edit-modal select").forEach(el => {
      if (el.name.startsWith("trans_")) {
        const lang = el.name.replace("trans_","");
        if (!formData.has("_translations")) formData.set("_translations",{});
        formData.get("_translations")[lang] = el.value;
      } else {
        formData.set(el.name, el.value);
      }
    });
    if (formData.has("_translations")) {
      formData.set("translations", JSON.stringify(formData.get("_translations")));
      formData.delete("_translations");
    }
    // tags 特殊处理
    if (formData.has("tags")) {
      formData.set("tags", JSON.stringify(formData.get("tags").split(",").map(s=>s.trim()).filter(Boolean)));
    }
    await onSave(formData);
  };
}

function closeModal() {
  const m = document.getElementById("edit-modal");
  if (m) m.remove();
}

// === 3. 合规审核 ===
function renderCompliance() {
  return `
    <h2 style="color:var(--accent);margin-bottom:20px">🛡️ 文化禁忌合规审核</h2>
    
    <div class="panel"><h2>📝 文本审核测试</h2>
      <div class="form-row">
        <textarea id="audit-text" placeholder="输入待审核文案..." style="flex:2"></textarea>
        <select id="audit-country">
          ${REGIONS.filter(r=>r!="全球").map(r=>`<option>${r}</option>`).join("")}
          <option value="沙特阿拉伯">沙特阿拉伯</option><option value="印度">印度</option>
        </select>
        <button class="btn btn-primary" onclick="doAuditText()">审核</button>
      </div>
      <div id="audit-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px"></div>
    </div>
    
    <div class="panel"><h2>📋 规则库管理 (共<span id="rules-total">0</span>条)</h2>
      <div class="form-row">
        <select id="rules-country" onchange="loadRules()"><option value="">全部国家</option></select>
        <select id="rules-cat" onchange="loadRules()"><option value="">全部类别</option>${TABOO_CATS.map(c=>`<option>${c}</option>`).join("")}</select>
        <button class="btn btn-primary" onclick="showAddRule()">+ 添加规则</button>
      </div>
      <div id="add-rule-form" style="display:none;margin-bottom:16px;padding:16px;border:1px solid var(--border);border-radius:8px">
        <h3>新增规则</h3>
        <div class="form-row">
          <input id="new-rule-country" placeholder="国家（如：沙特阿拉伯）">
          <select id="new-rule-cat">${TABOO_CATS.map(c=>`<option>${c}</option>`).join("")}</select>
          <select id="new-rule-risk"><option>高风险</option><option>低风险</option></select>
        </div>
        <div class="form-row"><input id="new-rule-kw" placeholder="敏感词（逗号分隔）" style="flex:1"></div>
        <div class="form-row"><input id="new-rule-reason" placeholder="风险原因" style="flex:1"></div>
        <div class="form-row"><input id="new-rule-sugg" placeholder="修改建议" style="flex:1"></div>
        <button class="btn btn-success" onclick="addRule()">确认添加</button>
        <button class="btn btn-outline" onclick="document.getElementById('add-rule-form').style.display='none'">取消</button>
      </div>
      <div style="overflow-x:auto"><table><thead><tr><th>ID</th><th>国家</th><th>类别</th><th>风险等级</th><th>原因</th><th>操作</th></tr></thead><tbody id="rules-table"></tbody></table></div>
    </div>`;
}

async function loadRules() {
  const country = document.getElementById("rules-country")?.value||"";
  const cat = document.getElementById("rules-cat")?.value||"";
  try {
    const data = await safeFetch(`${API}/compliance/rules?country=${encodeURIComponent(country)}&category=${encodeURIComponent(cat)}`);
    document.getElementById("rules-total").textContent = data.total;
    document.getElementById("rules-table").innerHTML = data.items.map(r => `
      <tr>
        <td>${escapeHtml(r.id)}</td>
        <td>${escapeHtml(r.country)}</td>
        <td>${escapeHtml(r.category)}</td>
        <td><span class="badge ${r.risk_level==='高风险'?'badge-high':'badge-review'}">${escapeHtml(r.risk_level)}</span></td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(r.reason)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="editRule(${escapeHtml(r.id)})">编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteRule(${escapeHtml(r.id)})">删除</button></td>
      </tr>`).join("");
    // 填充国家下拉
    document.getElementById("rules-country").innerHTML = '<option value="">全部国家</option>'+
      [...new Set(data.items.map(r=>r.country))].map(c=>`<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  } catch(e) {
    toast("加载规则失败: " + e.message, "error");
  }
}

async function doAuditText() {
  const text = document.getElementById("audit-text").value;
  const country = document.getElementById("audit-country").value;
  
  // 输入验证
  const validation = validateInput(text, 1, 5000, "审核文本");
  if (!validation.valid) {
    document.getElementById("audit-result").innerHTML = `<span style="color:var(--danger)">${escapeHtml(validation.error)}</span>`;
    return;
  }
  
  // 设置加载状态
  const btn = document.querySelector("button[onclick='doAuditText()']");
  setButtonLoading(btn, true, "审核中...");
  
  try {
    const data = await safeFetch(API+"/compliance/audit/text", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: validation.value, country})
    });
    const badge = data.risk_level==="合规" ? "badge-pass" : data.risk_level==="低风险" ? "badge-review" : "badge-high";
    // 使用escapeHtml防止XSS
    document.getElementById("audit-result").innerHTML = `
      <span class="badge ${badge}">${escapeHtml(data.risk_level)}</span> &nbsp;
      <b>耗时：</b>${escapeHtml(String(data.response_time_ms))}ms<br>
      <b>匹配规则：</b>${escapeHtml(String(data.matched_rules_count))}条<br>
      ${data.reasons.length ? `<b>⚠️ 风险原因：</b>${escapeHtml(data.reasons.join("；"))}<br>`:""}
      ${data.suggestions.length ? `<b>💡 修改建议：</b>${escapeHtml(data.suggestions.join("；"))}`:""}`;
  } catch(e) {
    document.getElementById("audit-result").innerHTML = `<span style="color:var(--danger)">审核失败: ${escapeHtml(e.message)}</span>`;
  } finally {
    setButtonLoading(btn, false);
  }
}

function showAddRule() { document.getElementById("add-rule-form").style.display="block"; }

async function addRule() {
  const data = {
    country: document.getElementById("new-rule-country").value,
    category: document.getElementById("new-rule-cat").value,
    keywords: document.getElementById("new-rule-kw").value.split(",").map(s=>s.trim()).filter(Boolean),
    reason: document.getElementById("new-rule-reason").value,
    suggestion: document.getElementById("new-rule-sugg").value,
    risk_level: document.getElementById("new-rule-risk").value,
  };
  
  // 输入验证
  const countryValidation = validateInput(data.country, 1, 50, "国家");
  if (!countryValidation.valid) return toast(countryValidation.error, "error");
  if (!data.category) return toast("请选择类别", "error");
  if (!data.keywords.length) return toast("请填写敏感词", "error");
  
  const btn = document.querySelector("button[onclick='addRule()']");
  setButtonLoading(btn, true, "添加中...");
  
  try {
    await safeFetch(API+"/compliance/rules", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
    document.getElementById("add-rule-form").style.display="none";
    loadRules();
    toast("规则添加成功", "success");
  } catch(e) {
    toast("添加失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

async function deleteRule(id) {
  if(!confirm("确认删除？")) return;
  try {
    await safeFetch(API+"/compliance/rules/"+id, {method: "DELETE"});
    loadRules();
    toast("已删除", "success");
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}

async function editRule(id) {
  try {
    const data = await safeFetch(API+"/compliance/rules?page=1&per_page=100");
    const rule = data.items.find(r => r.id === id);
    if (!rule) return toast("规则未找到", "error");

    let kwStr = "";
    try { kwStr = (typeof rule.keywords==="string"?JSON.parse(rule.keywords):rule.keywords).join(","); } catch(e) {}

    showEditModal({
      title: "编辑合规规则",
      fields: [
        {label:"国家", name:"country", value:rule.country, type:"text"},
        {label:"区域", name:"region", value:rule.region||"", type:"text"},
        {label:"类别", name:"category", value:rule.category, type:"select", options:TABOO_CATS},
        {label:"敏感词（逗号分隔）", name:"keywords", value:kwStr, type:"text"},
        {label:"纹样/符号描述", name:"pattern", value:rule.pattern||"", type:"text"},
        {label:"风险等级", name:"risk_level", value:rule.risk_level, type:"select", options:["高风险","低风险"]},
        {label:"风险原因", name:"reason", value:rule.reason||"", type:"text"},
        {label:"修改建议", name:"suggestion", value:rule.suggestion||"", type:"text"},
      ],
      onSave: async (formData) => {
        const body = {};
        for (const [k,v] of formData) {
          body[k] = k === "keywords" ? JSON.stringify(v.split(",").map(s=>s.trim()).filter(Boolean)) : v;
        }
        try {
          await safeFetch(API+"/compliance/rules/"+id, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(body)
          });
          loadRules();
          toast("规则更新成功", "success");
          closeModal();
        } catch(e) {
          toast("更新失败: " + e.message, "error");
        }
      }
    });
  } catch(e) {
    toast("加载规则失败: " + e.message, "error");
  }
}

// === 4. 视觉识别 ===
function renderVision() {
  return `
    <h2 style="color:var(--accent);margin-bottom:20px">👁️ 视觉识别模块</h2>
    <div class="panel"><h2>🔍 汉服识别测试</h2>
      <div class="form-row">
        <input id="vision-path" placeholder="图片路径（如：images/hanfu.jpg）" style="flex:2">
        <button class="btn btn-primary" onclick="doVision()">识别</button>
      </div><div id="vision-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px"></div>
    </div>
    <div class="panel"><h2>🎨 区域审美库 (共<span id="pref-total">0</span>条)</h2>
      <div id="pref-list"></div>
      <div class="form-row" style="margin-top:12px">
        <select id="pref-region">${REGIONS.map(r=>`<option>${r}</option>`).join("")}</select>
        <select id="pref-cat"><option>色彩</option><option>纹样</option><option>风格</option></select>
        <input id="pref-value" placeholder="偏好描述">
        <button class="btn btn-primary btn-sm" onclick="addPreference()">添加</button>
      </div>
    </div>`;
}
async function loadPreferences() {
  try {
    const data = await safeFetch(API+"/vision/preferences");
    document.getElementById("pref-total").textContent = data.length;
    document.getElementById("pref-list").innerHTML = data.map(p => `
      <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border);align-items:center">
        <span><b>${escapeHtml(p.region)}</b> → ${escapeHtml(p.category)}: ${escapeHtml(p.preference)} <small style="color:var(--text-muted)">权重${escapeHtml(p.weight)}</small></span>
        <button class="btn btn-sm btn-danger" onclick="deletePref(${escapeHtml(p.id)})">×</button>
      </div>`).join("");
  } catch(e) {
    toast("加载偏好失败: " + e.message, "error");
  }
}

async function addPreference() {
  const d = { 
    region: document.getElementById("pref-region").value, 
    category: document.getElementById("pref-cat").value, 
    preference: document.getElementById("pref-value").value 
  };
  
  // 输入验证
  const prefValidation = validateInput(d.preference, 1, 200, "偏好描述");
  if (!prefValidation.valid) return toast(prefValidation.error, "error");
  
  const btn = document.querySelector("button[onclick='addPreference()']");
  setButtonLoading(btn, true, "添加中...");
  
  try {
    await safeFetch(API+"/vision/preferences", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(d)
    });
    loadPreferences();
    toast("添加成功", "success");
  } catch(e) {
    toast("添加失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

async function deletePref(id) {
  try {
    await safeFetch(API+"/vision/preferences/"+id, {method: "DELETE"});
    loadPreferences();
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}

async function doVision() {
  const path = document.getElementById("vision-path").value;
  
  // 输入验证
  const pathValidation = validateInput(path, 1, 500, "图片路径");
  if (!pathValidation.valid) {
    document.getElementById("vision-result").innerHTML = `<span style="color:var(--danger)">${escapeHtml(pathValidation.error)}</span>`;
    return;
  }
  
  // 设置加载状态
  const btn = document.querySelector("button[onclick='doVision()']");
  setButtonLoading(btn, true, "识别中...");
  
  try {
    const d = await safeFetch(API+"/vision/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image_path: pathValidation.value})
    });
    // 使用escapeHtml防止XSS
    document.getElementById("vision-result").innerHTML = 
      `<b>朝代：</b>${escapeHtml(d.dynasty)} | <b>形制：</b>${escapeHtml(d.format)} | <b>色彩：</b>${escapeHtml(d.colors?.join(", ")||"")} | <b>纹样：</b>${escapeHtml(d.patterns?.join(", ")||"")} | <b>准确率：</b>${(d.confidence*100).toFixed(0)}%`;
  } catch(e) {
    document.getElementById("vision-result").innerHTML = `<span style="color:var(--danger)">识别失败: ${escapeHtml(e.message)}</span>`;
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 5. 知识库 ===
function renderKnowledge() {
  return `<h2 style="color:var(--accent);margin-bottom:20px">📚 文化解读知识库</h2>
    <div class="panel"><h2>📖 知识检索</h2>
      <div class="form-row">
        <input id="kb-search" placeholder="搜索..." style="flex:2">
        <select id="kb-cat"><option value="">全部分类</option>${CATEGORIES.map(c=>`<option>${c}</option>`).join("")}</select>
        <button class="btn btn-primary" onclick="loadKnowledge()">搜索</button>
      </div>
      <div id="kb-list" style="margin-top:12px"></div>
    </div>
    <div class="panel"><h2>✍️ 文案生成</h2>
      <div class="form-row">
        <input id="copy-topic" placeholder="主题（如：马面裙穿搭）" style="flex:2">
        <select id="copy-region">${REGIONS.filter(r=>r!=="全球").map(r=>`<option>${r}</option>`).join("")}</select>
        <button class="btn btn-primary" onclick="genCopy()">生成文案</button>
      </div>
      <div id="copy-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px;white-space:pre-wrap"></div>
    </div>`;
}
async function loadKnowledge() {
  const kw = document.getElementById("kb-search")?.value||"";
  const cat = document.getElementById("kb-cat")?.value||"";
  try {
    const data = await safeFetch(`${API}/knowledge?keyword=${encodeURIComponent(kw)}&category=${encodeURIComponent(cat)}`);
    document.getElementById("kb-list").innerHTML = data.items.map(i => `
      <div style="padding:12px;border-bottom:1px solid var(--border)">
        <b>${escapeHtml(i.title_zh)}</b> <span class="badge badge-pass">${escapeHtml(i.category)}</span>
        <p style="color:var(--text-muted);margin-top:4px">${(i.content_zh||"").substring(0,150)}...</p>
      </div>`).join("") || "<p style='color:var(--text-muted)'>无结果</p>";
  } catch(e) {
    toast("加载知识库失败: " + e.message, "error");
  }
}

async function genCopy() {
  const topic = document.getElementById("copy-topic").value;
  const region = document.getElementById("copy-region").value;
  
  // 输入验证
  const topicValidation = validateInput(topic, 1, 200, "主题");
  if (!topicValidation.valid) {
    document.getElementById("copy-result").innerHTML = `<span style="color:var(--danger)">${escapeHtml(topicValidation.error)}</span>`;
    return;
  }
  
  // 设置加载状态
  const btn = document.querySelector("button[onclick='genCopy()']");
  setButtonLoading(btn, true, "生成中...");
  
  try {
    const d = await safeFetch(API+"/knowledge/generate-copy", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic: topicValidation.value, region})
    });
    // 使用escapeHtml防止XSS
    document.getElementById("copy-result").innerHTML = 
      `<b>📝 文案：</b>${escapeHtml(d.short_copy)}<br><b>🏷️ 标签：</b>${escapeHtml(d.hashtags.join(" "))}<br><b>📌 文化注释：</b>${escapeHtml(d.cultural_note)}`;
  } catch(e) {
    document.getElementById("copy-result").innerHTML = `<span style="color:var(--danger)">生成失败: ${escapeHtml(e.message)}</span>`;
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 6. 推荐 ===
function renderRecommend() {
  return `<h2 style="color:var(--accent);margin-bottom:20px">🎯 个性化推荐（P2 - 开发中）</h2>
    <div class="panel"><p style="color:var(--text-muted)">推荐引擎基于用户画像+视觉标签+审美偏好生成内容推荐，匹配准确率目标≥35%。</p>
      <button class="btn btn-primary" style="margin-top:12px" onclick="testRecommend()">运行测试推荐</button>
      <div id="rec-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px"></div>
    </div>`;
}
async function testRecommend() {
  const btn = document.querySelector("button[onclick='testRecommend()']");
  setButtonLoading(btn, true, "推荐中...");
  
  try {
    const d = await safeFetch(API+"/recommend", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        user_profile:{age:"25-34",interests:["fashion","culture"],region:"北美"},
        visual_tags:{colors:["红色","金色"],patterns:["云纹"]},
        region:"北美"
      })
    });
    document.getElementById("rec-result").innerHTML = `<pre style="white-space:pre-wrap">${escapeHtml(JSON.stringify(d,null,2))}</pre>`;
  } catch(e) {
    document.getElementById("rec-result").innerHTML = `<span style="color:var(--danger)">推荐失败: ${escapeHtml(e.message)}</span>`;
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 7. 设置 ===
function renderSettings() {
  return `<h2 style="color:var(--accent);margin-bottom:20px">⚙️ 系统设置</h2>

    <div class="panel"><h2>🤖 AI供应商配置</h2>
      <p style="color:var(--text-muted);margin-bottom:16px">配置多个AI供应商，支持OpenAI、DeepSeek、通义千问等。每个供应商可配置独立的API端点、密钥和模型映射。</p>

      <div style="display:flex;gap:20px;min-height:400px">
        <!-- 左侧：供应商列表 -->
        <div style="flex:0 0 280px;border-right:1px solid var(--border);padding-right:20px">
          <div style="margin-bottom:12px">
            <button class="btn btn-primary" onclick="addProvider()" style="width:100%">+ 添加供应商</button>
          </div>
          <div id="provider-list" style="display:flex;flex-direction:column;gap:8px">
            <p style="color:var(--text-muted);text-align:center;padding:20px">加载中...</p>
          </div>
        </div>

        <!-- 右侧：配置详情 -->
        <div style="flex:1" id="provider-detail">
          <p style="color:var(--text-muted);text-align:center;padding:40px">请选择或添加供应商</p>
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
      <p>版本：1.0.0 | Python Flask + SQLite | 默认账户：admin（请联系管理员获取初始密码）</p>
    </div>`;
}

// === AI供应商管理 ===

/**
 * 加载供应商列表
 */
async function loadProviders() {
  try {
    const data = await safeFetch(API + "/ai/providers");
    const listEl = document.getElementById("provider-list");

    if (!data.providers || data.providers.length === 0) {
      listEl.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px">暂无供应商</p>';
      return;
    }

    listEl.innerHTML = data.providers.map(p => `
      <div class="provider-item ${p.is_active ? 'active' : ''}"
           onclick="selectProvider(${escapeHtml(p.id)})"
           style="padding:12px;border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all 0.2s;${p.is_active ? 'border-color:var(--accent);background:var(--input-bg);' : ''}">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <b style="font-size:14px">${escapeHtml(p.name)}</b>
            ${p.is_active ? '<span class="badge badge-pass" style="margin-left:6px">激活</span>' : ''}
          </div>
          <span style="color:var(--text-muted);font-size:12px">${escapeHtml(p.provider_type)}</span>
        </div>
        <div style="color:var(--text-muted);font-size:12px;margin-top:4px">${escapeHtml(p.base_url || '默认端点')}</div>
      </div>
    `).join("");

    // 自动选择第一个激活的供应商
    const activeProvider = data.providers.find(p => p.is_active);
    if (activeProvider) {
      selectProvider(activeProvider.id);
    }
  } catch(e) {
    toast("加载供应商失败: " + e.message, "error");
    document.getElementById("provider-list").innerHTML =
      '<p style="color:var(--danger);text-align:center;padding:20px">加载失败</p>';
  }
}

/**
 * 添加新供应商
 */
async function addProvider() {
  const name = prompt("请输入供应商名称（如：OpenAI-主账号）");
  if (!name || !name.trim()) return;

  const providerType = prompt("请输入供应商类型（openai/deepseek/qwen/custom）", "openai");
  if (!providerType) return;

  const validTypes = ["openai", "deepseek", "qwen", "custom"];
  if (!validTypes.includes(providerType)) {
    return toast("供应商类型必须是: " + validTypes.join(", "), "error");
  }

  try {
    const data = await safeFetch(API + "/ai/providers", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name: name.trim(),
        provider_type: providerType
      })
    });
    toast("供应商创建成功", "success");
    await loadProviders();
    selectProvider(data.id);
  } catch(e) {
    toast("创建失败: " + e.message, "error");
  }
}

/**
 * 选择供应商并显示详情
 */
async function selectProvider(providerId) {
  try {
    const data = await safeFetch(API + "/ai/providers");
    const provider = data.providers.find(p => p.id === providerId);

    if (!provider) {
      return toast("供应商未找到", "error");
    }

    // 更新列表选中状态
    document.querySelectorAll(".provider-item").forEach(el => {
      el.style.borderColor = "var(--border)";
      el.style.background = "transparent";
    });
    event.currentTarget.style.borderColor = "var(--accent)";
    event.currentTarget.style.background = "var(--input-bg)";

    // 渲染详情
    renderProviderDetail(provider);
  } catch(e) {
    toast("加载供应商详情失败: " + e.message, "error");
  }
}

/**
 * 渲染供应商配置详情
 */
function renderProviderDetail(provider) {
  const detailEl = document.getElementById("provider-detail");

  // 解析模型映射
  let modelMapping = {translate: "", compliance: "", vision: "", knowledge: ""};
  try {
    if (provider.model_mapping) {
      modelMapping = typeof provider.model_mapping === "string"
        ? JSON.parse(provider.model_mapping)
        : provider.model_mapping;
    }
  } catch(e) {
    console.error("解析模型映射失败:", e);
  }

  detailEl.innerHTML = `
    <div style="padding:20px;border:1px solid var(--border);border-radius:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <h3 style="margin:0">${escapeHtml(provider.name)}</h3>
        <div>
          ${provider.is_active
            ? '<span class="badge badge-pass">已激活</span>'
            : '<button class="btn btn-success btn-sm" onclick="activateProvider(' + provider.id + ')">激活</button>'}
          <button class="btn btn-outline btn-sm" onclick="testProvider(${provider.id})" style="margin-left:8px">测试连接</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProvider(${provider.id})" style="margin-left:8px" ${provider.is_active ? 'disabled' : ''}>删除</button>
        </div>
      </div>

      <div class="form-row">
        <label style="min-width:120px">供应商类型</label>
        <input value="${escapeHtml(provider.provider_type)}" disabled style="flex:1;background:var(--input-bg)">
      </div>

      <div class="form-row">
        <label style="min-width:120px">API端点</label>
        <input id="provider-url-${provider.id}" value="${escapeHtml(provider.base_url || '')}"
               placeholder="留空使用默认端点" style="flex:1">
      </div>

      <div class="form-row">
        <label style="min-width:120px">API密钥</label>
        <input id="provider-key-${provider.id}" type="password"
               value="${escapeHtml(provider.api_key || '')}"
               placeholder="sk-xxxxxxxx" style="flex:1">
        <span style="color:var(--text-muted);margin-left:8px;font-size:12px">
          ${provider.api_key ? '✓ 已设置' : '未设置'}
        </span>
      </div>

      <h4 style="margin-top:24px;margin-bottom:12px;color:var(--accent)">🎯 模型映射（4层）</h4>
      <p style="color:var(--text-muted);font-size:13px;margin-bottom:16px">
        为不同功能模块指定专用模型，留空则使用供应商默认模型
      </p>

      <div class="form-row">
        <label style="min-width:120px">🌐 翻译模型</label>
        <input id="model-translate-${provider.id}" value="${escapeHtml(modelMapping.translate || '')}"
               placeholder="如：gpt-4o-mini" style="flex:1">
      </div>

      <div class="form-row">
        <label style="min-width:120px">🛡️ 合规模型</label>
        <input id="model-compliance-${provider.id}" value="${escapeHtml(modelMapping.compliance || '')}"
               placeholder="如：deepseek-chat" style="flex:1">
      </div>

      <div class="form-row">
        <label style="min-width:120px">👁️ 视觉模型</label>
        <input id="model-vision-${provider.id}" value="${escapeHtml(modelMapping.vision || '')}"
               placeholder="如：gpt-4o" style="flex:1">
      </div>

      <div class="form-row">
        <label style="min-width:120px">📚 知识库模型</label>
        <input id="model-knowledge-${provider.id}" value="${escapeHtml(modelMapping.knowledge || '')}"
               placeholder="如：qwen-turbo" style="flex:1">
      </div>

      <div style="margin-top:20px">
        <button class="btn btn-success" onclick="saveProvider(${provider.id})">💾 保存配置</button>
        <span id="provider-status-${provider.id}" style="margin-left:12px"></span>
      </div>
    </div>`;
}

/**
 * 保存供应商配置
 */
async function saveProvider(providerId) {
  const data = {
    base_url: document.getElementById(`provider-url-${providerId}`).value.trim() || null,
    api_key: document.getElementById(`provider-key-${providerId}`).value.trim() || null,
    model_mapping: {
      translate: document.getElementById(`model-translate-${providerId}`).value.trim() || null,
      compliance: document.getElementById(`model-compliance-${providerId}`).value.trim() || null,
      vision: document.getElementById(`model-vision-${providerId}`).value.trim() || null,
      knowledge: document.getElementById(`model-knowledge-${providerId}`).value.trim() || null
    }
  };

  const btn = document.querySelector(`button[onclick="saveProvider(${providerId})"]`);
  setButtonLoading(btn, true, "保存中...");

  try {
    await safeFetch(API + "/ai/providers/" + providerId, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
    toast("配置已保存", "success");
    document.getElementById(`provider-status-${providerId}`).innerHTML =
      '<span style="color:var(--success)">✓ 已保存</span>';
    await loadProviders();
  } catch(e) {
    toast("保存失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

/**
 * 测试供应商连接
 */
async function testProvider(providerId) {
  const statusEl = document.getElementById(`provider-status-${providerId}`);
  statusEl.innerHTML = '<span style="color:var(--text-muted)">测试中...</span>';

  try {
    const result = await safeFetch(API + "/ai/providers/" + providerId + "/test", {
      method: "POST"
    });

    if (result.success) {
      statusEl.innerHTML = '<span style="color:var(--success)">✓ ' + escapeHtml(result.message) + '</span>';
      toast("连接成功", "success");
    } else {
      statusEl.innerHTML = '<span style="color:var(--danger)">✗ ' + escapeHtml(result.message) + '</span>';
      toast(result.message, "error");
    }
  } catch(e) {
    statusEl.innerHTML = '<span style="color:var(--danger)">✗ 连接失败</span>';
    toast("测试失败: " + e.message, "error");
  }
}

/**
 * 激活供应商
 */
async function activateProvider(providerId) {
  if (!confirm("确认激活此供应商？激活后将切换到该供应商的配置。")) return;

  try {
    await safeFetch(API + "/ai/providers/" + providerId + "/activate", {
      method: "POST"
    });
    toast("供应商已激活", "success");
    await loadProviders();
  } catch(e) {
    toast("激活失败: " + e.message, "error");
  }
}

/**
 * 删除供应商
 */
async function deleteProvider(providerId) {
  if (!confirm("确认删除此供应商？此操作不可恢复。")) return;

  try {
    await safeFetch(API + "/ai/providers/" + providerId, {
      method: "DELETE"
    });
    toast("供应商已删除", "success");
    await loadProviders();
    document.getElementById("provider-detail").innerHTML =
      '<p style="color:var(--text-muted);text-align:center;padding:40px">请选择或添加供应商</p>';
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}
async function loadUsers() {
  try {
    const data = await safeFetch(API+"/users");
    document.getElementById("user-list").innerHTML = `
      <table><tr><th>ID</th><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr>
      ${data.map(u=>`<tr>
        <td>${escapeHtml(u.id)}</td>
        <td><b>${escapeHtml(u.username)}</b></td>
        <td><span class="badge badge-pass">${escapeHtml(u.role)}</span></td>
        <td>${escapeHtml(u.status)}</td>
        <td><button class="btn btn-sm btn-danger" onclick="deleteUser(${escapeHtml(u.id)})" ${u.role==='superadmin'?'disabled':''}>删除</button></td>
      </tr>`).join("")}
      </table>`;
  } catch(e) {
    toast("加载用户失败: " + e.message, "error");
  }
}

async function addUser() {
  const d = { 
    username: document.getElementById("new-user").value, 
    password: document.getElementById("new-pw").value, 
    role: document.getElementById("new-role").value 
  };
  
  // 输入验证
  const userValidation = validateInput(d.username, 2, 50, "用户名");
  if (!userValidation.valid) return toast(userValidation.error, "error");
  
  const pwValidation = validateInput(d.password, 6, 100, "密码");
  if (!pwValidation.valid) return toast(pwValidation.error, "error");
  
  const btn = document.querySelector("button[onclick='addUser()']");
  setButtonLoading(btn, true, "创建中...");
  
  try {
    await safeFetch(API+"/users", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({username: userValidation.value, password: pwValidation.value, role: d.role})
    });
    loadUsers();
    toast("用户创建成功", "success");
  } catch(e) {
    toast("创建失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

async function deleteUser(id) {
  if(!confirm("确认删除？")) return;
  try {
    await safeFetch(API+"/users/"+id, {method: "DELETE"});
    loadUsers();
    toast("已删除", "success");
  } catch(e) {
    toast("删除失败: " + e.message, "error");
  }
}

// === 工具函数 ===
function toast(msg, type="success") {
  const el = document.createElement("div"); el.className=`toast ${type}`; el.textContent=msg; document.body.appendChild(el);
  setTimeout(()=>el.remove(), 3000);
}

// === 初始化 ===
loadPage("dashboard");
