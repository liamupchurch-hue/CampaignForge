"""System-aware but deliberately non-authoritative character and encounter records."""
from __future__ import annotations
import uuid, json
from pathlib import Path

STAT_FIELDS = {
    'Pathfinder 2e (Remaster)': ['Level', 'Perception', 'AC', 'HP', 'Speed', 'Fortitude', 'Reflex', 'Will', 'Strike', 'Damage', 'Abilities', 'Spells'],
    'Pathfinder 2e (Legacy)': ['Level', 'Perception', 'AC', 'HP', 'Speed', 'Fortitude', 'Reflex', 'Will', 'Strike', 'Damage', 'Abilities', 'Spells'],
    'Pathfinder 2e': ['Level', 'Perception', 'AC', 'HP', 'Speed', 'Fortitude', 'Reflex', 'Will', 'Strike', 'Damage', 'Abilities', 'Spells'],
    'D&D 5e (2014)': ['Challenge', 'AC', 'HP', 'Speed', 'STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA', 'Saving Throws', 'Skills', 'Attacks', 'Actions', 'Spells'],
    'D&D 5e (2024)': ['Challenge', 'AC', 'HP', 'Speed', 'STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA', 'Saving Throws', 'Skills', 'Attacks', 'Actions', 'Spells'],
    'System-neutral': ['Level', 'AC', 'HP', 'Speed', 'Attacks', 'Abilities'],
    'Other': ['Level', 'AC', 'HP', 'Speed', 'Attacks', 'Abilities'],
}
RULE_SOURCES = {
    'Pathfinder 2e (Remaster)': ('Archives of Nethys — Pathfinder 2e', 'https://2e.aonprd.com/'),
    'Pathfinder 2e (Legacy)': ('Archives of Nethys — Pathfinder 2e', 'https://2e.aonprd.com/'),
    'Pathfinder 2e': ('Archives of Nethys — Pathfinder 2e', 'https://2e.aonprd.com/'),
    'D&D 5e (2014)': ('D&D SRD 5.1', 'https://www.dndbeyond.com/srd'),
    'D&D 5e (2024)': ('D&D SRD 5.2', 'https://www.dndbeyond.com/srd'),
}

def new_character(name='New Character', combat=False, system='System-neutral'):
    return {'id':uuid.uuid4().hex, 'name':name, 'role':'NPC', 'bio':'', 'traits':'',
            'relationships':'','combat':bool(combat),'gm_only':False, 'system':system,
            'stats':{},'source':'Manual entry — unverified'}

def new_encounter(title='New Encounter'):
    return {'id':uuid.uuid4().hex,'title':title,'description':'','gm_only':True,
            'combatants':[]}  # [{'character_id': ID, 'count': int}]

def add_combatant(encounter, character_id, count=1):
    if not isinstance(count,int) or not 1<=count<=99:
        raise ValueError('Quantity must be between 1 and 99.')
    for c in encounter['combatants']:
        if c['character_id']==character_id:
            c['count']+=count
            return
    encounter['combatants'].append({'character_id':character_id,'count':count})

def import_json_characters(path, system):
    """Best-effort JSON mapping; never asserts legal or rules-valid stat blocks.

    Hero Lab export schemas differ by application/version. Unknown JSON is
    retained for user review rather than silently interpreted as validated.
    """
    obj=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if isinstance(obj,list): raw=obj
    elif isinstance(obj,dict):
        raw=next((obj[k] for k in ('characters','actors','creatures') if isinstance(obj.get(k),list)),None)
        if raw is None:
            raw=[obj]
    else: raise ValueError('Expected a JSON object or list of characters.')
    if len(raw)>150: raise ValueError('Import a maximum of 150 characters per file.')
    characters=[]
    for record in raw:
        if not isinstance(record,dict): continue
        name=str(record.get('name') or record.get('character_name') or 'Imported character')
        character=new_character(name,combat=False,system=system)
        character['bio']=str(record.get('description') or record.get('bio') or '')[:15000]
        character['traits']=str(record.get('traits') or '')[:5000]
        character['source']='JSON import — review all statistics and edition compatibility'
        # Preserve provided values with original keys. Do not manufacture a ruleset interpretation.
        offered=record.get('stats') or record.get('statistics') or {}
        if not isinstance(offered,dict): offered={}
        for key in ['AC','HP','ac','hp','level','Level','speed','Speed','challenge','CR']:
            if key in record and key not in offered:
                offered[key]=record[key]
        character['stats']={str(k):str(v)[:2000] for k,v in offered.items() if isinstance(v,(int,float,str,bool))}
        character['combat']=bool(character['stats'])
        characters.append(character)
    if not characters: raise ValueError('No character records were recognized in this JSON.')
    return characters
