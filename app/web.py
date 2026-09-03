"""Local website for the Philippine Cheque Writer (same templates and PCHC rules)."""

from __future__ import annotations

import json
import sys
import webbrowser
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WEB_DIR = ROOT / "web"

from app.pchc import (
    alignment_sample,
    format_amount_figures,
    format_amount_words,
    format_date_boxed,
    format_manual_amount_words,
    format_payee,
    parse_amount,
)
from app.templates_loader import bank_choices, load_bank

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".ico": "image/x-icon",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: object) -> None:
        self._send(code, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/banks":
            banks = [{"id": bank_id, "name": name} for bank_id, name in bank_choices()]
            self._json(200, {"banks": banks, "default": "landbank"})
            return
        if path.startswith("/api/template/"):
            bank_id = path.rsplit("/", 1)[-1]
            from urllib.parse import parse_qs

            variant = parse_qs(parsed.query).get("type", ["personal"])[0]
            self._json(200, load_bank(bank_id, variant))
            return
        if path in ("/", "/index.html"):
            path = "/index.html"
        file_path = (WEB_DIR / path.lstrip("/")).resolve()
        if WEB_DIR.resolve() not in file_path.parents and file_path != WEB_DIR.resolve():
            self._json(403, {"error": "Forbidden"})
            return
        if not file_path.is_file():
            self._json(404, {"error": "Not found"})
            return
        data = file_path.read_bytes()
        self._send(200, data, MIME.get(file_path.suffix, "application/octet-stream"))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/format":
            self._json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._json(400, {"error": "Invalid JSON"})
            return
        if payload.get("alignment"):
            self._json(200, alignment_sample())
            return
        try:
            issue = _parse_date(str(payload.get("date") or ""))
            pad = bool(payload.get("pad", True))
            amount_raw = str(payload.get("amount") or "").strip()
            amount = parse_amount(amount_raw) if amount_raw else None
            words_mode = str(payload.get("words_mode") or "auto")
            if words_mode == "manual":
                words = format_manual_amount_words(str(payload.get("amount_words") or ""), pad)
            else:
                words = format_amount_words(amount, pad) if amount is not None else ""
            fields = {
                "date": format_date_boxed(issue),
                "payee": format_payee(str(payload.get("payee") or ""), pad),
                "amount_figures": format_amount_figures(amount) if amount is not None else "",
                "amount_words": words,
                "memo": str(payload.get("memo") or "").strip(),
            }
            self._json(200, fields)
        except ValueError as exc:
            self._json(400, {"error": str(exc)})


def _parse_date(value: str) -> date:
    value = value.strip()
    if not value:
        return date.today()
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError("Date must be YYYY-MM-DD or MM-DD-YYYY")


def main(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/"
    print(f"Philippine Cheque Writer website: {url}")
    print("Print from the browser at 100% (Actual size). Press Ctrl+C to stop.")
    try:
        webbrowser.open(url)
    except OSError:
        pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
