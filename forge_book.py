"""Editable book section hierarchy. No AI or chronological inference is claimed."""
from __future__ import annotations
import uuid

TEMPLATES = {
 'D&D Adventure': ['Adventure Overview','Player Guide','Setting & DM Background','Adventure Chapters','NPCs & Creatures','Encounters','Items & Rewards','Maps & Handouts','Reference Appendix'],
 'Pathfinder Adventure': ['Adventure Overview','Player Guide','Setting & DM Background','Adventure Chapters','NPCs & Creatures','Encounters','Items & Rewards','Maps & Handouts','Reference Appendix'],
 'World & Setting Guide': ['Adventure Overview','Setting & DM Background','Player Guide','NPCs & Creatures','Adventure Chapters','Maps & Handouts','Items & Rewards','Encounters','Reference Appendix'],
 'Custom DM Binder': ['Adventure Overview','Adventure Chapters','Setting & DM Background','Player Guide','NPCs & Creatures','Encounters','Items & Rewards','Maps & Handouts','Reference Appendix'],
}

def _new_section(title):
 return {'id':uuid.uuid4().hex,'title':title,'nodes':[]}

def suggest_outline(campaign, template='Pathfinder Adventure'):
 if template not in TEMPLATES: raise ValueError('Unknown book template.')
 sections=[_new_section(title) for title in TEMPLATES[template]]
 groups={x['title']:x for x in sections}
 groups['Adventure Overview']['nodes']=[{'type':'overview','id':'overview'}]
 for e in campaign.get('entries',[]):
  cat=e.get('category')
  if cat in ('Chapter','Quest','Session Notes','Encounter'):
   dest='Adventure Chapters'
  elif cat in ('Location','Lore','Faction','Secret'):
   dest='Setting & DM Background' if e.get('gm_only') or cat=='Secret' else 'Player Guide'
  elif cat=='NPC': dest='NPCs & Creatures'
  elif cat=='Item': dest='Items & Rewards'
  elif cat=='Handout': dest='Maps & Handouts'
  else: dest='Reference Appendix'
  groups[dest]['nodes'].append({'type':'entry','id':e['id']})
 for c in campaign.get('roster',[]): groups['NPCs & Creatures']['nodes'].append({'type':'character','id':c['id']})
 for e in campaign.get('encounters',[]): groups['Encounters']['nodes'].append({'type':'encounter','id':e['id']})
 for m in campaign.get('maps',[]): groups['Maps & Handouts']['nodes'].append({'type':'map','id':m['id']})
 return {'template':template,'sections':sections}

def node_title(campaign,node):
 if node['type']=='overview':return 'Campaign Overview'
 key={'entry':'entries','character':'roster','encounter':'encounters','map':'maps'}.get(node['type'])
 if not key: return '(Unknown item)'
 match=next((x for x in campaign.get(key,[]) if x.get('id')==node['id']),None)
 if match: return match.get('title') or match.get('name') or 'Untitled'
 return '(Missing item — review outline)'

def remove_missing_nodes(campaign,outline):
 for section in outline.get('sections',[]):
  section['nodes']=[n for n in section.get('nodes',[]) if n['type']=='overview' or not node_title(campaign,n).startswith('(Missing')]
 return outline

def outline_node_ids(outline):
 return {(n.get('type'),n.get('id')) for s in outline.get('sections',[]) for n in s.get('nodes',[])}
