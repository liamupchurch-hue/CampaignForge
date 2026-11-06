"""Narrow, validated project-edit protocol for Oracle proposals.

Never accepts Python, SQL, shell commands, file paths, or software mutations.
Each proposal is applied to a COPY after explicit UI approval.
"""
from __future__ import annotations
import copy,json,re
from campaign_data import CATEGORIES,new_entry

ALLOWED_FIELDS={'pitch','setting','story_arc','tone','levels','title','author'}
MAX_ACTIONS=60


def project_outline_context(project):
    data={'campaign':{k:project.get(k,'') for k in ('title','system','pitch','setting','story_arc')},
          'sections':[], 'entries':[]}
    outline=project.get('book_outline') or {}
    names={e['id']:e.get('title','') for e in project.get('entries',[])}
    for section in outline.get('sections',[]):
        data['sections'].append({'id':section['id'],'title':section.get('title',''),
              'entries':[{'id':n['id'],'title':names.get(n['id'],'(linked content)')} for n in section.get('nodes',[]) if n.get('type')=='entry']})
    for e in project.get('entries',[]):
        data['entries'].append({'id':e['id'],'category':e.get('category'),'title':e.get('title',''),
                                'excerpt':e.get('content','')[:220], 'gm_only':e.get('gm_only',False)})
    return json.dumps(data,ensure_ascii=False)


def action_instructions():
    return '''You are a project-edit PLANNER, not a campaign writer. Propose at most 60 reversible edits to this Campaign Forge project.
Return ONLY JSON of the form {"changes":[...]}.
Supported operations:
{"op":"move_entry","entry_id":"EXISTING ID","section_id":"EXISTING SECTION ID","position":0}
{"op":"reorder_section","section_id":"EXISTING SECTION ID","ordered_ids":["ALL CURRENT ENTRY IDs OF SECTION IN NEW ORDER"]}
{"op":"update_field","field":"pitch|setting|story_arc|tone|levels|title|author","value":"replacement text"}
{"op":"edit_entry","entry_id":"EXISTING ID","content":"replacement text"}
{"op":"create_entry","category":"Chapter|Quest|NPC|Location|Encounter|Faction|Item|Lore|Secret|Session Notes|Handout","title":"name","content":"text"}
For organization tasks, prefer moves and reorders. Keep ALL original entries and text intact. Do not create new story beats, replace content, or invent lore unless explicitly requested. Preserve prerequisites and story chronology. Never output code or application changes. If impossible using supported actions, return {"changes":[]}.
'''


def normalize_plan(raw, project):
    if isinstance(raw,str):
        s=raw.strip()
        if s.startswith('```'):s=re.sub(r'^```(?:json)?\s*|\s*```$', '',s,flags=re.I)
        plan=json.loads(s)
    else:plan=raw
    changes=plan.get('changes') if isinstance(plan,dict) else None
    if not isinstance(changes,list) or len(changes)>MAX_ACTIONS:raise ValueError('Expected at most 60 structured project changes.')
    entries={e['id']:e for e in project.get('entries',[])}
    sections={s['id']:s for s in (project.get('book_outline') or {}).get('sections',[])}
    clean=[]
    for change in changes:
        if not isinstance(change,dict):raise ValueError('Invalid change type.')
        op=change.get('op')
        if op=='move_entry':
            eid=change.get('entry_id');sid=change.get('section_id');pos=change.get('position')
            if eid not in entries or sid not in sections or type(pos) is not int or pos<0 or pos>10000:raise ValueError('Invalid move references.')
            clean.append({'op':op,'entry_id':eid,'section_id':sid,'position':pos})
        elif op=='reorder_section':
            sid=change.get('section_id');ids=change.get('ordered_ids')
            if sid not in sections or not isinstance(ids,list):raise ValueError('Invalid reorder references.')
            expected=[n['id'] for n in sections[sid]['nodes'] if n.get('type')=='entry']
            if sorted(ids)!=sorted(expected) or len(ids)!=len(expected):
                raise ValueError('Reordering must preserve every existing entry exactly once.')
            clean.append({'op':op,'section_id':sid,'ordered_ids':ids[:]})
        elif op=='update_field':
            field=change.get('field');val=change.get('value')
            if field not in ALLOWED_FIELDS or not isinstance(val,str) or len(val)>15000:raise ValueError('Unrecognized or oversized campaign field.')
            clean.append({'op':op,'field':field,'value':val})
        elif op=='edit_entry':
            eid=change.get('entry_id');text=change.get('content')
            if eid not in entries or not isinstance(text,str) or len(text)>30000:raise ValueError('Invalid entry edit.')
            clean.append({'op':op,'entry_id':eid,'content':text})
        elif op=='create_entry':
            cat=change.get('category');title=change.get('title');content=change.get('content')
            if cat not in CATEGORIES or not isinstance(title,str) or not 1<=len(title.strip())<=150 or not isinstance(content,str) or len(content)>30000:
                raise ValueError('Invalid new entry.')
            clean.append({'op':op,'category':cat,'title':title.strip(),'content':content})
        else:raise ValueError('Unsupported project action: '+str(op))
    return clean


