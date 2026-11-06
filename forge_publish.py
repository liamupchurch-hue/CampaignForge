"""Book Architect rendering helpers for reportlab's Platypus story."""
from __future__ import annotations
from html import escape
from io import BytesIO
from pathlib import Path
from reportlab.lib.units import inch
from reportlab.platypus import Image, Spacer
from forge_book import node_title
from map_tools import render_map


def add_architect_content(campaign, story, add_heading, paragraph, body, small, include_gm, archive=None):
    roster={x['id']:x for x in campaign.get('roster',[])}
    entries={x['id']:x for x in campaign.get('entries',[])}
    encounters={x['id']:x for x in campaign.get('encounters',[])}
    maps={x['id']:x for x in campaign.get('maps',[])}
    def prose(text, style=body):
        if text is None:return
        for p in str(text).split('\n\n'):
            if p.strip():story.append(paragraph(p,style))
    def stats(character,compact=False):
        if not character.get('combat'):return
        fields=character.get('stats') or {}
        if not fields:
            prose('Combat character — no statistics entered yet. Complete and verify the character sheet before play.',small)
            return
        if compact:
            chosen=('Level','Challenge','AC','ac','HP','hp','Speed','speed','Strike','Attack','Attacks','Damage','Actions')
            items=[(k,v) for k,v in fields.items() if k in chosen]
            if not items:items=list(fields.items())[:5]
        else: items=list(fields.items())
        for key,val in items:
            prose(f'{key}: {val}',small)
        if not compact:prose('Combat statistics require DM verification for the selected game system and edition.',small)
    def render_character(c,short=False):
        prose(f"Role: {c.get('role','NPC')}",small)
        if not short:
            prose(c.get('bio',''))
            prose(c.get('traits',''))
            prose(c.get('relationships',''))
        if include_gm:stats(c,compact=short)
    def render_encounter(e):
        prose(e.get('description',''))
        if not include_gm:return
        for member in e.get('combatants',[]):
            c=roster.get(member.get('character_id'))
            if not c:
                prose('Encounter entry refers to a missing character. Review the roster.',small)
                continue
            if c.get('gm_only') and not include_gm:continue
            prose(f"{member.get('count',1)} × {c.get('name','Character')}",small)
            if c.get('combat'):
                stats(c,compact=True)
            else:
                prose('Noncombat character — biography only; no combat statistics supplied.',small)
    def render_map_node(m):
        background=None
        if archive is not None and m.get('background_archive_id'):
            try:background=archive.source_path(m['background_archive_id'],campaign.get('project_id'))
            except (KeyError,PermissionError,OSError):pass
        img=render_map(m,size=40,background=background)
        b=BytesIO();img.save(b,format='PNG');b.seek(0)
        max_width,max_height=6.7*inch,6.1*inch
        scale=min(max_width/img.width,max_height/img.height,1.4)
        story.append(Image(b,width=img.width*scale,height=img.height*scale))
        story.append(Spacer(1,8))
    def render_archive(ident):
        if archive is None:
            prose('Library unavailable on this computer — original file was not embedded.',small)
            return
        try:
            row=archive.get(ident,campaign.get('project_id'))
            p=archive.source_path(ident,campaign.get('project_id'))
        except Exception:
            prose('Archived reference missing. Restore The Archives backup to include this item.',small)
            return
        if p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):
            prose(f"Reference document: {row['name']}. Original contents not reproduced automatically.",small)
            return
        try:
            from PIL import Image as PILImage
            img=PILImage.open(p).convert('RGB')
            # Downsample massive source assets, but don't enlarge low-res graphics.
            img.thumbnail((2500,2500))
            buf=BytesIO();img.save(buf,format='JPEG',quality=88);buf.seek(0)
            max_width,max_height=6.7*inch,6.0*inch
            factor=min(max_width/img.width,max_height/img.height,1)
            story.append(Image(buf,width=img.width*factor,height=img.height*factor))
        except Exception:
            prose('Image could not be embedded. Check the archived source file.',small)

    outline=campaign.get('book_outline') or {}
    for section in outline.get('sections',[]):
        included=[]
        for node in section.get('nodes',[]):
            typ=node.get('type');ident=node.get('id')
            if typ=='entry':
                obj=entries.get(ident)
                if obj and (include_gm or not obj.get('gm_only')):included.append((typ,obj))
            elif typ=='character':
                obj=roster.get(ident)
                if obj and (include_gm or not obj.get('gm_only')):included.append((typ,obj))
            elif typ=='encounter':
                obj=encounters.get(ident)
                if obj and include_gm:included.append((typ,obj))
            elif typ=='map':
                obj=maps.get(ident)
                if obj:included.append((typ,obj))
            elif typ=='archive':
                if include_gm:included.append((typ,ident))
            elif typ=='overview':included.append((typ,None))
        if not included:continue
        add_heading(section.get('title','Section'))
        for typ,obj in included:
            if typ=='overview':
                for label,key in (('Premise','pitch'),('Setting','setting'),('Main Story Arc','story_arc')):
                    if campaign.get(key,'').strip():add_heading(label,1);prose(campaign[key])
            elif typ=='entry':
                add_heading(obj.get('title','Untitled'),1)
                if obj.get('gm_only'):prose('DM ONLY — NOT FOR PLAYERS',small)
                prose(obj.get('content',''))
            elif typ=='character':
                add_heading(obj.get('name','Character'),1);render_character(obj)
            elif typ=='encounter':
                add_heading(obj.get('title','Encounter'),1);render_encounter(obj)
            elif typ=='map':
                add_heading(obj.get('title','Map'),1);render_map_node(obj)
            elif typ=='archive':
                try:
                    item=archive.get(obj,campaign.get('project_id')) if archive else {}
                    add_heading(item.get('name','Archived document'),1)
                except Exception:add_heading('Archived document',1)
                render_archive(obj)
