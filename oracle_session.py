"""Ephemeral Oracle transcript, field proposals and user preference storage.

None of these routines writes campaign files or sends information to a provider.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import os
import re


def clean_markdown(text: str) -> str:
    """Produce readable plain text without markdown control characters.

    Preserve paragraphs and meaningful list items. Avoid deleting asterisks
    within normal prose or stripping # in non-heading content.
    """
    value = str(text or '').replace('\r\n', '\n').replace('\r', '\n')
    value = re.sub(r'(?m)^\s{0,3}#{1,6}\s+', '', value)
    value = re.sub(r'(?m)^\s{0,3}>\s?', '', value)
    value = re.sub(r'(?m)^\s*[-*+]\s+', '• ', value)
    value = re.sub(r'(?m)^\s*([-*_]\s*){3,}$', '────────────────', value)
    value = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'\1 (\2)', value)
    value = re.sub(r'(?<!\w)(\*\*|__)(.+?)\1', r'\2', value)
    value = re.sub(r'(?<!\w)(\*|_)([^\n*]+?)\1(?!\w)', r'\2', value)
    value = re.sub(r'(?m)^```[^\n]*\n?', '', value)
    value = re.sub(r'`([^`]+)`', r'\1', value)
    return re.sub(r'\n{4,}', '\n\n\n', value).strip()


def apply_suggestion(original: str, suggestion: str, action: str) -> str:
    new = clean_markdown(suggestion)
    if not new:
        raise ValueError('There is no usable Oracle suggestion to apply.')
    if action == 'replace':
        return new
    if action == 'append':
        old = original.rstrip()
        return (old + '\n\n' + new) if old else new
    raise ValueError('Choose Append or Replace; merge requires another Oracle consultation.')


def transcript_text(turns: list[dict]) -> str:
    chunks = ['CAMPAIGN FORGE — ORACLE CONSULTATION TRANSCRIPT',
              'Exported by the user. The conversation is not stored inside the campaign project.']
    for i, turn in enumerate(turns, 1):
        target = turn.get('target_label') or 'General consultation'
        chunks.append(f'\n--- Inquiry {i} | {turn.get("mode", "Oracle").title()} | {target} ---\n'
                      f'YOU:\n{turn.get("question", "").strip()}\n\n'
                      f'ORACLE:\n{clean_markdown(turn.get("answer", ""))}')
    return '\n\n'.join(chunks).strip() + '\n'


def preferences_path() -> Path:
    root = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.campaign_forge'))
    return root / 'CampaignForge' / 'settings.json'


def load_preferences() -> dict:
    try:
        payload = json.loads(preferences_path().read_text(encoding='utf-8'))
        return {k: bool(payload.get(k, False)) for k in ('hide_local_notice', 'hide_cloud_notice', 'hide_import_notice')}
    except (OSError, ValueError, TypeError):
        return {'hide_local_notice': False, 'hide_cloud_notice': False, 'hide_import_notice': False}


def save_preferences(prefs: dict):
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: bool(v) for k, v in prefs.items()}, indent=2), encoding='utf-8')
