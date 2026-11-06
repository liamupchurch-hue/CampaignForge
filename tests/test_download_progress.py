"""Streaming Ollama pull tests. No network access to public services, no download."""
import json
import unittest
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from threading import Thread
from unittest.mock import patch
from oracle_providers import download_model

class FakePull(BaseHTTPRequestHandler):
    ready = False
    fail = False
    def log_message(self, *args):
        pass
    def do_GET(self):
        blob = json.dumps({'models': [{'name':'gemma3:4b'}] if self.ready else []}).encode()
        self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(blob)
    def do_POST(self):
        n=int(self.headers['Content-Length']); req=json.loads(self.rfile.read(n))
        assert req == {'model':'gemma3:4b', 'stream': True}, req
        self.send_response(200); self.send_header('Content-Type','application/x-ndjson'); self.end_headers()
        events=[{'status':'pulling manifest'}, {'status':'downloading layer', 'total':1000, 'completed':250},
                {'status':'downloading layer', 'total':1000, 'completed':1000}, {'status':'verifying sha256 digest'}]
        if self.fail:
            events.append({'error':'test failure'})
        else:
            FakePull.ready=True; events.append({'status':'success'})
        for item in events:
            self.wfile.write((json.dumps(item)+'\n').encode())
        self.wfile.flush()

class DownloadProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1',0),FakePull)
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)
    def setUp(self):
        FakePull.ready=False; FakePull.fail=False
    def test_stream_percentage_and_completion(self):
        seen=[]
        with patch('oracle_providers.ollama_executable',return_value='ollama.exe'):
            result=download_model('gemma3:4b',progress_callback=seen.append,base_url=self.url)
        self.assertEqual([e['percent'] for e in seen if e['percent'] is not None],[25.0,100.0])
        self.assertEqual(seen[-1]['status'],'success')
        self.assertIn('Ready',result)
    def test_error_surfaces(self):
        FakePull.fail=True
        with patch('oracle_providers.ollama_executable',return_value='ollama.exe'):
            with self.assertRaisesRegex(RuntimeError,'test failure'):
                download_model('gemma3:4b',base_url=self.url)
    def test_bad_model_guard(self):
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            download_model('../custom',base_url=self.url)
if __name__=='__main__': unittest.main()
