"""Conservative local model discovery and core-node workflow builder.

No AI weights are bundled or downloaded. A model is selectable only when a
known, supported architecture and its companion files are visible to the
running ComfyUI instance. Checkpoint support is experimental beyond SDXL.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

MODEL_FAMILIES = {'sdxl', 'standard', 'zimage', 'flux_schnell', 'flux_dev'}


@dataclass(frozen=True)
class ModelChoice:
    display: str
    family: str
    filename: str
    text_encoder: str = ''
    second_encoder: str = ''
    vae: str = ''
    missing: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.family in MODEL_FAMILIES and not self.missing


def classify_model(name: str, *, folder: str = 'checkpoints') -> str:
    """Identify only supported diffusion architectures by conservative filename cues."""
    if not isinstance(name, str) or not name.lower().endswith(('.safetensors', '.ckpt')):
        return 'unknown'
    base = name.replace('\\', '/').split('/')[-1].casefold()
    if folder != 'checkpoints':
        if ('z_image_turbo' in base or 'z-image-turbo' in base or 'zimage_turbo' in base):
            return 'zimage'
        if 'flux' in base and ('schnell' in base or 'schnell' in base):
            return 'flux_schnell'
        if 'flux' in base and ('dev' in base or 'krea' in base):
            return 'flux_dev'
        return 'unknown'
    if any(term in base for term in ('flux', 'z_image', 'z-image', 'zimage', 'sd3', 'hunyuan', 'qwen', 'wan', 'video')):
        return 'unknown'  # those architectures cannot be loaded by our basic SD graph
    if any(term in base for term in (
        'sdxl', 'sd_xl', 'xl-base', 'xl_base', 'juggernautxl', 'ponyxl',
        'dreamshaperxl', 'copax', 'albedobasexl', 'realvisxl'
    )):
        return 'sdxl'
    return 'standard'  # best-effort: other checkpoint formats need live testing


def _choose(available: Sequence[str], preferred: Sequence[str]) -> str:
    seen = [x for x in available if isinstance(x, str)]
    for word in preferred:
        for file in seen:
            if word in file.casefold() and file.lower().endswith(('.safetensors', '.ckpt', '.pt')):
                return file
    return ''


def list_model_choices(checkpoints: Sequence[str], diffusion_models: Sequence[str],
                       text_encoders: Sequence[str], vaes: Sequence[str]) -> list[ModelChoice]:
    """Return supported models, including missing-asset explanations.

    Only names reported by the running ComfyUI instance count as installed.
    """
    models = []
    for name in checkpoints:
        family = classify_model(name)
        if family in ('sdxl', 'standard'):
            models.append(ModelChoice(name, family, name))
    for name in diffusion_models:
        family = classify_model(name, folder='diffusion_models')
        if family == 'unknown':
            continue
        vae = _choose(vaes, ('ae.safetensors', 'ae.', 'flux_vae'))
        missing = []
        if not vae:
            missing.append('VAE (ae.safetensors)')
        if family == 'zimage':
            enc = _choose(text_encoders, ('qwen_3_4b.safetensors', 'qwen_3_4b_', 'qwen3_4b'))
            enc2 = ''
            if not enc:
                missing.append('Qwen 3 4B text encoder')
            label = 'Z-Image Turbo'
        else:
            enc = _choose(text_encoders, ('clip_l.safetensors', 'clip_l'))
            enc2 = _choose(text_encoders, ('t5xxl_fp16', 't5xxl_fp8', 't5xxl'))
            if not enc:
                missing.append('CLIP-L text encoder')
            if not enc2:
                missing.append('T5XXL text encoder')
            label = 'FLUX.1 Schnell' if family == 'flux_schnell' else 'FLUX.1 Dev'
        models.append(ModelChoice(f'{label} — {name}', family, name, enc, enc2, vae, tuple(missing)))
    return models


def make_diffusion_workflow(choice: ModelChoice, prompt: str, negative: str,
                            width: int, height: int, steps: int, seed: int) -> dict:
    """Generate a fixed core-node API workflow for supported diffusion architectures.

    Z-Image Turbo and FLUX use unconditional/zero-negative branches. Their
    negative prompt is intentionally not used; the caller must disclose that.
    """
    if not isinstance(choice, ModelChoice) or choice.family not in ('zimage', 'flux_schnell', 'flux_dev'):
        raise ValueError('Choose a supported Z-Image Turbo or FLUX.1 model.')
    if not choice.ready:
        raise ValueError('Model files are missing: ' + ', '.join(choice.missing))
    graph = {
        '7': {'class_type': 'SaveImage', 'inputs': {'filename_prefix': 'CampaignForge_Art', 'images': ['14', 0]}},
        '11': {'class_type': 'ConditioningZeroOut', 'inputs': {'conditioning': ['10', 0]}},
        '13': {'class_type': 'EmptySD3LatentImage', 'inputs': {'width': width, 'height': height, 'batch_size': 1}},
        '14': {'class_type': 'VAEDecode', 'inputs': {'samples': ['12', 0], 'vae': ['17', 0]}},
        '17': {'class_type': 'VAELoader', 'inputs': {'vae_name': choice.vae}},
        '18': {'class_type': 'UNETLoader', 'inputs': {'unet_name': choice.filename, 'weight_dtype': 'default'}},
    }
    if choice.family == 'zimage':
        graph['10'] = {'class_type': 'CLIPTextEncode', 'inputs': {'clip': ['15', 0], 'text': prompt}}
        graph['15'] = {'class_type': 'CLIPLoader', 'inputs': {'clip_name': choice.text_encoder, 'type': 'lumina2', 'device': 'default'}}
        graph['16'] = {'class_type': 'ModelSamplingAuraFlow', 'inputs': {'model': ['18', 0], 'sampling': 'flow', 'shift': 3}}
        model_ref = ['16', 0]
        sampler, scheduler = 'res_multistep', 'simple'
    else:
        guidance = 3.5 if choice.family == 'flux_dev' else 0.0
        graph['10'] = {'class_type': 'CLIPTextEncodeFlux', 'inputs': {
            'clip': ['15', 0], 'clip_l': prompt, 't5xxl': prompt, 'guidance': guidance}}
        graph['15'] = {'class_type': 'DualCLIPLoader', 'inputs': {
            'clip_name1': choice.text_encoder, 'clip_name2': choice.second_encoder,
            'type': 'flux', 'device': 'default'}}
        model_ref = ['18', 0]
        sampler, scheduler = 'euler', 'simple'
    graph['12'] = {'class_type': 'KSampler', 'inputs': {
        'seed': seed, 'steps': steps, 'cfg': 1.0, 'sampler_name': sampler,
        'scheduler': scheduler, 'denoise': 1.0, 'model': model_ref,
        'positive': ['10', 0], 'negative': ['11', 0], 'latent_image': ['13', 0]
    }}
    return graph
