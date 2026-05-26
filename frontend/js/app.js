/* CCAE 跨文化适配引擎 (Cross-Cultural Adaptation Engine) - 管理后台 */

const API = "/api";
const LANGUAGES = {en:"英语", ja:"日语", ko:"韩语", es:"西班牙语", fr:"法语", ar:"阿拉伯语"};
const CATEGORIES = ["形制","纹样","工艺","礼仪","朝代"];
const REGIONS = ["北美","欧洲","日韩","东南亚","中东","拉美","全球"];
const TABOO_CATS = ["文化冒犯","宗教禁忌","政治敏感","文化挪用"];

// === 安全工具函数 ===

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.content;
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : "";
}

function validateInput(text, minLen = 1, maxLen = 5000, fieldName = "输入") {
  if (!text || typeof text !== "string") {
    return { valid: false, error: fieldName + "不能为空" };
  }
  const trimmed = text.trim();
  if (trimmed.length < minLen) {
    return { valid: false, error: fieldName + "长度不能少于" + minLen + "个字符" };
  }
  if (trimmed.length > maxLen) {
    return { valid: false, error: fieldName + "长度不能超过" + maxLen + "个字符" };
  }
  return { valid: true, error: null, value: trimmed };
}

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

async function safeFetch(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PUT", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      options.headers = options.headers || {};
      options.headers["X-CSRF-Token"] = csrfToken;
    }
  }

  const res = await fetch(url, options);

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
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
    const friendlyMsg = friendlyErrors[res.status] || "HTTP " + res.status;
    throw new Error(err.error || friendlyMsg);
  }

  return res.json();
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
    .replace(/\//g, "&#x2F;");
}

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
    content.innerHTML = "<div class='panel'><p style='color:var(--danger)'>加载失败: " + escapeHtml(e.message) + "</p></div>";
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
    <h2 style="color:var(--accent);margin-bottom:20px">数据看板</h2>
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

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px">
      <div class="panel">
        <h2>趋势分析（近7天）</h2>
        <div style="height:300px">
          <canvas id="trend-chart"></canvas>
        </div>
      </div>
      <div class="panel">
        <h2>模块使用占比</h2>
        <div style="height:300px">
          <canvas id="usage-chart"></canvas>
        </div>
      </div>
    </div>

    <div class="panel"><h2>模块状态</h2>
      <table><tr><th>模块</th><th>优先级</th><th>状态</th><th>API端点</th></tr>
        <tr><td>智能翻译</td><td>P0</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/translate</td></tr>
        <tr><td>合规审核</td><td>P0</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/compliance/audit/text</td></tr>
        <tr><td>视觉识别</td><td>P1</td><td><span class="badge badge-pass">运行中</span></td><td>POST /api/vision/analyze</td></tr>
        <tr><td>知识库</td><td>P1</td><td><span class="badge badge-pass">运行中</span></td><td>GET /api/knowledge</td></tr>
        <tr><td>推荐引擎</td><td>P2</td><td><span class="badge badge-review">开发中</span></td><td>POST /api/recommend</td></tr>
      </table>
    </div>`;
}

async function renderDashboardCharts() {
  try {
    const data = await safeFetch(API + "/dashboard/daily");

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
      Charts.line('trend-chart', ['无数据'], [{ label: '暂无数据', data: [0] }]);
    }

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
      Charts.pie('usage-chart', ['暂无数据'], [1]);
    }
  } catch(e) {
    console.error("加载图表数据失败:", e);
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
    <h2 style="color:var(--accent);margin-bottom:20px">智能翻译模块</h2>

    <div class="panel"><h2>翻译测试</h2>
      <div class="form-row">
        <textarea id="trans-input" placeholder="输入需要翻译的汉服相关文本（中文）..." style="flex:2"></textarea>
        <select id="trans-lang" style="min-width:100px">
          ${Object.entries(LANGUAGES).map(([k,v])=>"<option value=\"" + k + "\">" + v + "</option>").join("")}
        </select>
        <button class="btn btn-primary" onclick="doTranslate()">翻译</button>
      </div>
      <div id="trans-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px;white-space:pre-wrap;font-size:14px"></div>
    </div>

    <div class="panel"><h2>语料库管理 (共<span id="corpus-total">0</span>条)</h2>
      <div class="form-row">
        <input id="corpus-search" placeholder="搜索术语..." oninput="debounce(loadCorpus)()">
        <select id="corpus-cat" onchange="loadCorpus()">
          <option value="">全部分类</option>
          ${CATEGORIES.map(c=>"<option value=\"" + c + "\">" + c + "</option>").join("")}
        </select>
        <button class="btn btn-primary" onclick="showAddTerm()">+ 添加术语</button>
      </div>
      <div id="add-term-form" style="display:none;margin-bottom:16px;padding:16px;border:1px solid var(--border);border-radius:8px">
        <h3>新增术语</h3>
        <div class="form-row">
          <input id="new-term" placeholder="中文术语">
          <select id="new-cat">${CATEGORIES.map(c=>"<option>" + c + "</option>").join("")}</select>
        </div>
        <div class="form-row"><input id="new-def" placeholder="释义（可选）" style="flex:1"></div>
        <div class="form-row"><input id="new-note" placeholder="文化注释（可选）" style="flex:1"></div>
        <div class="form-row" id="new-translations">
          ${Object.entries(LANGUAGES).map(([k,v])=>"<input placeholder=\"" + v + "译文\" data-lang=\"" + k + "\" style=\"flex:1\">").join("")}
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
    const data = await safeFetch(API+"/corpus?page=" + page + "&keyword=" + encodeURIComponent(kw) + "&category=" + encodeURIComponent(cat));
    document.getElementById("corpus-total").textContent = data.total;
    document.getElementById("corpus-table").innerHTML = data.items.map(i => `
      <tr>
        <td>${escapeHtml(i.id)}</td>
        <td><b>${escapeHtml(i.term_zh)}</b></td>
        <td>${escapeHtml(i.category)}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(i.cultural_note||"-")}</td>
        <td><button class="btn btn-sm btn-outline" onclick="editTerm(" + escapeHtml(i.id) + ")">编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTerm(" + escapeHtml(i.id) + ")">删除</button></td>
      </tr>`).join("");
  } catch(e) {
    toast("加载语料库失败: " + e.message, "error");
  }
}

async function doTranslate() {
  const text = document.getElementById("trans-input").value;
  const lang = document.getElementById("trans-lang").value;

  const validation = validateInput(text, 1, 5000, "翻译文本");
  if (!validation.valid) {
    document.getElementById("trans-result").innerHTML = "<span style=\"color:var(--danger)\">" + escapeHtml(validation.error) + "</span>";
    return;
  }

  const btn = document.querySelector("button[onclick='doTranslate()']");
  setButtonLoading(btn, true, "翻译中...");

  try {
    const data = await safeFetch(API+"/translate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: validation.value, target_lang: lang})
    });
    document.getElementById("trans-result").innerHTML =
      "<b>翻译结果：</b>" + escapeHtml(data.translated) + "<br>" +
       "<b>准确率：</b>" + (data.confidence*100).toFixed(0) + "% &nbsp;|&nbsp;" +
       "<b>耗时：</b>" + escapeHtml(String(data.response_time_ms)) + "ms<br>" +
       "<b>匹配术语：</b>" + escapeHtml(data.matched_terms.map(t=>t.term).join(", ")||"无") + "<br>" +
       data.matched_terms.map(t=>"<small>📌 " + escapeHtml(t.term) + ": " + escapeHtml(t.cultural_note||"") + "</small><br>").join("");
  } catch(e) {
    document.getElementById("trans-result").innerHTML = "<span style=\"color:var(--danger)\">翻译失败: " + escapeHtml(e.message) + "</span>";
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

function showEditModal({title, fields, translations, onSave}) {
  let html = "<div class=\"modal-overlay\" id=\"edit-modal\" onclick=\"if(event.target===this)closeModal()\">" +
    "<div class=\"modal-content\"><h2>" + title + "</h2><div class=\"modal-body\">";

  for (const f of fields) {
    if (f.type === "select") {
      html += "<label>" + f.label + "</label><select name=\"" + f.name + "\">" + f.options.map(o=>"<option value=\"" + o + "\" " + (o===f.value?"selected":"") + ">" + o + "</option>").join("") + "</select>";
    } else {
      html += "<label>" + f.label + "</label><input name=\"" + f.name + "\" value=\"" + escapeHtml(f.value) + "\" type=\"" + (f.type||"text") + "\">";
    }
  }

  if (translations) {
    html += "<h3 style=\"margin-top:16px\">多语种翻译</h3>";
    for (const [lang, name] of Object.entries(LANGUAGES)) {
      html += "<label>" + name + " (" + lang + ")</label><input name=\"trans_" + lang + "\" value=\"" + escapeHtml(translations[lang]||"") + "\">";
    }
  }

  html += "</div><div class=\"modal-footer\">" +
    "<button class=\"btn btn-success\" id=\"modal-save-btn\">保存</button>" +
    "<button class=\"btn btn-outline\" onclick=\"closeModal()\">取消</button>" +
  "</div></div></div>";

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
    <h2 style="color:var(--accent);margin-bottom:20px">文化禁忌合规审核</h2>

    <div class="panel"><h2>文本审核测试</h2>
      <div class="form-row">
        <textarea id="audit-text" placeholder="输入待审核文案..." style="flex:2"></textarea>
        <select id="audit-country">
          ${REGIONS.filter(r=>r!="全球").map(r=>"<option>" + r + "</option>").join("")}
          <option value="沙特阿拉伯">沙特阿拉伯</option><option value="印度">印度</option>
        </select>
        <button class="btn btn-primary" onclick="doAuditText()">审核</button>
      </div>
      <div id="audit-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px"></div>
    </div>

    <div class="panel"><h2>规则库管理 (共<span id="rules-total">0</span>条)</h2>
      <div class="form-row">
        <select id="rules-country" onchange="loadRules()"><option value="">全部国家</option></select>
        <select id="rules-cat" onchange="loadRules()"><option value="">全部类别</option>${TABOO_CATS.map(c=>"<option>" + c + "</option>").join("")}</select>
        <button class="btn btn-primary" onclick="showAddRule()">+ 添加规则</button>
      </div>
      <div id="add-rule-form" style="display:none;margin-bottom:16px;padding:16px;border:1px solid var(--border);border-radius:8px">
        <h3>新增规则</h3>
        <div class="form-row">
          <input id="new-rule-country" placeholder="国家（如：沙特阿拉伯）">
          <select id="new-rule-cat">${TABOO_CATS.map(c=>"<option>" + c + "</option>").join("")}</select>
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
    const data = await safeFetch(API+"/compliance/rules?country=" + encodeURIComponent(country) + "&category=" + encodeURIComponent(cat));
    document.getElementById("rules-total").textContent = data.total;
    document.getElementById("rules-table").innerHTML = data.items.map(r => `
      <tr>
        <td>${escapeHtml(r.id)}</td>
        <td>${escapeHtml(r.country)}</td>
        <td>${escapeHtml(r.category)}</td>
        <td><span class="badge " + (r.risk_level==="高风险"?"badge-high":"badge-review") + "">${escapeHtml(r.risk_level)}</span></td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(r.reason)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="editRule(" + escapeHtml(r.id) + ")">编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteRule(" + escapeHtml(r.id) + ")">删除</button></td>
      </tr>`).join("");
    document.getElementById("rules-country").innerHTML = "<option value=\"\">全部国家</option>" +
      [...new Set(data.items.map(r=>r.country))].map(c=>"<option value=\"" + escapeHtml(c) + "\">" + escapeHtml(c) + "</option>").join("");
  } catch(e) {
    toast("加载规则失败: " + e.message, "error");
  }
}

async function doAuditText() {
  const text = document.getElementById("audit-text").value;
  const country = document.getElementById("audit-country").value;

  const validation = validateInput(text, 1, 5000, "审核文本");
  if (!validation.valid) {
    document.getElementById("audit-result").innerHTML = "<span style=\"color:var(--danger)\">" + escapeHtml(validation.error) + "</span>";
    return;
  }

  const btn = document.querySelector("button[onclick='doAuditText()']");
  setButtonLoading(btn, true, "审核中...");

  try {
    const data = await safeFetch(API+"/compliance/audit/text", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: validation.value, country})
    });
    const badge = data.risk_level==="合规" ? "badge-pass" : data.risk_level==="低风险" ? "badge-review" : "badge-high";
    document.getElementById("audit-result").innerHTML = `
      <span class="badge ${badge}">${escapeHtml(data.risk_level)}</span> &nbsp;
      <b>耗时：</b>${escapeHtml(String(data.response_time_ms))}ms<br>
      <b>匹配规则：</b>${escapeHtml(String(data.matched_rules_count))}条<br>
      ${data.reasons.length ? "<b>风险原因：</b>" + escapeHtml(data.reasons.join("；")) + "<br>" : "" } +
      ${data.suggestions.length ? "<b>修改建议：</b>" + escapeHtml(data.suggestions.join("；")) : "" }`;
  } catch(e) {
    document.getElementById("audit-result").innerHTML = "<span style=\"color:var(--danger)\">审核失败: " + escapeHtml(e.message) + "</span>";
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
    <h2 style="color:var(--accent);margin-bottom:20px">视觉识别模块</h2>
    <div class="panel"><h2>汉服识别测试</h2>
      <div class="form-row">
        <input id="vision-path" placeholder="图片路径（如：images/hanfu.jpg）" style="flex:2">
        <button class="btn btn-primary" onclick="doVision()">识别</button>
      </div><div id="vision-result" style="margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px"></div>
    </div>
    <div class="panel"><h2>区域审美库 (共<span id="pref-total">0</span>条)</h2>
      <div id="pref-list"></div>
      <div class="form-row" style="margin-top:12px">
        <select id="pref-region">${REGIONS.map(r=>"<option>" + r + "</option>").join("")}</select>
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
        <button class="btn btn-sm btn-danger" onclick="deletePref(" + escapeHtml(p.id) + ")">×</button>
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

  const pathValidation = validateInput(path, 1, 500, "图片路径");
  if (!pathValidation.valid) {
    document.getElementById("vision-result").innerHTML = "<span style=\"color:var(--danger)\">" + escapeHtml(pathValidation.error) + "</span>";
    return;
  }

  const btn = document.querySelector("button[onclick='doVision()']");
  setButtonLoading(btn, true, "识别中...");

  try {
    const d = await safeFetch(API+"/vision/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({image_path: pathValidation.value})
    });
    document.getElementById("vision-result").innerHTML =
      "<b>朝代：</b>" + escapeHtml(d.dynasty) + " | <b>形制：</b>" + escapeHtml(d.format) + " | <b>色彩：</b>" + escapeHtml(d.colors?.join(", ")||"") + " | <b>纹样：</b>" + escapeHtml(d.patterns?.join(", ")||"") + " | <b>准确率：</b>" + (d.confidence*100).toFixed(0) + "%";
  } catch(e) {
    document.getElementById("vision-result").innerHTML = "<span style=\"color:var(--danger)\">识别失败: " + escapeHtml(e.message) + "</span>";
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 5. 知识库 ===
function renderKnowledge() {
  return "<h2 style=\"color:var(--accent);margin-bottom:20px\">文化解读知识库</h2>" +
    "<div class=\"panel\"><h2>知识检索</h2>" +
      "<div class=\"form-row\">" +
        "<input id=\"kb-search\" placeholder=\"搜索...\" style=\"flex:2\">" +
        "<select id=\"kb-cat\"><option value=\"\">全部分类</option>" + CATEGORIES.map(c=>"<option>" + c + "</option>").join("") + "</select>" +
        "<button class=\"btn btn-primary\" onclick=\"loadKnowledge()\">搜索</button>" +
      "</div>" +
      "<div id=\"kb-list\" style=\"margin-top:12px\"></div>" +
    "</div>" +
    "<div class=\"panel\"><h2>文案生成</h2>" +
      "<div class=\"form-row\">" +
        "<input id=\"copy-topic\" placeholder=\"主题（如：马面裙穿搭）\" style=\"flex:2\">" +
        "<select id=\"copy-region\">" + REGIONS.filter(r=>r!=="全球").map(r=>"<option>" + r + "</option>").join("") + "</select>" +
        "<button class=\"btn btn-primary\" onclick=\"genCopy()\">生成文案</button>" +
      "</div>" +
      "<div id=\"copy-result\" style=\"margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px;white-space:pre-wrap\"></div>" +
    "</div>";
}

async function loadKnowledge() {
  const kw = document.getElementById("kb-search")?.value||"";
  const cat = document.getElementById("kb-cat")?.value||"";
  try {
    const data = await safeFetch(API+"/knowledge?keyword=" + encodeURIComponent(kw) + "&category=" + encodeURIComponent(cat));
    document.getElementById("kb-list").innerHTML = data.items.map(i => `
      <div style="padding:12px;border-bottom:1px solid var(--border)\">
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

  const topicValidation = validateInput(topic, 1, 200, "主题");
  if (!topicValidation.valid) {
    document.getElementById("copy-result").innerHTML = "<span style=\"color:var(--danger)\">" + escapeHtml(topicValidation.error) + "</span>";
    return;
  }

  const btn = document.querySelector("button[onclick='genCopy()']");
  setButtonLoading(btn, true, "生成中...");

  try {
    const d = await safeFetch(API+"/knowledge/generate-copy", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic: topicValidation.value, region})
    });
    document.getElementById("copy-result").innerHTML =
      "<b>文案：</b>" + escapeHtml(d.short_copy) + "<br><b>标签：</b>" + escapeHtml(d.hashtags.join(" ")) + "<br><b>文化注释：</b>" + escapeHtml(d.cultural_note);
  } catch(e) {
    document.getElementById("copy-result").innerHTML = "<span style=\"color:var(--danger)\">生成失败: " + escapeHtml(e.message) + "</span>";
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 6. 推荐 ===
function renderRecommend() {
  return "<h2 style=\"color:var(--accent);margin-bottom:20px\">个性化推荐（P2 - 开发中）</h2>" +
    "<div class=\"panel\"><p style=\"color:var(--text-muted)\">推荐引擎基于用户画像+视觉标签+审美偏好生成内容推荐，匹配准确率目标≥35%。</p>" +
      "<button class=\"btn btn-primary\" style=\"margin-top:12px\" onclick=\"testRecommend()\">运行测试推荐</button>" +
      "<div id=\"rec-result\" style=\"margin-top:12px;padding:12px;background:var(--input-bg);border-radius:6px;min-height:40px\"></div>" +
    "</div>";
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
    document.getElementById("rec-result").innerHTML = "<pre style=\"white-space:pre-wrap\">" + escapeHtml(JSON.stringify(d,null,2)) + "</pre>";
  } catch(e) {
    document.getElementById("rec-result").innerHTML = "<span style=\"color:var(--danger)\">推荐失败: " + escapeHtml(e.message) + "</span>";
  } finally {
    setButtonLoading(btn, false);
  }
}

