"""GUI regression: disappearing model must not trigger an SDXL fallback render."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
import tkinter as tk
import pytest

@pytest.mark.skipif(not os.environ.get('DISPLAY'),reason='Requires X virtual display')
def test_gui_stops_missing_model_and_clears_selection_on_reconnect(monkeypatch):
    try:
        probe=tk.Tk();probe.withdraw();probe.destroy()
    except tk.TclError:
        pytest.skip('No available graphical display')
    from app import CampaignForge
    from comfy_studio import open_comfy_studio
    from tkinter import messagebox

    state={'z_installed':True,'submitted':0}
    class Handler(BaseHTTPRequestHandler):
        def reply(self,obj):
            data=json.dumps(obj).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        def do_GET(self):
            if self.path=='/system_stats': return self.reply({'system':{'os':'test'}})
            if self.path.startswith('/models/'):
                return self.reply({
                    '/models/checkpoints':['sd_xl_base_1.0.safetensors'],
                    '/models/diffusion_models':['z_image_turbo_bf16.safetensors'] if state['z_installed'] else [],
                    '/models/text_encoders':['qwen_3_4b.safetensors'],
                    '/models/vae':['ae.safetensors'],
                }.get(self.path,[]))
            self.send_error(404)
        def do_POST(self):
            state['submitted']+=1
            self.reply({'prompt_id':'should-never-queue'})
        def log_message(self,*a):pass

    http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=http.serve_forever,daemon=True).start()
    monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs:True)
    errors=[]
    monkeypatch.setattr(messagebox,'showerror',lambda *args,**kwargs:errors.append(args))
    app=studio=None
    try:
        app=CampaignForge()
        studio=open_comfy_studio(app)
        studio.address.set(f'http://127.0.0.1:{http.server_port}')
        studio.connect()
        deadline=time.monotonic()+7
        while time.monotonic()<deadline and not studio.model_options:
            app.update();time.sleep(.02)
        label=next((n for n in studio.model_options if n.startswith('Z-Image Turbo')),'')
        assert label
        studio.checkpoint.set(label)
        studio.on_checkpoint_changed()
        assert studio.generate_button.instate(['!disabled'])
        state['z_installed']=False
        studio.generate()
        deadline=time.monotonic()+7
        while time.monotonic()<deadline and not errors:
            app.update();time.sleep(.02)
        assert errors,studio.status.get()
        assert 'not installed' in studio.status.get()
        assert state['submitted']==0
        studio.connect()
        deadline=time.monotonic()+7
        while time.monotonic()<deadline and studio._connecting:
            app.update();time.sleep(.02)
        assert studio.checkpoint.get()==''
        assert studio.generate_button.instate(['disabled'])
        assert 'No replacement' in studio.model_status.get()
    finally:
        if studio is not None and studio.winfo_exists(): studio.close()
        if app is not None and app.winfo_exists(): app.destroy()
        http.shutdown()
