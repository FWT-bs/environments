import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from env import TicTacToeEnv


EPISODES: Dict[str, TicTacToeEnv] = {}


class BenchAnythingHandler(BaseHTTPRequestHandler):
    server_version = "TicTacToeBench/1.0"

    def do_OPTIONS(self) -> None:
        self._send_json({})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok"})
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self) -> None:
        body = self._read_json()
        if body is None:
            self._send_json({"error": "request body must be valid JSON"}, status=400)
            return

        if self.path == "/reset":
            self._handle_reset(body)
            return
        if self.path == "/step":
            self._handle_step(body)
            return
        if self.path == "/close":
            self._handle_close(body)
            return

        self._send_json({"error": "not found"}, status=404)

    def _handle_reset(self, body: Dict[str, Any]) -> None:
        episode_id = str(body.get("episode_id") or "default")
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        env = TicTacToeEnv()
        observation = env.reset(seed=body.get("seed"), **params)
        EPISODES[episode_id] = env
        self._send_json(
            {
                "data": observation,
                "content_type": "application/json",
                "system_prompt": None,
            }
        )

    def _handle_step(self, body: Dict[str, Any]) -> None:
        episode_id = str(body.get("episode_id") or "default")
        env = EPISODES.get(episode_id)
        if env is None:
            self._send_json({"error": f"unknown episode_id {episode_id!r}; call /reset first"}, status=400)
            return

        result = env.step(body.get("action"))
        self._send_json(
            {
                "observation": {
                    "data": result.observation,
                    "content_type": "application/json",
                },
                "reward": result.reward,
                "terminated": result.terminated,
                "truncated": result.truncated,
                "info": result.info,
                "system_prompt": result.system_prompt,
            }
        )

    def _handle_close(self, body: Dict[str, Any]) -> None:
        episode_id = str(body.get("episode_id") or "default")
        EPISODES.pop(episode_id, None)
        self._send_json({})

    def _read_json(self) -> Optional[Dict[str, Any]]:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None
        return body if isinstance(body, dict) else None

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the tic-tac-toe environment.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), BenchAnythingHandler)
    print(f"Serving tic-tac-toe environment on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