// === 7. 设置 ===
function renderSettings() {
  return "<h2 style=\"color:var(--accent);margin-bottom:20px\">系统设置</h2>" +

    "<div class=\"panel\"><h2>AI供应商配置</h2>" +
      "<p style=\"color:var(--text-muted);margin-bottom:16px\">配置多个AI供应商，支持OpenAI、DeepSeek、通义千问等。每个供应商可配置独立的API端点、密钥和模型映射。</p>" +

      "<div style=\"display:flex;gap:20px;min-height:400px\">" +
        "<div style=\"flex:0 0 280px;border-right:1px solid var(--border);padding-right:20px\">" +
          "<div style=\"margin-bottom:12px\">" +
            "<button class=\"btn btn-primary\" onclick=\"addProvider()\" style=\"width:100%\">+ 添加供应商</button>" +
          "</div>" +
          "<div id=\"provider-list\" style=\"display:flex;flex-direction:column;gap:8px\">" +
            "<p style=\"color:var(--text-muted);text-align:center;padding:20px\">加载中...</p>" +
          "</div>" +
        "</div>" +

        "<div style=\"flex:1\" id=\"provider-detail\">" +
          "<p style=\"color:var(--text-muted);text-align:center;padding:40px\">请选择或添加供应商</p>" +
        "</div>" +
      "</div>" +
    "</div>" +

    "<div class=\"panel\"><h2>用户管理</h2>" +
      "<div id=\"user-list\"></div>" +
      "<div class=\"form-row\" style=\"margin-top:12px\">" +
        "<input id=\"new-user\" placeholder=\"用户名\">" +
        "<input id=\"new-pw\" type=\"password\" placeholder=\"密码\">" +
        "<select id=\"new-role\"><option>operator</option><option>auditor</option><option>readonly</option></select>" +
        "<button class=\"btn btn-primary btn-sm\" onclick=\"addUser()\">添加用户</button>" +
      "</div>" +
    "</div>" +
    "<div class=\"panel\"><h2>系统信息</h2>" +
      "<p>版本：1.0.0 | Python Flask + SQLite | 默认账户：admin（请联系管理员获取初始密码）</p>" +
    "</div>";
}

