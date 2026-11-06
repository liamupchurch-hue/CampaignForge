"""No silent model fallback: deterministic ComfyUI server mocks."""
import io
import json
import pytest
from comfy_bridge import ComfyLocalClient, make_model_workflow
from comfy_models import ModelChoice
from comfy_studio import choose_connected_model, quality_settings

SDXL = ModelChoice('sd_xl_base_1.0.safetensors','sdxl','sd_xl_base_1.0.safetensors')
Z = ModelChoice('Z-Image Turbo — z_image_turbo_bf16.safetensors','zimage',
                'z_image_turbo_bf16.safetensors',text_encoder='qwen_3_4b.safetensors',vae='ae.safetensors')

class Server:
    def __init__(self, z=False, encoder=True, vae=True):
        self.z, self.encoder, self.vae = z, encoder, vae
        self.queued = []
        self.urls = []
    def open(self, req, timeout):
        self.urls.append(req.full_url)
        if req.full_url.endswith('/prompt'):
            self.queued.append(json.loads(req.data)['prompt'])
            obj={'prompt_id':'1234-5678'}
        else:
            answers={
                '/models/checkpoints':['sd_xl_base_1.0.safetensors'],
                '/models/diffusion_models':['z_image_turbo_bf16.safetensors'] if self.z else [],
                '/models/unet':[],
                '/models/text_encoders':['qwen_3_4b.safetensors'] if self.encoder else [],
                '/models/clip':[],
                '/models/vae':['ae.safetensors'] if self.vae else [],
            }
            obj=answers.get(req.full_url.removeprefix('http://127.0.0.1:8188'),[])
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*args): self.close()
        return Response(json.dumps(obj).encode())

def client(server):
    return ComfyLocalClient(opener=server)

def test_missing_model_does_not_queue_installed_sdxl_instead():
    fake=Server(z=False)
    with pytest.raises(ValueError,match='not installed.*no other model was substituted'):
        client(fake).submit_checked(make_model_workflow(Z,'Dragon',seed=1),Z)
    assert not fake.queued

def test_removed_model_after_connect_is_blocked():
    fake=Server(z=True)
    c=client(fake)
    assert any(x.filename==Z.filename for x in c.available_models())
    fake.z=False
    with pytest.raises(ValueError,match='not installed'):
        c.submit_checked(make_model_workflow(Z,'Dragon',seed=2),Z)
    assert not fake.queued

@pytest.mark.parametrize('encoder,vae',[(False,True),(True,False)])
def test_missing_encoder_or_vae_blocks_queue(encoder,vae):
    fake=Server(z=True,encoder=encoder,vae=vae)
    with pytest.raises(ValueError,match='missing required files'):
        client(fake).submit_checked(make_model_workflow(Z,'Keep',seed=1),Z)
    assert not fake.queued

def test_available_sdxl_queues_exact_checkpoint():
    fake=Server()
    c=client(fake)
    assert c.submit_checked(make_model_workflow(SDXL,'Castle',seed=1),SDXL)=='1234-5678'
    assert fake.queued[0]['15']['inputs']['ckpt_name']==SDXL.filename

def test_available_zimage_queues_exact_diffusion_and_encoder():
    fake=Server(z=True)
    c=client(fake)
    assert c.submit_checked(make_model_workflow(Z,'Village',seed=1),Z)=='1234-5678'
    assert fake.queued[0]['18']['inputs']['unet_name']==Z.filename
    assert fake.queued[0]['15']['inputs']['clip_name']==Z.text_encoder

def test_checkpoint_graph_mismatch_is_not_submitted():
    fake=Server()
    graph=make_model_workflow(SDXL,'Castle',seed=1)
    graph['15']['inputs']['ckpt_name']='wrong.safetensors'
    with pytest.raises(ValueError,match='does not match'):
        client(fake).submit_checked(graph,SDXL)
    assert not fake.urls

def test_encoder_graph_mismatch_is_not_submitted():
    fake=Server(z=True)
    graph=make_model_workflow(Z,'Castle',seed=1)
    graph['15']['inputs']['clip_name']='wrong.safetensors'
    with pytest.raises(ValueError,match='companion files'):
        client(fake).submit_checked(graph,Z)
    assert not fake.urls

def test_reconnect_does_not_substitute_installed_sdxl_for_missing_zimage():
    selected,message=choose_connected_model(Z.display,{SDXL.display:SDXL})
    assert selected==''
    assert 'No replacement' in message

def test_multiple_installed_models_require_explicit_choice():
    selected,message=choose_connected_model('',{SDXL.display:SDXL,Z.display:Z})
    assert selected==''
    assert 'Select' in message

def test_only_one_ready_model_can_autoselect():
    selected,message=choose_connected_model('',{SDXL.display:SDXL})
    assert selected==SDXL.display and not message

def test_preserve_existing_model_choice_during_reconnect():
    selected,message=choose_connected_model(Z.display,{SDXL.display:SDXL,Z.display:Z})
    assert selected==Z.display and not message

def test_sdxl_quality_presets_not_changed():
    assert quality_settings('Low — fast','sdxl')==('512 x 512','15')
    assert quality_settings('Medium — balanced','sdxl')==('768 x 768','25')
    assert quality_settings('High — more detail','sdxl')==('1024 x 1024','35')
