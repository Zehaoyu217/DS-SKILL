import socket, subprocess, sys, time, urllib.request, signal, os, pathlib
SK = pathlib.Path(__file__).resolve().parents[1]

def test_pick_free_port_returns_bindable_port():
    from server.serve_dashboard import pick_free_port
    p = pick_free_port()
    s = socket.socket(); s.bind(("127.0.0.1", p)); s.close()

def test_server_starts_and_serves_index(tmp_path):
    d = tmp_path/"dash"; d.mkdir()
    (d/"index.html").write_text("<!doctype html><title>ok</title>")
    proc = subprocess.Popen([sys.executable, str(SK/"server/serve_dashboard.py"),
                             "--dir", str(d), "--pidfile", str(tmp_path/"pid"),
                             "--urlfile", str(tmp_path/"url")])
    try:
        for _ in range(50):
            if (tmp_path/"url").exists(): break
            time.sleep(0.1)
        url = (tmp_path/"url").read_text().strip()
        html = urllib.request.urlopen(url, timeout=2).read().decode()
        assert "ok" in html
    finally:
        proc.send_signal(signal.SIGINT); proc.wait(timeout=3)