// === AI供应商管理 ===

async function loadProviders() {
  try {
    const data = await safeFetch(API + "/ai/providers");
    const listEl = document.getElementById("provider-list");

    const providers = data.data || data.providers || [];

    if (!providers || providers.length === 0) {
      listEl.innerHTML = "<p style=\"color:var(--text-muted);text-align:center;padding:20px\">暂无供应商</p>";
      return;
    }

    listEl.innerHTML = providers.map(p => `
      <div class="provider-item ${p.is_active ? 'active' : ''}"
           data-id="${escapeHtml(p.id)}"
           onclick="selectProvider('${escapeHtml(p.id)}')"
           style="padding:12px;border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all 0.2s;${p.is_active ? 'border-color:var(--accent);background:var(--input-bg);' : ''}">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <b style="font-size:14px">${escapeHtml(p.name)}</b>
            ${p.is_active ? '<span class="badge badge-pass" style="margin-left:6px">激活</span>' : ''}
          </div>
          <span style="color:var(--text-muted);font-size:12px">${escapeHtml(p.provider_type)}</span>
        </div>
        <div style="color:var(--text-muted);font-size:12px;margin-top:4px">${p.endpoints ? p.endpoints.length : 0} 个端点 · 4 层模型</div>
      </div>
    `).join("");

    const activeProvider = providers.find(p => p.is_active);
    if (activeProvider) {
      selectProvider(activeProvider.id);
    }
  } catch(e) {
    toast("加载供应商失败: " + e.message, "error");
    document.getElementById("provider-list").innerHTML =
      "<p style=\"color:var(--danger);text-align:center;padding:20px\">加载失败</p>";
  }
}

