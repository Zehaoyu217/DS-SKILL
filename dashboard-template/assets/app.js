const DATA_URL = "data/leaderboard.json";

export async function fetchData(url = DATA_URL) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url}: ${r.status}`);
  return r.json();
}

function bestRun(runs, direction) {
  const valid = runs.filter(r => r.status === "valid");
  if (!valid.length) return null;
  const cmp = direction === "max" ? (a,b) => b.cv_mean - a.cv_mean : (a,b) => a.cv_mean - b.cv_mean;
  return [...valid].sort(cmp)[0];
}

function fmt(x, n=3) { return (x == null || isNaN(x)) ? "—" : Number(x).toFixed(n); }

function renderHero(d) {
  document.getElementById("project-name").textContent = d.project;
  const w = bestRun(d.runs, d.primary_metric.direction);
  if (!w) return;
  document.getElementById("winner-model").textContent = w.model;
  document.getElementById("winner-value").textContent = fmt(w.cv_mean);
  document.getElementById("winner-ci").textContent = `CI95 [${fmt(w.cv_ci95[0])}, ${fmt(w.cv_ci95[1])}]`;
  document.getElementById("winner-meta").textContent =
    `${d.primary_metric.name} · lift vs baseline ${fmt(w.lift_vs_baseline)} · v${w.v} · ${w.created_at.slice(0,10)}`;
}

function renderTimeline(d) {
  const strip = document.getElementById("version-strip");
  const versions = [...new Set(d.runs.map(r => r.v))].sort((a,b)=>a-b);
  strip.innerHTML = versions.map(v =>
    `<li>v${v}${v === d.current_state.v ? ` · ${d.current_state.phase}` : ""}</li>`).join("");
}

function renderBoard(d) {
  const tbody = document.querySelector("#leaderboard tbody");
  const rows = [...d.runs].sort((a,b) => b.created_at.localeCompare(a.created_at));
  tbody.innerHTML = rows.map(r => `
    <tr class="status-${r.status}">
      <td>${r.id}</td><td>${r.v}</td><td><strong>${r.model}</strong></td>
      <td>${fmt(r.cv_mean)}</td>
      <td>[${fmt(r.cv_ci95[0])}, ${fmt(r.cv_ci95[1])}]</td>
      <td>${fmt(r.lift_vs_baseline)}</td>
      <td>${r.features_used}</td>
      <td>${r.created_at.slice(0,10)}</td>
      <td>${r.status}</td>
    </tr>`).join("");
}

function renderDisproven(d) {
  const ul = document.getElementById("disproven-wall");
  ul.innerHTML = d.disproven.map(x => `
    <li><h3>${x.claim}</h3><p>${x.lesson}</p><p><small>${x.date.slice(0,10)} · ${x.id}</small></p></li>`).join("");
}

function renderAudits(d) {
  const ul = document.getElementById("audit-strip");
  ul.innerHTML = d.events.map(e =>
    `<li><span class="chip ${e.type === "leakage-found" ? "critical" : "pass"}">${e.type}</span>
         <code>v${e.v}</code> <a href="${e.ref}">${e.ref}</a>
         <small>${e.at.slice(0,16).replace("T"," ")}</small></li>`).join("");
}

export async function renderAll(data) {
  renderHero(data);
  renderTimeline(data);
  renderBoard(data);
  renderDisproven(data);
  renderAudits(data);
  try {
    const { renderMetricChart } = await import("./charts.js");
    renderMetricChart(data);
  } catch (_) { /* chart optional in tests */ }
}

async function tick() {
  try { renderAll(await fetchData()); } catch (e) { console.error(e); }
}

if (typeof window !== "undefined" && !window.__DS_TEST__) {
  tick();
  setInterval(tick, 3000);
}
