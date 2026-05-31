#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


VERSION = "0.1.0"


def _json_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _normalize_path(path: str) -> str:
    return "/" + path.strip().lstrip("/")


def _transcribe_payload() -> dict[str, object]:
    return {
        "text": "大家准备一下，我们开始这局 我先去中路看视野 可以，等我技能好了再开",
        "segments": [
            {
                "start": 0,
                "end": 3000,
                "text": "大家准备一下，我们开始这局",
                "speaker": "Speaker 1",
            },
            {
                "start": 3000,
                "end": 7000,
                "text": "我先去中路看视野",
                "speaker": "Speaker 2",
            },
            {
                "start": 7000,
                "end": 12000,
                "text": "可以，等我技能好了再开",
                "speaker": "Speaker 1",
            },
        ],
    }


class FakeFunASRHandler(BaseHTTPRequestHandler):
    server_version = f"FakeFunASR/{VERSION}"

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json({"status": "ok", "service": "fake-funasr", "version": VERSION})
            return
        self._send_json({"detail": "not found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        allowed_paths = {
            _normalize_path(os.getenv("FUNASR_HTTP_TRANSCRIBE_PATH", "/recognize")),
            "/recognize",
            "/asr",
        }
        if self.path not in allowed_paths:
            self._send_json({"detail": "not found"}, status=404)
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_json({"detail": "expected multipart/form-data"}, status=400)
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        if content_length <= 0:
            self._send_json({"detail": "missing audio payload"}, status=400)
            return

        # Consume the request body so clients can reuse the connection cleanly.
        self.rfile.read(content_length)
        self._send_json(_transcribe_payload())

    def log_message(self, format: str, *args: object) -> None:
        if os.getenv("FAKE_FUNASR_QUIET", "0") == "1":
            return
        super().log_message(format, *args)

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a fake FunASR HTTP server.")
    parser.add_argument("--host", default=os.getenv("FAKE_FUNASR_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.getenv("FAKE_FUNASR_PORT", "10095")), type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), FakeFunASRHandler)
    print(f"fake-funasr listening on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
