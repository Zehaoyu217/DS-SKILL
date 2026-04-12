#!/usr/bin/env python3
"""Serve a dashboard directory on a free local port."""
from __future__ import annotations
import argparse, http.server, os, pathlib, signal, socket, socketserver, sys, threading

def pick_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--pidfile", required=True)
    ap.add_argument("--urlfile", required=True)
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()

    root = pathlib.Path(args.dir).resolve()
    os.chdir(root)
    port = args.port or pick_free_port()

    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    pathlib.Path(args.urlfile).write_text(url)
    pathlib.Path(args.pidfile).write_text(str(os.getpid()))

    stop = threading.Event()
    def shutdown(_signum, _frame):
        stop.set()
        threading.Thread(target=httpd.shutdown, daemon=True).start()
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        for f in (args.pidfile, args.urlfile):
            try: os.unlink(f)
            except FileNotFoundError: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
