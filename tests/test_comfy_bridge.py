import copy
import io
import json

import pytest

from comfy_bridge import ComfyLocalClient, load_sdxl_preset, make_sdxl_workflow


def test_sdxl_preset_is_the_seven_node_core_workflow():
    d = load_sdxl_preset()
    assert set(d) == {'7', '10', '11', '12', '13', '14', '15'}
    assert {n['class_type'] for n in d.values()} == {
        'CheckpointLoaderSimple', 'CLIPTextEncode', 'EmptyLatentImage',
        'KSampler', 'VAEDecode', 'SaveImage',
    }
    assert d['15']['inputs']['ckpt_name'] == 'sd_xl_base_1.0.safetensors'
    assert d['13']['inputs']['width'] == d['13']['inputs']['height'] == 1024
    assert d['12']['inputs']['sampler_name'] == 'dpmpp_2m'
    assert d['12']['inputs']['scheduler'] == 'karras'
    assert 'DND map that shows' not in d['10']['inputs']['text']


def test_workflow_can_be_customized_without_changing_shared_template():
    before = load_sdxl_preset()
    d = make_sdxl_workflow('A misty forest', width=768, height=1024, seed=123, steps=20)
    assert d['10']['inputs']['text'] == 'A misty forest'
    assert d['13']['inputs']['width'] == 768
    assert d['12']['inputs']['steps'] == 20
    assert d['12']['inputs']['seed'] == 123
    assert load_sdxl_preset() == before


@pytest.mark.parametrize('kwargs', [
    {'width': 300}, {'height': 4096}, {'checkpoint': '../bad.safetensors'},
    {'steps': 0}, {'cfg': 100}, {'seed': -1},
])
def test_workflow_rejects_invalid_options(kwargs):
    with pytest.raises(ValueError):
        make_sdxl_workflow('Valid prompt', **kwargs)


class FakeOpener:
    def __init__(self):
        self.requests = []

    def open(self, req, timeout):
        self.requests.append((req, timeout))
        class Response(io.BytesIO):
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.close()
        if req.full_url.endswith('/models/checkpoints'):
            return Response(json.dumps(['sd_xl_base_1.0.safetensors']).encode())
        if req.full_url.endswith('/system_stats'):
            return Response(json.dumps({'system': 'ok'}).encode())
        if req.full_url.endswith('/prompt'):
            return Response(json.dumps({'prompt_id': 'c7a3-12'}).encode())
        return Response(json.dumps({}).encode())


def test_local_api_requests_only_to_explicit_loopback_server():
    fake = FakeOpener()
    client = ComfyLocalClient('http://127.0.0.1:8188', opener=fake)
    assert client.checkpoints() == ['sd_xl_base_1.0.safetensors']
    assert client.system_stats() == {'system': 'ok'}
    graph = make_sdxl_workflow('Fantasy village', seed=1)
    assert client.submit(graph) == 'c7a3-12'
    submitted = json.loads(fake.requests[-1][0].data)
    assert submitted['prompt'] == graph
    assert fake.requests[-1][0].full_url == 'http://127.0.0.1:8188/prompt'


@pytest.mark.parametrize('url', [
    'https://127.0.0.1:8188', 'http://example.com:8188',
    'http://127.0.0.1:8188/@evil', 'http://127.0.0.1:8188/path',
    'http://localhost', 'http://127.0.0.1:8188?x=1',
])
def test_unapproved_service_url_is_rejected(url):
    with pytest.raises(ValueError):
        ComfyLocalClient(url)
