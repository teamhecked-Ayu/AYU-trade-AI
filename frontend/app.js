const $ = (id) => document.getElementById(id);
let token = localStorage.getItem("ayuai_token") || "";
let pollTimer;

function base() { return $("apiBase").value.replace(/\/$/, ""); }
async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = "Bearer " + token;
  const response = await fetch(base() + path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}
function showDashboard() {
  $("authCard").hidden = true; $("dashboard").hidden = false;
  checkHealth(); loadProviders();
}
async function checkHealth() {
  try { const data = await api("/health"); $("health").textContent = data.status || "Online"; }
  catch { $("health").textContent = "Offline"; }
}
async function loadProviders() {
  try { const data = await api("/providers"); $("providers").textContent = (data.providers || []).length + " connected"; }
  catch { $("providers").textContent = "Unavailable"; }
}
async function authenticate(path) {
  $("authMessage").textContent = "";
  try {
    const data = await api(path, { method:"POST", body:JSON.stringify({username:$("username").value,password:$("password").value}) });
    if (path.includes("login")) { token = data.access_token; localStorage.setItem("ayuai_token", token); showDashboard(); }
    else $("authMessage").textContent = "Registered. Log in now.";
  } catch (error) { $("authMessage").textContent = error.message; }
}
$("login").onclick = () => authenticate("/auth/login");
$("register").onclick = () => authenticate("/auth/register");
$("logout").onclick = () => { localStorage.removeItem("ayuai_token"); token=""; clearInterval(pollTimer); location.reload(); };
$("analyze").onclick = async () => {
  const question = $("question").value.trim(); if (!question) return;
  $("analysisMessage").textContent = "Submitting…";
  try {
    const job = await api("/analysis", {method:"POST", body:JSON.stringify({question})});
    $("jobState").textContent = job.state; $("analysisMessage").textContent = "Analysis queued.";
    poll(job.job_id);
  } catch (error) { $("analysisMessage").textContent = error.message; }
};
async function streamJob(jobId) {
  clearInterval(pollTimer);
  try {
    const response = await fetch(base() + "/analysis/" + encodeURIComponent(jobId) + "/events", {
      headers: { Authorization: "Bearer " + token }
    });
    if (!response.ok || !response.body) throw new Error("Live updates unavailable");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();
      for (const event of events) {
        const line = event.split("\n").find(x => x.startsWith("data: "));
        if (!line) continue;
        const job = JSON.parse(line.slice(6));
        $("jobState").textContent = job.state;
        if (job.result !== null && job.result !== undefined) {
          $("result").textContent = typeof job.result === "string" ? job.result : JSON.stringify(job.result, null, 2);
        }
      }
    }
  } catch (error) {
    $("analysisMessage").textContent = "Live connection lost. Checking final status…";
    try {
      const job = await api("/analysis/" + encodeURIComponent(jobId));
      $("jobState").textContent = job.state;
      if (job.result !== null && job.result !== undefined) $("result").textContent = JSON.stringify(job.result, null, 2);
    } catch (_) {}
  }
}
if (token) showDashboard();