"""Minimal, opt-in, loopback-only ComfyUI workflow adapter.

This module does not start ComfyUI, download models, submit jobs automatically,
or enable in-app generation by itself. It provides building blocks for an
explicitly user-triggered future UI. No third-party packages are required.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from urllib import parse, request
from uuid import uuid4


SDXL_TEMPLATE = Path(__file__).resolve().parent / 'assets' / 'workflows' / 'sdxl_base_api.json'
ALLOWED_CLASSES = {
    'CheckpointLoaderSimple', 'CLIPTextEncode', 'EmptyLatentImage',
    'KSampler', 'VAEDecode', 'SaveImage',
}


def load_sdxl_preset() -> dict:
    """Return a private, mutable copy of the proven seven-node SDXL graph."""
    data = json.loads(SDXL_TEMPLATE.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or len(data) != 7:
        raise ValueError('Bundled SDXL preset is malformed.')
    for node in data.values():
        if not isinstance(node, dict) or node.get('class_type') not in ALLOWED_CLASSES:
            raise ValueError('Bundled SDXL preset contains an unexpected node.')
    for node in data.values():
        for val in node['inputs'].values():
            if isinstance(val, list) and len(val) == 2 and isinstance(val[0], str):
                if val[0] not in data or not isinstance(val[1], int):
                    raise ValueError('Bundled SDXL preset contains an invalid node reference.')
    return data


def make_sdxl_workflow(prompt: str, *, checkpoint: str = 'sd_xl_base_1.0.safetensors',
                       negative: str = 'text, letters, words, watermark, low quality',
                       width: int = 1024, height: int = 1024, steps: int = 25,
                       cfg: float = 7.0, seed: int | None = None) -> dict:
    """Create a ready-to-submit SDXL API workflow, without modifying the preset."""
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 6000:
        raise ValueError('Enter a prompt of 1–6000 characters.')
    if not isinstance(negative, str) or len(negative) > 3000:
        raise ValueError('Negative prompt is too long.')
    if not isinstance(checkpoint, str) or not checkpoint.lower().endswith('.safetensors') or '/' in checkpoint or '\\' in checkpoint:
        raise ValueError('Choose an installed .safetensors checkpoint filename.')
    for label, dim in [('width', width), ('height', height)]:
        if type(dim) is not int or dim < 256 or dim > 2048 or dim % 64:
            raise ValueError(f'{label} must be a multiple of 64 between 256 and 2048.')
    if type(steps) is not int or not 1 <= steps <= 80:
        raise ValueError('Steps must be between 1 and 80.')
    if isinstance(cfg, bool) or not isinstance(cfg, (int, float)) or not 1 <= cfg <= 20:
        raise ValueError('CFG must be between 1 and 20.')
    if seed is not None and (type(seed) is not int or not 0 <= seed <= 2**64 - 1):
        raise ValueError('Seed must be a non-negative 64-bit integer.')
    graph = load_sdxl_preset()
    graph['10']['inputs']['text'] = prompt.strip()
    graph['11']['inputs']['text'] = negative
    graph['15']['inputs']['ckpt_name'] = checkpoint
    graph['13']['inputs'].update(width=width, height=height)
    graph['12']['inputs'].update(steps=steps, cfg=float(cfg), seed=seed if seed is not None else uuid4().int & ((1 << 64) - 1))
    return graph


class ComfyLocalClient:
    """Localhost-only API helper; calling code must make user actions explicit."""

    def __init__(self, base_url: str = 'http://127.0.0.1:8188', opener=None):
        url = parse.urlsplit(base_url)
        if (url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1')
                or url.username or url.password or url.path not in ('', '/')
                or url.query or url.fragment or url.port is None):
            raise ValueError('ComfyUI address must be a local HTTP server with a port (e.g. http://127.0.0.1:8188).')
        self.base_url = f'http://{url.hostname}:{url.port}' if ':' not in url.hostname else f'http://[{url.hostname}]:{url.port}'
        self._opener = opener or request.build_opener(request.ProxyHandler({}))

    def _json(self, path: str, payload: dict | None = None) -> object:
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        req = request.Request(self.base_url + path, data=data,
                              headers={'Content-Type': 'application/json'} if data else {},
                              method='POST' if data else 'GET')
        with self._opener.open(req, timeout=10) as response:
            raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError('ComfyUI response was unexpectedly large.')
        return json.loads(raw.decode('utf-8'))

    def system_stats(self) -> dict:
        """Check a running ComfyUI instance without submitting any work."""
        response = self._json('/system_stats')
        if not isinstance(response, dict):
            raise ValueError('ComfyUI returned invalid server status.')
        return response

    def checkpoints(self) -> list[str]:
        """List the models the active ComfyUI instance actually sees."""
        result = self._json('/models/checkpoints')
        if not isinstance(result, list):
            raise ValueError('ComfyUI did not return a checkpoint list.')
        return [name for name in result if isinstance(name, str)]

    def submit(self, graph: dict) -> str:
        """Queue an explicitly requested workflow, returning the new prompt ID."""
        if not isinstance(graph, dict) or not graph:
            raise ValueError('Cannot submit an empty workflow.')
        if any(not isinstance(node, dict) or node.get('class_type') not in ALLOWED_CLASSES
               for node in graph.values()):
            raise ValueError('Only the built-in approved SDXL workflow nodes are allowed.')
        response = self._json('/prompt', {'prompt': graph, 'client_id': str(uuid4())})
        if not isinstance(response, dict) or not isinstance(response.get('prompt_id'), str):
            raise ValueError('ComfyUI rejected the workflow or did not return a prompt ID.')
        return response['prompt_id']

    def history(self, prompt_id: str) -> dict:
        if not isinstance(prompt_id, str) or not prompt_id or any(c not in '0123456789abcdef-' for c in prompt_id.lower()):
            raise ValueError('Unexpected ComfyUI prompt identifier.')
        result = self._json('/history/' + parse.quote(prompt_id))
        if not isinstance(result, dict):
            raise ValueError('ComfyUI returned invalid job history.')
        return result

    def image_output(self, prompt_id: str) -> dict | None:
        """Return the first Save Image output if finished; None while pending.

        Raise on a reported execution failure, rather than polling indefinitely.
        """
        records = self.history(prompt_id)
        job = records.get(prompt_id)
        if not job:
            return None
        if not isinstance(job, dict):
            raise ValueError('ComfyUI returned invalid job details.')
        status = job.get('status', {})
        if isinstance(status, dict):
            if status.get('status_str') in ('error', 'failed'):
                messages = status.get('messages') or []
                details = ''
                for item in messages:
                    if isinstance(item, (list, tuple)) and item and item[0] == 'execution_error':
                        if isinstance(item[-1], dict):
                            details = str(item[-1].get('exception_message') or '')[:350]
                        break
                raise RuntimeError('ComfyUI could not generate the image.' + (f' {details}' if details else ' Check the ComfyUI queue for details.'))
        outputs = job.get('outputs', {})
        if not isinstance(outputs, dict):
            raise ValueError('ComfyUI returned malformed output data.')
        images = (outputs.get('7') or {}).get('images', [])
        if images and isinstance(images, list) and isinstance(images[0], dict):
            return images[0]
        if isinstance(status, dict) and status.get('completed'):
            raise RuntimeError('ComfyUI marked the job finished but returned no image. Inspect its workflow and errors.')
        return None

    def download_image(self, output: dict, *, max_bytes: int = 25_000_000) -> bytes:
        """Read only a generated image from ComfyUI's output directory."""
        if not isinstance(output, dict):
            raise ValueError('Image descriptor is missing.')
        filename = output.get('filename')
        subfolder = output.get('subfolder') or ''
        if (not isinstance(filename, str) or len(filename) > 200 or
                not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) or
                filename in ('.', '..') or '/' in filename or '\\' in filename or '\x00' in filename):
            raise ValueError('ComfyUI returned an invalid image filename.')
        if not isinstance(subfolder, str) or len(subfolder) > 200:
            raise ValueError('ComfyUI returned an invalid image subfolder.')
        segments = subfolder.replace('\\', '/').split('/') if subfolder else []
        if any(part in ('.', '..', '') or ':' in part or '\x00' in part for part in segments):
            raise ValueError('ComfyUI returned an unsafe image subfolder.')
        if output.get('type', 'output') != 'output':
            raise ValueError('Only completed images in ComfyUI output are supported.')
        query = parse.urlencode({'filename': filename, 'subfolder': subfolder, 'type': 'output'})
        req = request.Request(self.base_url + '/view?' + query)
        with self._opener.open(req, timeout=30) as response:
            data = response.read(max_bytes + 1)
        if not data or len(data) > max_bytes:
            raise ValueError('ComfyUI image output is missing or too large.')
        return data


def find_local_comfy(*, ports=(8188, 8000), opener=None):
    """Try typical local Comfy ports; do not scan networks or remote hosts."""
    last_error = None
    for port in ports:
        try:
            client = ComfyLocalClient(f'http://127.0.0.1:{port}', opener=opener)
            client.system_stats()
            return client
        except (OSError, ValueError, TimeoutError) as exc:
            last_error = exc
    raise ConnectionError('Could not connect to local ComfyUI on ports ' + ', '.join(map(str, ports)) +
                          '. Start your ComfyUI instance, or enter its localhost URL manually.') from last_error
