import json, subprocess, sys, pathlib, shutil, time, signal, urllib.request
SK = pathlib.Path(__file__).resolve().parents[1]

def test_workspace_init_and_dashboard_serves_fixture(tmp_path):
    ws = tmp_path/"ds-workspace"; (ws/"dashboard").mkdir(parents=True)
    # Seed dashboard from template
    for p in (SK/"dashboard-template").rglob("*"):
        rel = p.relative_to(SK/"dashboard-template")
        dst = ws/"dashboard"/rel
        if p.is_dir(): dst.mkdir(parents=True, exist_ok=True)
        else: dst.write_bytes(p.read_bytes())
    # Seed leaderboard with a minimal valid fixture
    (ws/"dashboard/data").mkdir(parents=True, exist_ok=True)
    fixture = json.loads((SK/"tests/dashboard/fixture.leaderboard.json").read_text())
    (ws/"dashboard/data/leaderboard.json").write_text(json.dumps(fixture))
    # Start server
    pidfile = tmp_path/"pid"; urlfile = tmp_path/"url"
    proc = subprocess.Popen([sys.executable, str(SK/"server/serve_dashboard.py"),
                             "--dir", str(ws/"dashboard"),
                             "--pidfile", str(pidfile), "--urlfile", str(urlfile)])
    try:
        for _ in range(50):
            if urlfile.exists(): break
            time.sleep(0.1)
        url = urlfile.read_text().strip()
        assert "DS Leaderboard" in urllib.request.urlopen(url, timeout=2).read().decode()
        assert urllib.request.urlopen(url + "data/leaderboard.json", timeout=2).status == 200
    finally:
        proc.send_signal(signal.SIGINT); proc.wait(timeout=3)
