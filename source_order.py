"""Transparent, offline book-order suggestion based on original manuscript headings.

No invented scenes, no automatic changes: proposals require a DM confirmation.
"""
from __future__ import annotations
import re


def _norm(value):return re.sub(r'\s+',' ',str(value or '').casefold().strip())

def heading_position(source_text, heading):
    # Ignore an early table of contents when possible; require a standalone heading.
    title=_norm(heading)
    if not title:return None
    lines=source_text.splitlines()
    matches=[];position=0
    for line in lines:
        n=_norm(line).strip(':–- ')
        if n==title or (re.match(r'^chapter(?:\s+\d+)?\s*[:–—-]\s*',n) and title in n):
            matches.append(position)
        position+=len(line)+1
    if matches:
        # DOCX table of contents often lists a title twice. Prefer the actual later heading.
        return matches[-1] if len(matches)>1 else matches[0]
    # Last-resort phrase match, never guessing from semantics alone.
    return None


def propose_source_order(campaign, source_text, section_title='Adventure Chapters'):
    sections=campaign.get('book_outline',{}).get('sections',[]) if campaign.get('book_outline') else []
    section=next((s for s in sections if s.get('title')==section_title),None)
    if section is None:return None,[]
    lookup={e['id']:e['title'] for e in campaign.get('entries',[])}
    indexed=[];unknown=[]
    for index,node in enumerate(section.get('nodes',[])):
        title=lookup.get(node.get('id')) if node.get('type')=='entry' else None
        pos=heading_position(source_text,title) if title else None
        if pos is None:unknown.append((index,node,title))
        else:indexed.append((pos,index,node,title))
    indexed.sort(key=lambda x:(x[0],x[1]))
    # Preserve unrecognized nodes in their existing slots, never drop them.
    recognized_iter=iter([v[2] for v in indexed]); known_ids={id(v[2]) for v in indexed}
    reordered=[]
    for node in section['nodes']:
        if id(node) in known_ids:reordered.append(next(recognized_iter))
        else:reordered.append(node)
    return reordered,[(title,pos) for pos,_,_,title in indexed]


def validated_ai_order(raw, nodes):
    """Only accept complete, duplicate-free permutations of current node identities."""
    import json
    if isinstance(raw,str):
        value=raw.strip()
        if value.startswith('```'):
            value=re.sub(r'^```(?:json)?\s*|\s*```$', '', value,flags=re.I)
        result=json.loads(value)
    else:result=raw
    ids=result.get('ordered_ids') if isinstance(result,dict) else None
    expected={f'{n["type"]}:{n["id"]}' for n in nodes}
    if not isinstance(ids,list) or len(ids)!=len(nodes) or set(ids)!=expected or len(set(ids))!=len(ids):
        raise ValueError('The AI returned an incomplete or invalid scene order. No changes were applied.')
    by_id={f'{n["type"]}:{n["id"]}':n for n in nodes}
    return [by_id[ident] for ident in ids]


def scene_context_excerpts(source_text, titled_nodes, max_total=11000):
    """Gather relevant source passages around recognized scene headings (not a random tail)."""
    selections=[];used=0
    for ident,title in titled_nodes:
        pos=heading_position(source_text,title)
        if pos is None:continue
        start=max(0,pos-70);end=min(len(source_text),pos+750)
        text=source_text[start:end].strip()
        if used+len(text)>max_total:text=text[:max(0,max_total-used)]
        if len(text)<60:break
        selections.append(f'SCENE {ident} — {title}\n'+text)
        used+=len(text)
        if used>=max_total:break
    return '\n\n'.join(selections)
