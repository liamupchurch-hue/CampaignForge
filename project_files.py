"""Friendly and safe project filenames, Save As version suggestions, recent folder.

Storage is local only; it never includes campaign text, API keys, or Oracle transcripts.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path

EXTENSION = '.campaign.json'


def title_to_stem(title: str) -> str:
    """Turn the visible campaign title into a filename Windows accepts."""
    candidate = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', str(title or '')).strip().strip('. ')
    candidate = re.sub(r'\s+', ' ', candidate).strip()
    if candidate.casefold() in ('', 'untitled campaign'):
        candidate = 'Untitled Campaign'
    # Windows reserved device names are not legal filenames, even with extensions.
    if candidate.split('.', 1)[0].casefold() in {'con','prn','aux','nul',*(f'com{i}' for i in range(1,10)),*(f'lpt{i}' for i in range(1,10))}:
        candidate = 'Campaign - ' + candidate
    return candidate[:100].rstrip(' .')


def suggest_save_name(title: str, directory: str | Path, current_path: str | Path | None = None) -> str:
    """Suggest a unique filename, never silently target an existing project.

    On Save As, start from the current project's name, including a custom name.
    """
    folder = Path(directory)
    if current_path:
        name = Path(current_path).name
        stem = name[:-len(EXTENSION)] if name.lower().endswith(EXTENSION) else Path(name).stem
    else:
        stem = title_to_stem(title)
    stem = re.sub(r'\s+v\d+$', '', stem, flags=re.I)
    basic = folder / f'{stem}{EXTENSION}'
    if not current_path and not basic.exists():
        return basic.name
    version = 2
    while (folder / f'{stem} v{version}{EXTENSION}').exists():
        version += 1
    return f'{stem} v{version}{EXTENSION}'


def recent_metadata_path() -> Path:
    root = Path(os.environ.get('LOCALAPPDATA') or (Path.home() / '.campaign_forge'))
    return root / 'CampaignForge' / 'recent-project.json'


def last_project_directory() -> Path | None:
    try:
        saved = json.loads(recent_metadata_path().read_text(encoding='utf-8'))
        folder = Path(saved.get('directory', ''))
        return folder if folder.is_dir() else None
    except (OSError, TypeError, ValueError):
        return None


def remember_project_directory(project_file: str | Path) -> None:
    path = recent_metadata_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps({'directory': str(Path(project_file).resolve().parent)}, indent=2), encoding='utf-8')
    temp.replace(path)
