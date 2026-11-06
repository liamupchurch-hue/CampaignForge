"""Optional graphical smoke test; exercises the local queue protocol without ComfyUI/GPU.

Run with Xvfb on Linux. GitHub headless CI skips this and still runs unit checks.
"""
import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
import tkinter as tk

import pytest
from PIL import Image

from forge_library import Archive


@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Requires a graphical display')
def test_studio_local_mock_comfyui_end_to_end(monkeypatch, tmp_path):
    try:
        probe = tk.Tk()
        probe.withdraw()
        probe.destroy()
    except tk.TclError:
        pytest.skip('Display variable set but no actual X server available')
    from app import CampaignForge
    from comfy_studio import open_comfy_studio
    from tkinter import messagebox

    picture = io.BytesIO()
    Image.new('RGB',(256,256),'blue').save(picture, 'PNG')
    image_bytes = picture.getvalue()
    job_id = '12345678-1234-1234-1234-123456789abc'
    seen = {'submitted': False}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/system_stats':
                self.reply({'system': {'os': 'nt'}})
            elif self.path == '/models/checkpoints':
                self.reply(['sd_xl_base_1.0.safetensors'])
            elif self.path.startswith('/history/'):
                self.reply({job_id: {'status': {'status_str': 'success', 'completed': True},
                        'outputs': {'7': {'images': [{'filename':'saved.png','type':'output','subfolder':''}]}}}})
            elif self.path.startswith('/view?'):
                self.send_response(200)
                self.send_header('Content-Type','image/png')
                self.end_headers()
                self.wfile.write(image_bytes)
            else:
                self.send_error(404)
        def do_POST(self):
            if self.path != '/prompt':
                self.send_error(404);return
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            assert body['prompt']['15']['inputs']['ckpt_name'] == 'sd_xl_base_1.0.safetensors'
            assert body['prompt']['10']['inputs']['text'] == 'A cozy fantasy tavern'
            seen['submitted'] = True
            self.reply({'prompt_id':job_id})
        def reply(self, obj):
            blob=json.dumps(obj).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)
        def log_message(self, *args): pass

    http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=http.serve_forever,daemon=True).start()
    monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs: True)
    app=None
    studio=None
    try:
        app=CampaignForge()
        app.archive=Archive(tmp_path/'Archives')
        studio=open_comfy_studio(app)
        studio.address.set(f'http://127.0.0.1:{http.server_port}')
        studio.connect()
        end=time.time()+8
        while time.time()<end and studio.client is None:
            app.update()
            time.sleep(.02)
        assert studio.client is not None, studio.connection_note.get()
        assert studio.checkpoint.get() == 'sd_xl_base_1.0.safetensors'
        studio.positive.delete('1.0','end')
        studio.positive.insert('1.0','A cozy fantasy tavern')
        studio.generate()
        end=time.time()+8
        while time.time()<end and studio.selected_image is None:
            app.update()
            time.sleep(.02)
        assert seen['submitted']
        assert studio.selected_image is not None, studio.status.get()
        studio.add_to_archives()
        assert len(app.archive.list(app.data['project_id'])) == 1
    finally:
        if studio is not None and studio.winfo_exists(): studio.close()
        if app is not None and app.winfo_exists(): app.destroy()
        http.shutdown()
