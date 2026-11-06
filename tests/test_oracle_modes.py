"""Network-free tests: fake Ollama on loopback, not a live model or installer."""
import json
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from unittest.mock import patch

from campaign_data import new_campaign
from oracle_providers import LOCAL_MODELS, has_model, ollama_models, consult_local, organize_local, download_model

class FakeOllama(BaseHTTPRequestHandler):
    seen = []
    def log_message(self, *args):
        pass
    def do_GET(self):
        body = json.dumps({"models": [{"name": "gemma3:4b"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        req = json.loads(self.rfile.read(n))
        FakeOllama.seen.append(req)
        if req.get("format") == "json":
            value = json.dumps({"values": {"title": {"value": "Hollowford", "confidence": "explicit", "source": "first page"}},
              "entries": [{"category": "NPC", "title": "The Keeper", "content": "Keeps the gates.",
                           "gm_only": False, "location": "page 2", "confidence": "review"}]})
        else:
            value = "Consider an old pact, but do not change the lore without approval."
        body = json.dumps({"message": {"content": value}, "done": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
        cls.server_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=2)

    def setUp(self):
        FakeOllama.seen.clear()

    def test_local_model_discovery(self):
        self.assertEqual(ollama_models(self.server_url), ["gemma3:4b"])
        self.assertTrue(has_model(["gemma3:4b"], "gemma3:4b"))
        self.assertFalse(has_model(["gemma3:4b"], "gemma3:12b"))

    def test_local_consultation_does_not_include_refs_without_permission(self):
        data = new_campaign()
        data["references"] = [{"name": "notes", "text": "PRIVATE-REFERENCE-STRING"}]
        result = consult_local(data, "Help my campaign", base_url=self.server_url)
        self.assertIn("old pact", result)
        sent = json.dumps(FakeOllama.seen[-1])
        self.assertNotIn("PRIVATE-REFERENCE-STRING", sent)
        consult_local(data, "Help", include_refs=True, base_url=self.server_url)
        self.assertIn("PRIVATE-REFERENCE-STRING", json.dumps(FakeOllama.seen[-1]))
        self.assertFalse(FakeOllama.seen[-1]["stream"])

    def test_local_structured_recovery_preserves_archive(self):
        doc = {"name": "Hollowford.pdf", "chars": 46, "warnings": [], "text": "The Keeper keeps the gates. A secret passage."}
        proposal = organize_local(doc, base_url=self.server_url)
        self.assertEqual(proposal["values"]["title"]["value"], "Hollowford")
        self.assertEqual(len(proposal["entries"]), 2)
        self.assertIn("secret passage", proposal["entries"][-1]["content"])
        self.assertEqual(FakeOllama.seen[-1]["format"], "json")

    def test_oversized_local_import_auto_chunks(self):
        doc = {"name": "long.pdf", "chars": 35000, "warnings": [], "text": "Chapter 1\n" + "x" * 34990}
        reports = []
        proposal = organize_local(doc, base_url=self.server_url, progress_callback=lambda *args: reports.append(args))
        self.assertEqual(len(FakeOllama.seen), 4)
        self.assertEqual([r[2] for r in reports], ["processing", "completed"] * 4)
        self.assertEqual(proposal["source_text"], doc["text"])
        self.assertEqual(sum(e["title"] == "Original manuscript — unedited archive" for e in proposal["entries"]), 1)
        self.assertIn("passages", proposal["method"])
        self.assertIn("Keeps the gates", "".join(e["content"] for e in proposal["entries"]))

    def test_cancelled_import_never_contacts_ollama(self):
        from threading import Event
        stop = Event(); stop.set()
        doc = {"name": "long.pdf", "chars": 40000, "warnings": [], "text": "A" * 40000}
        with self.assertRaisesRegex(InterruptedError, "cancelled"):
            organize_local(doc, base_url=self.server_url, cancel_event=stop)
        self.assertEqual(FakeOllama.seen, [])

    def test_model_whitelist_blocks_unknown(self):
        from oracle_providers import ollama_chat
        with self.assertRaisesRegex(ValueError, "supported"):
            ollama_chat([{"role": "user", "content": "hi"}], model="whatever", base_url=self.server_url)

    def test_download_fails_without_ollama(self):
        with patch("oracle_providers.ollama_executable", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "Install Ollama"):
                download_model()

if __name__ == "__main__":
    unittest.main()
