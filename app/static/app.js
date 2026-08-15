const state = { history: [], busy: false };

const byId = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "请求失败");
  return body;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function refreshStatus() {
  try {
    const data = await api("/api/status");
    byId("modelName").textContent = data.model;
    byId("llmState").textContent = data.llmReady ? "已配置" : "未配置 Key";
    byId("documentCount").textContent = data.knowledgeBase.documentCount;
    byId("healthDot").classList.add("ready");
  } catch {
    byId("llmState").textContent = "服务不可用";
    byId("healthDot").classList.remove("ready");
  }
}

function renderSearchResults(results) {
  const target = byId("searchResults");
  if (!results.length) {
    target.className = "search-results empty";
    target.textContent = "没有命中本地文档";
    return;
  }
  target.className = "search-results";
  target.innerHTML = results.map((item) => `
    <div class="result">
      <strong>${escapeHtml(item.path)} <em>${Math.round(item.score * 100)}%</em></strong>
      <p>${escapeHtml(item.excerpt)}</p>
    </div>
  `).join("");
}

function addMessage(role, content, sources = [], knowledgeWrite = null) {
  const article = document.createElement("article");
  article.className = `message ${role}`;
  const avatar = role === "assistant" ? '<div class="avatar">D</div>' : "";
  const sourceHtml = sources.length ? `
    <div class="sources">${sources.map((item) => `<span class="source-chip">${escapeHtml(item.path)}</span>`).join("")}</div>
  ` : "";
  const writeLabels = {
    created: "已沉淀",
    replaced: "已覆盖",
    confirmation_required: "等待覆盖确认",
    needs_input: "需要补充信息",
    needs_path: "需要目标路径",
    rejected: "写入被拒绝",
  };
  const writeHtml = knowledgeWrite ? `
    <div class="knowledge-write ${escapeHtml(knowledgeWrite.status)}">
      <span>${escapeHtml(writeLabels[knowledgeWrite.status] || "知识写入")}</span>
      ${knowledgeWrite.path ? `<code>${escapeHtml(knowledgeWrite.path)}</code>` : ""}
    </div>
  ` : "";
  article.innerHTML = `${avatar}<div class="bubble"><p>${escapeHtml(content)}</p>${sourceHtml}${writeHtml}</div>`;
  byId("messages").appendChild(article);
  article.scrollIntoView({ behavior: "smooth", block: "end" });
  return article;
}

function setBusy(value, label = "就绪") {
  state.busy = value;
  byId("sendButton").disabled = value;
  byId("questionInput").disabled = value;
  byId("requestState").textContent = label;
}

byId("reindexButton").addEventListener("click", async () => {
  const button = byId("reindexButton");
  button.disabled = true;
  button.textContent = "正在重建…";
  try {
    const data = await api("/api/index", { method: "POST" });
    button.textContent = `完成：${data.indexed} 篇`;
    await refreshStatus();
  } catch (error) {
    button.textContent = error.message;
  } finally {
    setTimeout(() => {
      button.disabled = false;
      button.textContent = "重建知识库索引";
    }, 1400);
  }
});

byId("searchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = byId("searchInput").value.trim();
  if (!query) return;
  byId("searchResults").className = "search-results empty";
  byId("searchResults").textContent = "检索中…";
  try {
    const data = await api("/api/search", { method: "POST", body: JSON.stringify({ query, topK: 5 }) });
    renderSearchResults(data.results);
  } catch (error) {
    byId("searchResults").textContent = error.message;
  }
});

byId("chatForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (state.busy) return;
  const input = byId("questionInput");
  const question = input.value.trim();
  if (!question) return;

  const priorHistory = [...state.history];
  addMessage("user", question);
  state.history.push({ role: "user", content: question });
  input.value = "";
  input.style.height = "auto";
  setBusy(true, "正在处理…");
  const typing = addMessage("assistant", "思考中…");
  typing.querySelector(".bubble").classList.add("typing");

  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ question, history: priorHistory }),
    });
    typing.remove();
    addMessage("assistant", data.answer, data.sources, data.knowledgeWrite);
    state.history.push({ role: "assistant", content: data.answer });
    byId("usageState").textContent = `缓存 token：${data.usage.cachedTokens} · 输入：${data.usage.inputTokens}`;
    if (["created", "replaced"].includes(data.knowledgeWrite?.status)) {
      await refreshStatus();
    }
    setBusy(false, `完成 · ${data.model}`);
  } catch (error) {
    typing.remove();
    addMessage("assistant", error.message);
    state.history.pop();
    setBusy(false, "请求失败");
  }
});

byId("questionInput").addEventListener("input", (event) => {
  event.target.style.height = "auto";
  event.target.style.height = `${Math.min(event.target.scrollHeight, 180)}px`;
});

byId("questionInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    byId("chatForm").requestSubmit();
  }
});

byId("clearButton").addEventListener("click", () => {
  state.history = [];
  byId("messages").innerHTML = "";
  addMessage("assistant", "对话已清空。下一条问题会开启新的上下文。");
  byId("usageState").textContent = "缓存 token：—";
});

refreshStatus();
