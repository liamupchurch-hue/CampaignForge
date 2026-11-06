"""Regression checks for the optional ComfyUI Art Studio (no GPU required)."""
import io
from pathlib import Path
import pytest
from PIL import Image
from comfy_bridge import ComfyLocalClient
from comfy_studio import PRESETS, create_image_workflow, validate_generated_image


def test_studio_has_four_presets_and_positive_negative_fields():
    assert {'Map background', 'Landscape / location', 'Character portrait', 'Cartography prop'} <= set(PRESETS)
    graph = create_image_workflow('A ruined tower in a swamp',
        'watermarks, signatures', 'sd_xl_base_1.0.safetensors', '1024 x 768', '25', '7', '123')
    assert graph['10']['inputs']['text'] == 'A ruined tower in a swamp'
    assert graph['11']['inputs']['text'] == 'watermarks, signatures'
    assert (graph['13']['inputs']['width'], graph['13']['inputs']['height']) == (1024, 768)
    assert graph['12']['inputs']['seed'] == 123
    assert graph['15']['inputs']['ckpt_name'] == 'sd_xl_base_1.0.safetensors'


@pytest.mark.parametrize('resolution,step,cfg,seed', [
    ('400 x 400', '25', '7', ''), ('1024x1024', 'notanumber', '7', ''),
    ('1024x1024', '25', 'N/A', ''), ('1024x1024', '25', '7', '-1'),
])
def test_invalid_studio_options_cannot_reach_server(resolution, step, cfg, seed):
    with pytest.raises(ValueError):
        create_image_workflow('Fantasy castle', '', 'sd_xl_base_1.0.safetensors', resolution, step, cfg, seed)


def test_image_record_progress_and_result(monkeypatch):
    client = ComfyLocalClient()
    monkeypatch.setattr(client, 'history', lambda prompt_id: {})
    assert client.image_output('abcd-1234') is None
    monkeypatch.setattr(client, 'history', lambda prompt_id: {prompt_id: {
        'status': {'status_str': 'success', 'completed': True},
        'outputs': {'7': {'images': [{'filename': 'CampaignForge_00001_.png', 'subfolder': '', 'type': 'output'}]}}
    }})
    assert client.image_output('abcd-1234')['filename'] == 'CampaignForge_00001_.png'


def test_failed_comfy_job_raises_clear_error(monkeypatch):
    client = ComfyLocalClient()
    monkeypatch.setattr(client, 'history', lambda prompt_id: {prompt_id: {
        'status': {'status_str': 'error', 'completed': False,
                   'messages': [['execution_error', {'exception_message': 'Out of memory'}]]},
        'outputs': {}
    }})
    with pytest.raises(RuntimeError, match='Out of memory'):
        client.image_output('abcd-1234')


@pytest.mark.parametrize('name,subfolder,kind', [
    ('../escape.png', '', 'output'), ('asset\\escape.png', '', 'output'),
    ('ok.png', '../outside', 'output'), ('ok.png', 'foo\\..\\bar', 'output'),
    ('ok.png', '', 'input'), ('bad.exe', '', 'output'),
])
def test_refuse_unsafe_comfy_results(name, subfolder, kind):
    client = ComfyLocalClient()
    with pytest.raises(ValueError):
        client.download_image({'filename': name, 'subfolder': subfolder, 'type': kind})


class FakeOpener:
    def __init__(self, payload):
        self.payload = payload
        self.urls = []
    def open(self, req, timeout):
        self.urls.append(req.full_url)
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        return Response(self.payload)


def test_generated_image_is_loaded_from_output_path_only():
    raw = io.BytesIO()
    Image.new('RGB', (256, 256), (123, 67, 42)).save(raw, format='PNG')
    fake = FakeOpener(raw.getvalue())
    client = ComfyLocalClient('http://127.0.0.1:8188', opener=fake)
    result = client.download_image({'filename': 'sdxl_0001.png', 'subfolder': '', 'type': 'output'})
    assert result == raw.getvalue()
    assert fake.urls == ['http://127.0.0.1:8188/view?filename=sdxl_0001.png&subfolder=&type=output']
    assert validate_generated_image(result).size == (256, 256)


def test_invalid_image_bytes_do_not_enter_archives():
    with pytest.raises((ValueError, OSError, SyntaxError)):
        validate_generated_image(b'not a png')
    with pytest.raises(ValueError):
        validate_generated_image(b'')


def test_app_has_button_and_build_includes_workflow_asset():
    root = Path(__file__).resolve().parent.parent
    app = (root/'app.py').read_text(encoding='utf-8')
    script = (root/'build_windows.bat').read_text(encoding='utf-8')
    assert "text='Generate Image (ComfyUI)'" in app
    assert 'from comfy_studio import open_comfy_studio' in app
    assert '--add-data "assets;assets"' in script
    assert (root/'assets/workflows/sdxl_base_api.json').is_file()
