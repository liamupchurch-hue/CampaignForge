"""Describe a *selected local archived image* using an opt-in vision-capable Ollama model."""
from __future__ import annotations
from pathlib import Path
from character_sheets import image_payload
from oracle_providers import ollama_chat

IMAGE_TYPES={'.png','.jpg','.jpeg','.webp'}
def describe_image(path,question,model):
    path=Path(path)
    if path.suffix.lower() not in IMAGE_TYPES:
        raise ValueError('Image interpretation supports PNG, JPEG, and WebP. Scanned PDFs can be imported through character sheet review.')
    messages=[{'role':'system','content':('Describe only details visibly supported by the supplied picture. '
               'You are reviewing an image stored in a local Campaign Forge Archives. '
               'Do not invent map landmarks, labels or terrain you cannot see. If text is too small, say so.')},
              {'role':'user','content':question+'\nSOURCE IMAGE: '+path.name,'images':[image_payload(path)]}]
    return ollama_chat(messages,model=model,timeout=300)


def match_requested_image(archive,project_id,question):
    """Find an explicitly named image in an archive question, not a random related image."""
    lower=question.casefold()
    if not any(t in lower for t in ('archive','map','image','picture','document','photo','drawing','file')):return None
    for item in archive.list(project_id):
        stem=Path(item['name']).stem.casefold().strip()
        if Path(item['name']).suffix.lower() in IMAGE_TYPES and len(stem)>=5:
            # user can omit a trailing location suffix but must provide a unique 2-word phrase
            if stem in lower:return item
            words=[w for w in stem.split() if len(w)>=3]
            if len(words)>=2 and all(w in lower for w in words[:2]):return item
    return None
