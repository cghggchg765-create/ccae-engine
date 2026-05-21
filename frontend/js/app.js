/* CCAE管理后台主逻辑 */

const API = "/api";
const LANGUAGES = {en:"英语", ja:"日语", ko:"韩语", es:"西班牙语", fr:"法语", ar:"阿拉伯语"};
const CATEGORIES = ["形制","纹样","工艺","礼仪","朝代"];
const REGIONS = ["北美","欧洲","日韩","东南亚","中东","拉美","全球"];
const TABOO_CATS = ["文化冒犯","宗教禁忌","政治敏感","文化挪用"];

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
      case "dashboard": content.innerHTML = await renderDashboard(); break;
      case "translate": content.innerHTML = renderTranslate(); await loadCorpus(); break;
      case "compliance": content.innerHTML = renderCompliance(); await loadRules(); break;
      case "vision": content.innerHTML = renderVision(); await loadPreferences(); break;
      case "knowledge": content.innerHTML = renderKnowledge(); await loadKnowledge(); break;
      case "recommend": content.innerHTML = renderRecommend(); break;
      case "settings": content.innerHTML = renderSettings(); await loadUsers(); break;
    }
  } catch(e) {
    content.innerHTML = `<div class='panel'><p style='color:var(--danger)'>加载失败: ${e.message}</p></div>`;
  }
}