async function addProvider() {
  const modal = document.createElement("div");
  modal.id = "add-provider-modal";
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-content" style="max-width:400px">
      <h2>添加供应商</h2>
      <div class="modal-body">
        <label>选择预设</label>
        <select id="new-provider-preset" style="width:100%;margin-bottom:12px">
          <option value="">-- 从预设添加 --</option>
          <option value="openai">OpenAI</option>
          <option value="deepseek">DeepSeek</option>
          <option value="qwen">通义千问</option>
        </select>
        <p style="color:var(--text-muted);font-size:12px;margin-bottom:16px">或自定义：</p>
        <label>供应商 ID</label>
        <input id="new-provider-id" placeholder="如：my-openai" style="width:100%;margin-bottom:8px">
        <label>显示名称</label>
        <input id="new-provider-name" placeholder="如：我的 OpenAI" style="width:100%;margin-bottom:8px">
        <label>类型</label>
        <select id="new-provider-type" style="width:100%">
          <option value="openai">OpenAI 兼容</option>
          <option value="custom">自定义</option>
        </select>
      </div>
      <div class="modal-footer">
        <button class="btn btn-success" onclick="confirmAddProvider()">确认</button>
        <button class="btn btn-outline" onclick="closeProviderModal()">取消</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

async function confirmAddProvider() {
  const preset = document.getElementById("new-provider-preset").value;
  const id = document.getElementById("new-provider-id").value.trim();
  const name = document.getElementById("new-provider-name").value.trim();
  const type = document.getElementById("new-provider-type").value;

  try {
    let body;
    if (preset) {
      body = { provider_type: preset };
    } else {
      if (!id) return toast("请输入供应商 ID", "error");
      if (!name) return toast("请输入显示名称", "error");
      body = { id, name, provider_type: type, endpoints: [] };
    }

    await safeFetch(API + "/ai/providers", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    closeProviderModal();
    toast("供应商创建成功", "success");
    await loadProviders();
  } catch(e) {
    toast("创建失败: " + e.message, "error");
  }
}

function closeProviderModal() {
  const modal = document.getElementById("add-provider-modal");
  if (modal) modal.remove();
}

async function selectProvider(providerId) {
  try {
    const data = await safeFetch(API + "/ai/providers");
    const providers = data.data || data.providers || [];
    const provider = providers.find(p => p.id === providerId);

    if (!provider) {
      return toast("供应商未找到", "error");
    }

    document.querySelectorAll(".provider-item").forEach(el => {
      el.style.borderColor = el.dataset.id === providerId ? "var(--accent)" : "var(--border)";
      el.style.background = el.dataset.id === providerId ? "var(--input-bg)" : "transparent";
    });

    renderProviderDetail(provider);
  } catch(e) {
    toast("加载供应商详情失败: " + e.message, "error");
  }
}

function renderProviderDetail(provider) {
  const detailEl = document.getElementById("provider-detail");
  const endpoint = provider.endpoints && provider.endpoints[0] ? provider.endpoints[0] : null;
  const modelMapping = endpoint ? endpoint.model_mapping : { primary: "", light: "", balanced: "", strongest: "" };

  detailEl.innerHTML = `
    <div style="padding:20px;border:1px solid var(--border);border-radius:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <h3 style="margin:0">${escapeHtml(provider.name)}</h3>
        <div>
          ${provider.is_active
            ? '<span class="badge badge-pass">已激活</span>'
            : '<button class="btn btn-success btn-sm" onclick="activateProvider(\'' + provider.id + '\')">激活</button>'}
          <button class="btn btn-outline btn-sm" onclick="testProvider('${provider.id}')" style="margin-left:8px">测试</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProvider('${provider.id}')" style="margin-left:8px" ${provider.is_active ? 'disabled' : ''}>删除</button>
        </div>
      </div>

      <div class="form-row">
        <label style="min-width:100px">类型</label>
        <input value="${escapeHtml(provider.provider_type)}" disabled style="flex:1;background:var(--input-bg)">
      </div>

      <div class="form-row">
        <label style="min-width:100px">API 端点</label>
        <input id="provider-url-${provider.id}" value="${endpoint ? escapeHtml(endpoint.base_url || '') : ''}"
               placeholder="https://api.example.com/v1" style="flex:1">
      </div>

      <div class="form-row">
        <label style="min-width:100px">API 密钥</label>
        <input id="provider-key-${provider.id}" type="password"
               value="${endpoint ? escapeHtml(endpoint.api_key || '') : ''}"
               placeholder="sk-xxxxxxxx" style="flex:1">
        <span style="color:var(--text-muted);margin-left:8px;font-size:12px">
          ${endpoint && endpoint.api_key ? '已设置' : '未设置'}
        </span>
      </div>

      <h4 style="margin-top:20px;margin-bottom:12px;color:var(--accent)">模型映射</h4>

      <table style="margin-bottom:16px">
        <tr><th style="width:100px">层级</th><th>模型</th><th style="width:180px">用途</th></tr>
        <tr>
          <td><b>Primary</b></td>
          <td><input id="model-primary-${provider.id}" value="${escapeHtml(modelMapping.primary || '')}"
                     placeholder="默认模型" style="width:100%"></td>
          <td style="color:var(--text-muted);font-size:12px">日常使用</td>
        </tr>
        <tr>
          <td><b>Light</b></td>
          <td><input id="model-light-${provider.id}" value="${escapeHtml(modelMapping.light || '')}"
                     placeholder="快速响应" style="width:100%"></td>
          <td style="color:var(--text-muted);font-size:12px">轻量任务</td>
        </tr>
        <tr>
          <td><b>Balanced</b></td>
          <td><input id="model-balanced-${provider.id}" value="${escapeHtml(modelMapping.balanced || '')}"
                     placeholder="性价比" style="width:100%"></td>
          <td style="color:var(--text-muted);font-size:12px">均衡场景</td>
        </tr>
        <tr>
          <td><b>Strongest</b></td>
          <td><input id="model-strongest-${provider.id}" value="${escapeHtml(modelMapping.strongest || '')}"
                     placeholder="最强模型" style="width:100%"></td>
          <td style="color:var(--text-muted);font-size:12px">复杂推理</td>
        </tr>
      </table>

      <div style="margin-top:16px">
        <button class="btn btn-success" onclick="saveProvider('${provider.id}')">保存</button>
        <span id="provider-status-${provider.id}" style="margin-left:12px"></span>
      </div>
    </div>`;
}

async function saveProvider(providerId) {
  const data = {
    base_url: document.getElementById("provider-url-" + providerId).value.trim() || null,
    api_key: document.getElementById("provider-key-" + providerId).value.trim() || null,
    model_mapping: {
      primary: document.getElementById("model-primary-" + providerId).value.trim() || null,
      light: document.getElementById("model-light-" + providerId).value.trim() || null,
      balanced: document.getElementById("model-balanced-" + providerId).value.trim() || null,
      strongest: document.getElementById("model-strongest-" + providerId).value.trim() || null
    }
  };

  const btn = document.querySelector("button[onclick=\"saveProvider('" + providerId + "')\"]");
  setButtonLoading(btn, true, "保存中...");

  try {
    await safeFetch(API + "/ai/providers/" + providerId, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data)
    });
    toast("配置已保存", "success");
    document.getElementById("provider-status-" + providerId).innerHTML =
      '<span style="color:var(--success)">已保存</span>';
    await loadProviders();
  } catch(e) {
    toast("保存失败: " + e.message, "error");
  } finally {
    setButtonLoading(btn, false);
  }
}

