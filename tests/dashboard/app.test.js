import { describe, it, expect, beforeEach, vi } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const html = `
  <header class="hero"><p id="project-name"></p>
  <h1 class="metric"><span id="winner-model"></span><span id="winner-value"></span><span id="winner-ci"></span></h1>
  <p id="winner-meta"></p></header>
  <ol id="version-strip"></ol>
  <table id="leaderboard"><tbody></tbody></table>
  <ul id="disproven-wall"></ul>
  <ul id="audit-strip"></ul>`;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixture = JSON.parse(readFileSync(join(__dirname, "fixture.leaderboard.json"), "utf8"));

beforeEach(() => {
  document.body.innerHTML = html;
  globalThis.fetch = vi.fn(async () => ({ ok: true, json: async () => fixture }));
});

describe("dashboard app", () => {
  it("renders the winner from the fixture", async () => {
    const { renderAll } = await import("../../dashboard-template/assets/app.js");
    await renderAll(fixture);
    expect(document.getElementById("winner-model").textContent).toBe("lightgbm");
    expect(document.getElementById("winner-value").textContent).toContain("0.71");
  });
  it("renders a row per run with status class", async () => {
    const { renderAll } = await import("../../dashboard-template/assets/app.js");
    await renderAll(fixture);
    const rows = document.querySelectorAll("#leaderboard tbody tr");
    expect(rows).toHaveLength(2);
    expect(rows[0].className).toContain("status-");
  });
  it("renders disproven cards", async () => {
    const { renderAll } = await import("../../dashboard-template/assets/app.js");
    await renderAll(fixture);
    const cards = document.querySelectorAll("#disproven-wall li");
    expect(cards).toHaveLength(1);
    expect(cards[0].textContent).toContain("RFM");
  });
});
