"""Multi-family ComfyUI compatibility tests. No local GPU/model weights required."""
import json
import io
import pytest
from comfy_models import ModelChoice, classify_model, list_model_choices
from comfy_bridge import ComfyLocalClient, make_model_workflow
from comfy_studio import quality_settings, create_image_workflow


def available():
    return list_model_choices(
        ['sd_xl_base_1.0.safetensors', 'v1-5-pruned-emaonly.safetensors'],
        ['z_image_turbo_bf16.safetensors', 'flux1-schnell.safetensors',
         'flux1-dev.safetensors', 'random_video_model.safetensors'],
        ['qwen_3_4b.safetensors', 'clip_l.safetensors', 't5xxl_fp8_e4m3fn.safetensors'],
        ['ae.safetensors'],
    )


def test_supported_model_families_selected_without_mislabeling():
    choices = available()
    assert len(choices) == 5
    assert {c.family for c in choices} == {'sdxl', 'standard', 'zimage', 'flux_schnell', 'flux_dev'}
    assert all(c.ready for c in choices)
    assert classify_model('flux-2.safetensors', folder='diffusion_models') == 'unknown'
    assert classify_model('z_image_base.safetensors', folder='diffusion_models') == 'unknown'
    assert classify_model('flux1-dev.safetensors', folder='checkpoints') == 'unknown'


def test_zimage_workflow_uses_distinct_loader_encoder_and_sampler():
    choice = next(c for c in available() if c.family == 'zimage')
    graph = make_model_workflow(choice, 'An ancient library', negative='no text',
                               width=1024, height=1024, steps=8, cfg=7, seed=112)
    assert graph['18']['class_type'] == 'UNETLoader'
    assert graph['18']['inputs']['unet_name'] == 'z_image_turbo_bf16.safetensors'
    assert graph['15']['class_type'] == 'CLIPLoader'
    assert graph['15']['inputs']['clip_name'] == 'qwen_3_4b.safetensors'
    assert graph['15']['inputs']['type'] == 'lumina2'
    assert graph['16']['class_type'] == 'ModelSamplingAuraFlow'
    assert graph['12']['inputs']['sampler_name'] == 'res_multistep'
    assert graph['12']['inputs']['cfg'] == 1.0
    assert graph['11']['class_type'] == 'ConditioningZeroOut'
    assert graph['7']['inputs']['images'] == ['14', 0]
    assert graph['10']['inputs']['text'] == 'An ancient library'
    assert not any('no text' in str(v) for v in graph.values())  # negative ignored for turbo


@pytest.mark.parametrize('family,steps', [('flux_schnell', 4), ('flux_dev', 20)])
def test_flux_workflow_uses_correct_model_family_and_dual_encoders(family, steps):
    choice = next(c for c in available() if c.family == family)
    graph = make_model_workflow(choice, 'A ruined citadel', width=1024, height=1024,
                                steps=steps, cfg=7, seed=222)
    assert graph['18']['class_type'] == 'UNETLoader'
    assert graph['15']['class_type'] == 'DualCLIPLoader'
    assert graph['15']['inputs']['clip_name1'] == 'clip_l.safetensors'
    assert graph['15']['inputs']['clip_name2'] == 't5xxl_fp8_e4m3fn.safetensors'
    assert graph['10']['class_type'] == 'CLIPTextEncodeFlux'
    assert graph['10']['inputs']['t5xxl'] == 'A ruined citadel'
    assert graph['12']['inputs']['sampler_name'] == 'euler'
    assert graph['12']['inputs']['cfg'] == 1.0
    assert graph['7']['class_type'] == 'SaveImage'


def test_missing_companion_models_are_blocked_before_submission():
    missing = list_model_choices([], ['z_image_turbo_bf16.safetensors', 'flux1-dev.safetensors'], [], [])
    assert len(missing) == 2
    assert all(not model.ready for model in missing)
    assert any('Qwen' in err for err in missing[0].missing)
    assert any('T5XXL' in err for err in missing[1].missing)
    with pytest.raises(ValueError, match='missing'):
        make_model_workflow(missing[0], 'Fantasy scene')


@pytest.mark.parametrize('family', ['sdxl', 'standard', 'zimage', 'flux_dev', 'flux_schnell'])
def test_low_medium_high_presets_for_each_family(family):
    low = quality_settings('Low — fast', family)
    medium = quality_settings('Medium — balanced', family)
    high = quality_settings('High — more detail', family)
    assert low != high
    assert int(low[1]) <= int(high[1])
    assert all(' x ' in x[0] for x in (low, medium, high))


def test_model_choice_is_used_by_image_workflow_ui_translation():
    z = next(c for c in available() if c.family == 'zimage')
    graph = create_image_workflow('Forest', 'text', z.filename, '1024 x 1024', '8', '7', '9', model_choice=z)
    assert graph['18']['inputs']['unet_name'] == z.filename
    assert graph['12']['inputs']['seed'] == 9


class FakeOpener:
    def __init__(self):
        self.urls = []
    def open(self, req, timeout):
        self.urls.append(req.full_url)
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): self.close()
        data = {
            '/models/checkpoints': ['sd_xl_base_1.0.safetensors'],
            '/models/diffusion_models': ['z_image_turbo_bf16.safetensors'],
            '/models/unet': [],
            '/models/text_encoders': ['qwen_3_4b.safetensors'],
            '/models/clip': [],
            '/models/vae': ['ae.safetensors']
        }
        path=req.full_url.removeprefix('http://127.0.0.1:8188')
        if path == '/prompt':
            graph=json.loads(req.data)['prompt']
            assert graph['18']['class_type'] == 'UNETLoader'
            return Response(json.dumps({'prompt_id': 'abc-1'}).encode())
        return Response(json.dumps(data.get(path, {})).encode())


def test_local_api_model_index_and_zimage_submission():
    fake = FakeOpener()
    client = ComfyLocalClient('http://127.0.0.1:8188', opener=fake)
    z = next(c for c in client.available_models() if c.family == 'zimage')
    graph = make_model_workflow(z, 'A hilltop village', seed=1)
    assert client.submit(graph) == 'abc-1'
    assert all(url.startswith('http://127.0.0.1:8188/') for url in fake.urls)


def test_no_unapproved_custom_nodes_allowed():
    client = ComfyLocalClient('http://127.0.0.1:8188')
    with pytest.raises(ValueError, match='approved'):
        client.submit({'1': {'class_type': 'ExecuteShell', 'inputs': {}}})