def apply_actions(project,changes):
    """Validate the whole plan on a snapshot so no partial update can leak through."""
    changes=normalize_plan({'changes':changes},project)
    result=copy.deepcopy(project)
    nodes=(result.get('book_outline') or {}).get('sections',[])
    index={e['id']:e for e in result.get('entries',[])}
    for op in changes:
        kind=op['op']
        if kind=='move_entry':
            entry_id=op['entry_id']
            for section in nodes:section['nodes']=[n for n in section['nodes'] if not(n.get('type')=='entry' and n.get('id')==entry_id)]
            target=next(s for s in nodes if s['id']==op['section_id'])
            target['nodes'].insert(min(len(target['nodes']),op['position']),{'type':'entry','id':entry_id})
        elif kind=='reorder_section':
            target=next(s for s in nodes if s['id']==op['section_id'])
            existing={n['id']:n for n in target['nodes'] if n.get('type')=='entry'}
            if set(op['ordered_ids'])!=set(existing):raise ValueError('Scene set changed since the proposal was prepared. Please request a fresh proposal.')
            others=[n for n in target['nodes'] if n.get('type')!='entry']
            target['nodes']=[existing[i] for i in op['ordered_ids']]+others
        elif kind=='update_field':result[op['field']]=op['value']
        elif kind=='edit_entry':index[op['entry_id']]['content']=op['content']
        elif kind=='create_entry':
            e=new_entry(op['category'],op['title'],op['content']);result['entries'].append(e)
            section=next((s for s in nodes if s['title']=='Adventure Chapters'),None)
            if section:section['nodes'].append({'type':'entry','id':e['id']})
    return result


def summarize_actions(project,changes):
    entries={e['id']:e.get('title','') for e in project.get('entries',[])}
    sections={s['id']:s.get('title','') for s in (project.get('book_outline') or {}).get('sections',[])}
    rows=[]
    for op in changes:
        k=op['op']
        if k=='move_entry':rows.append('MOVE: '+entries[op['entry_id']]+' → '+sections[op['section_id']]+f" (position {op['position']+1})")
        elif k=='reorder_section':rows.append('REORDER: '+sections[op['section_id']]+' → '+', '.join(entries.get(e,'?') for e in op['ordered_ids']))
        elif k=='update_field':rows.append('REPLACE '+op['field']+': '+repr(str(project.get(op['field'],''))[:120])+' → '+repr(op['value'][:120]))
        elif k=='edit_entry':rows.append('REWRITE '+entries[op['entry_id']]+': '+repr(op['content'][:150]))
        elif k=='create_entry':rows.append('CREATE '+op['category']+': '+op['title'])
    return '\n\n'.join(f'{n+1}. {s}' for n,s in enumerate(rows))
