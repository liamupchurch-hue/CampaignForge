"""GUI integration with a fake local Z-Image ComfyUI API; no GPU/model downloads."""
import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
import tkinter as tk
import pytest
from PIL import Image


@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='Requires X virtual display')
def test_gui_select_zimage_generate_and_preview(monkeypatch, tmp_path):
    try:
        r = tk.Tk(); r.withdraw(); r.destroy()
    except tk.TclError:
        pytest.skip('No available GUI display')
    from app import CampaignForge
    from comfy_studio import open_comfy_studio
    from tkinter import messagebox
    from forge_library import Archive
    image = io.BytesIO(); Image.new('RGB',(128,128),'green').save(image, 'PNG')
    png = image.getvalue()
    job = '01234567-89ab-cdef-0123-456789abcdef'
    submitted = []
    class Handler(BaseHTTPRequestHandler):
        def reply(self, content):
            data=json.dumps(content).encode(); self.send_response(200)
            self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(data)
        def do_GET(self):
            if self.path=='/system_stats': return self.reply({'system':{'os':'nt'}})
            if self.path.startswith('/models/'):
                return self.reply({
                    '/models/checkpoints': ['sd_xl_base_1.0.safetensors'],
                    '/models/diffusion_models': ['z_image_turbo_bf16.safetensors'],
                    '/models/text_encoders': ['qwen_3_4b.safetensors'],
                    '/models/vae': ['ae.safetensors'],
                }.get(self.path, []))
            if self.path.startswith('/history/'):
                return self.reply({job:{'status':{'status_str':'success','completed':True},
                    'outputs': {'7': {'images': [{'filename':'result.png','subfolder':'','type':'output'}]}}}})
            if self.path.startswith('/view?'):
                self.send_response(200);self.send_header('Content-Type','image/png');self.end_headers();self.wfile.write(png);return
            self.send_error(404)
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            submitted.append(body)
            self.reply({'prompt_id':job})
        def log_message(self,*args): pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs:True)
    app=studio=None
    try:
        app=CampaignForge();app.archive=Archive(tmp_path/'Archives')
        studio=open_comfy_studio(app)
        studio.address.set(f'http://127.0.0.1:{server.server_port}')
        studio.connect()
        deadline=time.time()+8
        while time.time()<deadline and not studio.model_options:
            app.update();time.sleep(.02)
        label=next((name for name in studio.model_options if name.startswith('Z-Image Turbo')),'')
        assert label, studio.connection_note.get()
        studio.checkpoint.set(label);studio.on_checkpoint_changed()
        assert studio.generate_button.instate(['!disabled'])
        assert studio.model_family=='zimage'
        assert studio.steps.get()=='9'  # High preset selected by default
        studio.generate()
        deadline=time.time()+8
        while time.time()<deadline and studio.selected_image is None:
            app.update();time.sleep(.02)
        assert submitted, studio.status.get()
        graph=submitted[0]['prompt']
        assert graph['18']['inputs']['unet_name']=='z_image_turbo_bf16.safetensors'
        assert graph['15']['inputs']['clip_name']=='qwen_3_4b.safetensors'
        assert studio.selected_image.size==(128,128)
    finally:
        if studio and studio.winfo_exists(): studio.close()
        if app and app.winfo_exists(): app.destroy()
        server.shutdown()
