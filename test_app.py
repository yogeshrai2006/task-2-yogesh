import json, threading, unittest, urllib.request, urllib.error
import app

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = app.create_server(0)
        cls.base = f"http://127.0.0.1:{cls.srv.server_address[1]}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def req(self, method, path, body=None, raw=None):
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        r = urllib.request.Request(self.base + path, data=data, method=method,
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r) as resp:
                b = resp.read(); return resp.status, json.loads(b) if b else None
        except urllib.error.HTTPError as e:
            b = e.read(); return e.code, json.loads(b) if b else None

    def test_health(self): self.assertEqual(self.req("GET", "/health"), (200, {"status": "ok"}))
    def test_crud(self):
        c, t = self.req("POST", "/tasks", {"title": "write"}); self.assertEqual(c, 201)
        self.assertFalse(t["done"]); tid = t["id"]
        self.assertEqual(self.req("GET", f"/tasks/{tid}")[1]["title"], "write")
        c, t = self.req("PATCH", f"/tasks/{tid}", {"done": True}); self.assertTrue(t["done"])
        c, t = self.req("PUT", f"/tasks/{tid}", {"title": "new"}); self.assertEqual(t["title"], "new")
        self.assertIn(tid, [x["id"] for x in self.req("GET", "/tasks")[1]])
        self.assertEqual(self.req("DELETE", f"/tasks/{tid}")[0], 204)
        self.assertEqual(self.req("GET", f"/tasks/{tid}")[0], 404)
    def test_validation(self):
        for body in [{}, {"title": ""}, {"title": 5}, {"title": "x", "done": "yes"},
                     {"title": "x", "hack": 1}, {"title": "x" * 201}, [1]]:
            self.assertEqual(self.req("POST", "/tasks", body)[0], 400, body)
    def test_invalid_json(self): self.assertEqual(self.req("POST", "/tasks", raw=b"{bad")[0], 400)
    def test_404s(self):
        self.assertEqual(self.req("GET", "/nope")[0], 404)
        self.assertEqual(self.req("GET", "/tasks/99999")[0], 404)
        self.assertEqual(self.req("PATCH", "/tasks/99999", {"done": True})[0], 404)
        self.assertEqual(self.req("DELETE", "/tasks/99999")[0], 404)
    def test_method_not_allowed(self): self.assertEqual(self.req("DELETE", "/tasks")[0], 405)
    def test_ids_not_reused(self):
        a = self.req("POST", "/tasks", {"title": "a"})[1]["id"]
        self.req("DELETE", f"/tasks/{a}")
        b = self.req("POST", "/tasks", {"title": "b"})[1]["id"]
        self.assertGreater(b, a)

if __name__ == "__main__":
    unittest.main()
