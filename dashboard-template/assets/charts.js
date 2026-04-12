export function renderMetricChart(data) {
  const el = document.getElementById("metric-chart");
  if (!el || typeof uPlot === "undefined") return;
  const valid = data.runs.filter(r => r.status === "valid")
    .sort((a,b)=>a.created_at.localeCompare(b.created_at));
  const xs = valid.map(r => new Date(r.created_at).getTime()/1000);
  const ys = valid.map(r => r.cv_mean);
  const lo = valid.map(r => r.cv_ci95[0]);
  const hi = valid.map(r => r.cv_ci95[1]);
  const opts = {
    width: el.clientWidth || 800,
    height: 320,
    series: [
      {},
      { label: data.primary_metric.name, stroke: "#7fc8ff" },
      { label: "CI low",  stroke: "#7fc8ff55" },
      { label: "CI high", stroke: "#7fc8ff55" }
    ],
    scales: { x: { time: true } }
  };
  el.innerHTML = "";
  new uPlot(opts, [xs, ys, lo, hi], el);
}