async function testProvider(providerId) {
  const statusEl = document.getElementById("provider-status-" + providerId);
  statusEl.innerHTML = '<span style="color:var(--text-muted)">测试中...</span>';

  try {
    const result = await safeFetch(API + "/ai/providers/" + providerId + "/test", {
      method: "POST"
    });

    if (result.success) {
      statusEl.innerHTML = '<span style="color:var(--success)">连接成功</span>';
      toast("连接成功", "success");
    } else {
      statusEl.innerHTML = '<span style="color:var(--danger)">连接失败</span>';
      toast(result.message, "error");
    }
  } catch(e) {
    statusEl.innerHTML = '<span style="color:var(--danger)">连接失败</span>';
    toast("测试失败: " + e.message, "error");
  }
}

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
      ${data.map(u=>"<tr>" +
        "<td>" + escapeHtml(u.id) + "</td>" +
        "<td><b>" + escapeHtml(u.username) + "</b></td>" +
        "<td><span class=\"badge badge-pass\">" + escapeHtml(u.role) + "</span></td>" +
        "<td>" + escapeHtml(u.status) + "</td>" +
        "<td><button class=\"btn btn-sm btn-danger\" onclick=\"deleteUser(" + escapeHtml(u.id) + ")\" " + (u.role==='superadmin'?'disabled':'') + ">删除</button></td>" +
      "</tr>").join("")}
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
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(()=>el.remove(), 3000);
}

// === 初始化 ===
loadPage("dashboard");
