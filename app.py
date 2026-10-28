"""Tasks REST API (stdlib only). Run: python app.py  (PORT env var, default 8000)."""
import json, os, re, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Store:
    def __init__(self):
        self.items, self.next_id, self.lock = {}, 1, threading.Lock()
    def create(self, data):
        with self.lock:
            t = {"id": self.next_id, "title": data["title"], "done": data.get("done", False)}
            self.items[self.next_id] = t; self.next_id += 1
            return t
    def get(self, i): return self.items.get(i)
    def all(self): return list(self.items.values())
    def update(self, i, data):
        with self.lock:
            t = self.items.get(i)
            if t is None: return None
            t.update(data); return t
    def delete(self, i):
        with self.lock: return self.items.pop(i, None) is not None

def validate(data, partial=False):
    if not isinstance(data, dict): return "body must be a JSON object"
    extra = set(data) - {"title", "done"}
    if extra: return f"unknown field(s): {', '.join(sorted(extra))}"
    if not partial and "title" not in data: return "title is required"
    if "title" in data and (not isinstance(data["title"], str) or not data["title"].strip()
                            or len(data["title"]) > 200):
        return "title must be a non-empty string up to 200 chars"
    if "done" in data and not isinstance(data["done"], bool): return "done must be a boolean"
    return None

def make_handler(store):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def _send(self, code, body=None):
            payload = json.dumps(body).encode() if body is not None else b""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers(); self.wfile.write(payload)
        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > 10_000: raise ValueError("body too large")
            try: return json.loads(self.rfile.read(n) or b"null")
            except json.JSONDecodeError: raise ValueError("invalid JSON")
        def _route(self):
            if self.path == "/health": return "health", None
            if self.path == "/tasks": return "list", None
            m = re.fullmatch(r"/tasks/(\d+)", self.path)
            return ("item", int(m.group(1))) if m else (None, None)
        def _handle(self, method):
            kind, i = self._route()
            try:
                if kind == "health" and method == "GET": return self._send(200, {"status": "ok"})
                if kind == "list":
                    if method == "GET": return self._send(200, store.all())
                    if method == "POST":
                        data = self._body(); err = validate(data)
                        if err: return self._send(400, {"error": err})
                        return self._send(201, store.create(data))
                elif kind == "item":
                    if method == "GET":
                        t = store.get(i)
                        return self._send(200, t) if t else self._send(404, {"error": "not found"})
                    if method in ("PUT", "PATCH"):
                        data = self._body(); err = validate(data, partial=method == "PATCH")
                        if err: return self._send(400, {"error": err})
                        t = store.update(i, data)
                        return self._send(200, t) if t else self._send(404, {"error": "not found"})
                    if method == "DELETE":
                        return self._send(204) if store.delete(i) else self._send(404, {"error": "not found"})
                if kind is None: return self._send(404, {"error": "not found"})
                return self._send(405, {"error": "method not allowed"})
            except ValueError as e:
                self._send(400, {"error": str(e)})
            except Exception:
                self._send(500, {"error": "internal server error"})
        do_GET = lambda s: s._handle("GET")
        do_POST = lambda s: s._handle("POST")
        do_PUT = lambda s: s._handle("PUT")
        do_PATCH = lambda s: s._handle("PATCH")
        do_DELETE = lambda s: s._handle("DELETE")
    return H

def create_server(port=0, store=None):
    return ThreadingHTTPServer(("0.0.0.0", port), make_handler(store or Store()))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"listening on :{port}")
    create_server(port).serve_forever()