// === 1. 数据看板 ===
async function renderDashboard() {
  let stats = {};
  try { const r = await fetch(API+"/dashboard/overview"); stats = await r.json(); } catch(e) {}
  
  return `
    <h2 style="color:var(--accent);margin-bottom:20px">📊 数据看板</h2>
    <div class="stats-grid">
      <div class="stat-card"><div class="label">语料库术语</div><div class="value">${stats.corpus_count||0}</div></div>
      <div class="stat-card"><div class="label">合规规则</div><div class="value">${stats.rules_count||0}</div></div>
      <div class="stat-card"><div class="label">30天翻译量</div><div class="value">${stats.monthly_translations||0}</div></div>
      <div class="stat-card"><div class="label">翻译准确率</div><div class="value success">${(stats.avg_translation_confidence*100||0).toFixed(0)}%</div></div>
      <div class="stat-card"><div class="label">审核通过率</div><div class="value success">${(stats.pass_rate*100||0).toFixed(0)}%</div></div>
      <div class="stat-card"><div class="label">高风险率</div><div class="value danger">${(stats.high_risk_rate*100||0).toFixed(0)}%</div></div>
      <div class="stat-card"><div class="label">视觉识别量</div><div class="value">${stats.vision_analyses||0}</div></div>
      <div class="stat-card"><div class="label">知识库条目</div><div class="value">${stats.knowledge_entries||0}</div></div>
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
        <input id="corpus-search" placeholder="搜索术语..." oninput="loadCorpus()">
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
  const res = await fetch(`${API}/corpus?page=${page}&keyword=${kw}&category=${cat}`);
  const data = await res.json();
  document.getElementById("corpus-total").textContent = data.total;
  document.getElementById("corpus-table").innerHTML = data.items.map(i => `
    <tr>
      <td>${i.id}</td><td><b>${i.term_zh}</b></td><td>${i.category}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${i.cultural_note||"-"}</td>
      <td><button class="btn btn-sm btn-outline" onclick="editTerm(${i.id})">编辑</button>
          <button class="btn btn-sm btn-danger" onclick="deleteTerm(${i.id})">删除</button></td>
    </tr>`).join("");
}

async function doTranslate() {
  const text = document.getElementById("trans-input").value;
  const lang = document.getElementById("trans-lang").value;
  if(!text) return;
  const res = await fetch(API+"/translate", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text, target_lang:lang})});
  const data = await res.json();
  document.getElementById("trans-result").innerHTML = 
    `<b>翻译结果：</b>${data.translated}<br>
     <b>准确率：</b>${(data.confidence*100).toFixed(0)}% &nbsp;|&nbsp;
     <b>耗时：</b>${data.response_time_ms}ms<br>
     <b>匹配术语：</b>${data.matched_terms.map(t=>t.term).join(", ")||"无"}<br>
     ${data.matched_terms.map(t=>`<small>📌 ${t.term}: ${t.cultural_note}</small><br>`).join("")}`;
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
  if(!term_zh || !category) return toast("请填写术语和分类","error");
  
  await fetch(API+"/corpus", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({term_zh, category, definition, cultural_note, translations})});
  document.getElementById("add-term-form").style.display="none";
  loadCorpus(); toast("术语添加成功","success");
}

async function deleteTerm(id) { if(confirm("确认删除？")){ await fetch(API+"/corpus/"+id, {method:"DELETE"}); loadCorpus(); toast("已删除","success"); } }

// ---- 术语编辑弹窗 ----
async function editTerm(id) {
  const res = await fetch(API+"/corpus?page=1&per_page=100");
  const data = await res.json();
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
      await fetch(API+"/corpus/"+id, {method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      loadCorpus(); toast("术语更新成功","success");
      closeModal();
    }
  });
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

function escapeHtml(str) {
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
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
  const res = await fetch(`${API}/compliance/rules?country=${country}&category=${cat}`);
  const data = await res.json();
  document.getElementById("rules-total").textContent = data.total;
  document.getElementById("rules-table").innerHTML = data.items.map(r => `
    <tr><td>${r.id}</td><td>${r.country}</td><td>${r.category}</td>
      <td><span class="badge ${r.risk_level==='高风险'?'badge-high':'badge-review'}">${r.risk_level}</span></td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.reason}</td>
      <td><button class="btn btn-sm btn-outline" onclick="editRule(${r.id})">编辑</button>
          <button class="btn btn-sm btn-danger" onclick="deleteRule(${r.id})">删除</button></td></tr>`).join("");
  // 填充国家下拉
  document.getElementById("rules-country").innerHTML = '<option value="">全部国家</option>'+
    [...new Set(data.items.map(r=>r.country))].map(c=>`<option value="${c}">${c}</option>`).join("");
}

async function doAuditText() {
  const text = document.getElementById("audit-text").value;
  const country = document.getElementById("audit-country").value;
  if(!text) return;
  const res = await fetch(API+"/compliance/audit/text", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text, country})});
  const data = await res.json();
  const badge = data.risk_level==="合规" ? "badge-pass" : data.risk_level==="低风险" ? "badge-review" : "badge-high";
  document.getElementById("audit-result").innerHTML = `
    <span class="badge ${badge}">${data.risk_level}</span> &nbsp;
    <b>耗时：</b>${data.response_time_ms}ms<br>
    <b>匹配规则：</b>${data.matched_rules_count}条<br>
    ${data.reasons.length ? `<b>⚠️ 风险原因：</b>${data.reasons.join("；")}<br>`:""}
    ${data.suggestions.length ? `<b>💡 修改建议：</b>${data.suggestions.join("；")}`:""}`;
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
  if(!data.country||!data.category||!data.keywords.length) return toast("请填写必填字段","error");
  await fetch(API+"/compliance/rules", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  document.getElementById("add-rule-form").style.display="none";
  loadRules(); toast("规则添加成功","success");
}
async function deleteRule(id) { if(confirm("确认删除？")){ await fetch(API+"/compliance/rules/"+id,{method:"DELETE"}); loadRules(); } }

async function editRule(id) {
  const res = await fetch(API+"/compliance/rules?page=1&per_page=100");
  const data = await res.json();
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
      await fetch(API+"/compliance/rules/"+id, {method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
      loadRules(); toast("规则更新成功","success");
      closeModal();
    }
  });
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
  const res = await fetch(API+"/vision/preferences"); const data = await res.json();
  document.getElementById("pref-total").textContent = data.length;
  document.getElementById("pref-list").innerHTML = data.map(p => `
    <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border);align-items:center">
      <span><b>${p.region}</b> → ${p.category}: ${p.preference} <small style="color:var(--text-muted)">权重${p.weight}</small></span>
      <button class="btn btn-sm btn-danger" onclick="deletePref(${p.id})">×</button>
    </div>`).join("");
}
async function addPreference() {
  const d = { region: document.getElementById("pref-region").value, category: document.getElementById("pref-cat").value, preference: document.getElementById("pref-value").value };
  if(!d.preference) return;
  await fetch(API+"/vision/preferences", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});
  loadPreferences(); toast("添加成功","success");
}
async function deletePref(id) { await fetch(API+"/vision/preferences/"+id,{method:"DELETE"}); loadPreferences(); }
async function doVision() {
  const path = document.getElementById("vision-path").value;
  if(!path) return;
  const res = await fetch(API+"/vision/analyze", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image_path:path})});
  const d = await res.json();
  document.getElementById("vision-result").innerHTML = `<b>朝代：</b>${d.dynasty} | <b>形制：</b>${d.format} | <b>色彩：</b>${d.colors?.join(", ")} | <b>纹样：</b>${d.patterns?.join(", ")} | <b>准确率：</b>${(d.confidence*100).toFixed(0)}%`;
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
  const kw = document.getElementById("kb-search")?.value||""; const cat = document.getElementById("kb-cat")?.value||"";
  const res = await fetch(`${API}/knowledge?keyword=${kw}&category=${cat}`); const data = await res.json();
  document.getElementById("kb-list").innerHTML = data.items.map(i => `
    <div style="padding:12px;border-bottom:1px solid var(--border)">
      <b>${i.title_zh}</b> <span class="badge badge-pass">${i.category}</span>
      <p style="color:var(--text-muted);margin-top:4px">${(i.content_zh||"").substring(0,150)}...</p>
    </div>`).join("") || "<p style='color:var(--text-muted)'>无结果</p>";
}
async function genCopy() {
  const topic = document.getElementById("copy-topic").value; const region = document.getElementById("copy-region").value;
  if(!topic) return;
  const res = await fetch(API+"/knowledge/generate-copy", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic, region})});
  const d = await res.json();
  document.getElementById("copy-result").innerHTML = `<b>📝 文案：</b>${d.short_copy}<br><b>🏷️ 标签：</b>${d.hashtags.join(" ")}<br><b>📌 文化注释：</b>${d.cultural_note}`;
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
  const res = await fetch(API+"/recommend", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    user_profile:{age:"25-34",interests:["fashion","culture"],region:"北美"},
    visual_tags:{colors:["红色","金色"],patterns:["云纹"]},region:"北美"})});
  const d = await res.json();
  document.getElementById("rec-result").innerHTML = `<pre style="white-space:pre-wrap">${JSON.stringify(d,null,2)}</pre>`;
}

// === 7. 设置 ===
function renderSettings() {
  return `<h2 style="color:var(--accent);margin-bottom:20px">⚙️ 系统设置</h2>
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
      <p>版本：1.0.0 | Python Flask + SQLite | 默认账户：admin / admin123</p>
    </div>`;
}
async function loadUsers() {
  const res = await fetch(API+"/users"); const data = await res.json();
  document.getElementById("user-list").innerHTML = `
    <table><tr><th>ID</th><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr>
    ${data.map(u=>`<tr><td>${u.id}</td><td><b>${u.username}</b></td><td><span class="badge badge-pass">${u.role}</span></td><td>${u.status}</td><td><button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id})" ${u.role==='superadmin'?'disabled':''}>删除</button></td></tr>`).join("")}
    </table>`;
}
async function addUser() {
  const d = { username: document.getElementById("new-user").value, password: document.getElementById("new-pw").value, role: document.getElementById("new-role").value };
  if(!d.username||!d.password) return toast("请填写用户名和密码","error");
  await fetch(API+"/users",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(d)});
  loadUsers(); toast("用户创建成功","success");
}
async function deleteUser(id) { if(confirm("确认删除？")){ await fetch(API+"/users/"+id,{method:"DELETE"}); loadUsers(); } }

// === 工具函数 ===
function toast(msg, type="success") {
  const el = document.createElement("div"); el.className=`toast ${type}`; el.textContent=msg; document.body.appendChild(el);
  setTimeout(()=>el.remove(), 3000);
}

// === 初始化 ===
loadPage("dashboard");
