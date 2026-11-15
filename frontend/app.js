"use strict";

const $ = (id) => document.getElementById(id);
const state = {
  base: localStorage.getItem("ayu_api_base") || $("apiBase").value,
  paperKey: "",
  token: "",
  connectedProviders: [],
  polling: false,
};

$("apiBase").value = state.base;

function setMessage(id, message, bad = false) {
  const node = $(id);
  node.textContent = message || "";
  node.classList.toggle("error", Boolean(bad));
}

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function request(path, options = {}, authenticated = false) {
  if (!state.base) throw new Error("Set the API base URL first.");
  const headers = { ...(options.headers || {}) };
  if (authenticated) Object.assign(headers, authHeaders());
  const response = await fetch(state.base + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function jsonOptions(payload) {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

async function connectApi() {
  state.base = $("apiBase").value.trim().replace(/\/$/, "");
  localStorage.setItem("ayu_api_base", state.base);
  try {
    const health = await request("/health");
    $("status").textContent = health.status === "ok" ? "API online" : "API unavailable";
    $("status").className = "status ok";
  } catch (error) {
    $("status").textContent = error.message;
    $("status").className = "status bad";
  }
}

async function authenticate(mode) {
  const username = $("username").value.trim();
  const password = $("password").value;
  const path = mode === "register" ? "/auth/register" : "/auth/login";
  await request(path, jsonOptions({ username, password }));
  if (mode === "register") {
    setMessage("authMessage", "Account created. Signing in...");
  }
  const login = await request("/auth/login", jsonOptions({ username, password }));
  state.token = login.access_token;
  $("password").value = "";
  $("authStatus").textContent = `Signed in as ${username}`;
  $("logoutButton").hidden = false;
  $("loginButton").hidden = true;
  $("registerButton").hidden = true;
  setMessage("authMessage", "Signed in.");
  await Promise.all([loadProviders(), loadHistory()]);
}

function signOut() {
  state.token = "";
  state.connectedProviders = [];
  $("authStatus").textContent = "Not signed in";
  $("logoutButton").hidden = true;
  $("loginButton").hidden = false;
  $("registerButton").hidden = false;
  $("providerList").textContent = "Sign in to view connected providers.";
  $("providerCount").textContent = "0 connected";
  $("historyList").textContent = "Sign in to load saved results.";
  setMessage("authMessage", "Signed out.");
}

async function loadProviders() {
  if (!state.token) return;
  const data = await request("/providers", {}, true);
  state.connectedProviders = data.providers || [];
  $("providerCount").textContent = `${state.connectedProviders.length} connected`;
  const list = $("providerList");
  list.replaceChildren();
  if (!state.connectedProviders.length) {
    const empty = document.createElement("span");
    empty.className = "hint";
    empty.textContent = "No personal provider keys saved. Server environment keys may still be available.";
    list.append(empty);
    return;
  }
  for (const provider of state.connectedProviders) {
    const item = document.createElement("span");
    item.className = "provider-chip";
    item.textContent = provider;
    list.append(item);
  }
}

async function saveProvider() {
  const provider = $("providerName").value;
  const apiKey = $("providerKey").value.trim();
  if (apiKey.length < 8) throw new Error("Enter a valid provider key.");
  await request(`/providers/${encodeURIComponent(provider)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, api_key: apiKey }),
  }, true);
  $("providerKey").value = "";
  await loadProviders();
  setMessage("providerMessage", `${provider} key saved securely.`);
}

async function removeProvider() {
  const provider = $("providerName").value;
  await request(`/providers/${encodeURIComponent(provider)}`, { method: "DELETE" }, true);
  await loadProviders();
  setMessage("providerMessage", `${provider} key removed.`);
}

function addTextItem(parent, value) {
  if (!value) return;
  const item = document.createElement("li");
  item.textContent = String(value);
  parent.append(item);
}

function renderDecision(result) {
  const decision = result.decision || {};
  $("results").hidden = false;
  $("decisionTitle").textContent = decision.conclusion || "Insufficient evidence";
  $("confidence").textContent = Number.isFinite(decision.confidence)
    ? `${Math.round(decision.confidence * 100)}% confidence`
    : "Confidence unavailable";
  $("decisionStatus").textContent = `Status: ${decision.status || "not provided"} · ${result.provider_count || 0} provider response(s)`;

  const rationale = $("decisionRationale");
  rationale.replaceChildren();
  (decision.rationale || []).forEach((item) => addTextItem(rationale, item));

  const risks = $("riskList");
  risks.replaceChildren();
  (decision.key_risks || []).forEach((item) => addTextItem(risks, item));
  $("riskBlock").hidden = !(decision.key_risks || []).length;
  $("reviewNotice").hidden = !decision.requires_human_review;

  const analyses = result.analyses || [];
  $("analysisCount").textContent = `${analyses.length} provider(s)`;
  const cards = $("agentResults");
  cards.replaceChildren();
  if (!analyses.length) {
    cards.textContent = "No provider responses were returned.";
  }
  for (const analysis of analyses) {
    const card = document.createElement("article");
    card.className = "agent-card";
    const heading = document.createElement("h3");
    heading.textContent = `${analysis.provider || "Provider"} · ${analysis.model || "model"}`;
    const body = document.createElement("pre");
    body.className = "output";
    body.textContent = analysis.content || "No analysis text.";
    card.append(heading, body);
    cards.append(card);
  }

  $("reasoningOutput").textContent = JSON.stringify(result.reasoning || {}, null, 2);
  $("debateOutput").textContent = JSON.stringify(result.debate || {}, null, 2);
  $("results").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function pollAnalysis(jobId) {
  state.polling = true;
  $("analyseButton").disabled = true;
  try {
    for (let attempt = 0; attempt < 180; attempt += 1) {
      const job = await request(`/analysis/${encodeURIComponent(jobId)}`, {}, true);
      $("jobStatus").textContent = `Job ${job.state.toLowerCase()}`;
      if (job.state === "SUCCESS") {
        renderDecision(job.result || {});
        await loadHistory();
        return;
      }
      if (["FAILURE", "REVOKED"].includes(job.state)) {
        throw new Error("Analysis failed. Check provider keys and server logs.");
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }
    $("jobStatus").textContent = "Still running. Use Refresh after a short wait.";
  } finally {
    state.polling = false;
    $("analyseButton").disabled = false;
  }
}

async function startAnalysis(event) {
  event.preventDefault();
  if (!state.token) throw new Error("Sign in before starting an analysis.");
  const question = $("question").value.trim();
  if (!question) throw new Error("Enter a question first.");
  $("jobStatus").textContent = "Submitting...";
  $("results").hidden = true;
  const created = await request("/analysis", jsonOptions({ question }), true);
  $("jobStatus").textContent = `Queued · ${created.job_id}`;
  await pollAnalysis(created.job_id);
}

async function loadHistory() {
  if (!state.token) return;
  const data = await request("/decisions?limit=25", {}, true);
  const list = $("historyList");
  list.replaceChildren();
  if (!data.decisions.length) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = "No saved analyses yet.";
    list.append(empty);
    return;
  }
  for (const item of data.decisions) {
    const row = document.createElement("article");
    row.className = "history-item";
    const question = document.createElement("p");
    question.className = "history-question";
    question.textContent = item.question;
    const meta = document.createElement("span");
    meta.className = "hint";
    const date = item.created_at ? new Date(item.created_at).toLocaleString() : "Date unavailable";
    meta.textContent = `${item.action} · ${Math.round(Number(item.confidence || 0) * 100)}% · ${date}`;
    row.append(question, meta);
    list.append(row);
  }
}

async function refreshPaperPortfolio() {
  if (!state.paperKey) throw new Error("Enter the AYU API key first.");
  const headers = { "X-API-Key": state.paperKey };
  const [metrics, portfolio] = await Promise.all([
    request("/metrics", { headers }),
    request("/portfolio", { headers }),
  ]);
  $("cash").textContent = Number(metrics.cash).toLocaleString();
  $("positionCount").textContent = metrics.position_count;
  $("tradeCount").textContent = metrics.trade_count;
  $("portfolio").textContent = JSON.stringify(portfolio, null, 2);
}

async function connectPaper() {
  state.paperKey = $("apiKey").value;
  await refreshPaperPortfolio();
  setMessage("paperMessage", "Paper portfolio connected.");
}

$("connect").addEventListener("click", () => connectApi().catch((error) => {
  $("status").textContent = error.message;
  $("status").className = "status bad";
}));
$("authForm").addEventListener("submit", (event) => {
  event.preventDefault();
  authenticate("login").catch((error) => setMessage("authMessage", error.message, true));
});
$("registerButton").addEventListener("click", () => {
  authenticate("register").catch((error) => setMessage("authMessage", error.message, true));
});
$("logoutButton").addEventListener("click", signOut);
$("saveProvider").addEventListener("click", () => {
  saveProvider().catch((error) => setMessage("providerMessage", error.message, true));
});
$("removeProvider").addEventListener("click", () => {
  removeProvider().catch((error) => setMessage("providerMessage", error.message, true));
});
$("analysisForm").addEventListener("submit", (event) => {
  startAnalysis(event).catch((error) => {
    $("jobStatus").textContent = error.message;
  });
});
$("refreshHistory").addEventListener("click", () => {
  loadHistory().catch((error) => setMessage("authMessage", error.message, true));
});
$("connectPaper").addEventListener("click", () => {
  connectPaper().catch((error) => setMessage("paperMessage", error.message, true));
});
$("orderForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await request("/paper/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": state.paperKey,
      },
      body: JSON.stringify({
        symbol: $("symbol").value.trim(),
        side: $("side").value,
        quantity: Number($("quantity").value),
        price: Number($("price").value),
      }),
    });
    setMessage("paperMessage", `Paper order recorded: ${result.side} ${result.quantity} ${result.symbol}`);
    await refreshPaperPortfolio();
  } catch (error) {
    setMessage("paperMessage", error.message, true);
  }
});

connectApi();
