"""v0.7.0 - tests for map object layers, cautious sheets, ordering and PDF proof."""
from pathlib import Path
import json, tempfile, sys
from PIL import Image
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from character_sheets import parse_sheet_text,parse_vision_result,image_payload,extract_text_file
from source_order import heading_position,propose_source_order,validated_ai_order
from map_tools import render_map,export_map
from campaign_data import new_campaign,new_entry,new_map,save_campaign,load_campaign
from forge_book import suggest_outline
from forge_roster import new_character,new_encounter,add_combatant
from pdf_book import export_book


def test_sheet_text_only_recognizes_labeled_stats():
    values=parse_sheet_text('AC: 24\nHP: 75\nLevel: 6\nSpeed: 25 ft\nFortitude: +13\nName: Captain Rowan\nWeapon: mace\nHP: unknown')
    assert values=={'AC':'24','HP':'75','Level':'6','Speed':'25 ft','Fortitude':'+13'}


def test_vision_parse_safely_omits_unknown():
    raw='```json\n'+json.dumps({'stats':{'AC':'21','HP':'Unclear','Fortitude':'+9','ORACLE SECRET':'123'}})+'\n```'
    assert parse_vision_result(raw)=={'AC':'21','Fortitude':'+9'}
    assert parse_vision_result('not a JSON string')=={}


def test_pdf_selectable_character_sheet(tmp_path):
    from reportlab.pdfgen import canvas
    path=tmp_path/'guard.pdf'
    pdf=canvas.Canvas(str(path))
    pdf.drawString(72,740,'AC: 18')
    pdf.drawString(72,718,'HP: 45')
    pdf.drawString(72,696,'Level: 4')
    pdf.save()
    assert parse_sheet_text(extract_text_file(path))['HP']=='45'


def test_image_scaling_local_payload(tmp_path):
    import base64,io
    img=Image.new('RGB',(2200,1400),'white');path=tmp_path/'sheet.png';img.save(path)
    data=Image.open(io.BytesIO(base64.b64decode(image_payload(path))))
    assert max(data.size)<=1700


def test_source_order_only_reorders_matching_nodes():
    d=new_campaign('Hollowford')
    a=new_entry('Chapter','Council Meeting','');b=new_entry('Quest','The Search','');c=new_entry('Quest','Unknown Branch','')
    d['entries']=[a,b,c];d['book_outline']=suggest_outline(d)
    source='CHAPTER: The Search\n\nThings\nCouncil Meeting\nEnd.'
    proposal,matches=propose_source_order(d,source)
    assert [n['id'] for n in proposal]==[b['id'],a['id'],c['id']]
    assert len(matches)==2


def test_ai_proposal_must_be_exact_permutation():
    nodes=[{'type':'entry','id':'1'},{'type':'entry','id':'2'}]
    assert validated_ai_order({'ordered_ids':['entry:2','entry:1']},nodes)==[nodes[1],nodes[0]]
    with pytest.raises(ValueError):validated_ai_order({'ordered_ids':['entry:1','entry:1']},nodes)
    with pytest.raises(ValueError):validated_ai_order({'ordered_ids':['entry:1','entry:3']},nodes)


def test_layered_map_render_background_and_props(tmp_path):
    m=new_map('High Dock',10,6)
    m['objects']=[{'kind':'Crate','x':3,'y':3},{'kind':'Tree','x':1,'y':2},{'kind':'Marker','x':7,'y':1}]
    bg=tmp_path/'bg.png';Image.new('RGB',(500,300),(91,55,55)).save(bg)
    img=render_map(m,size=40,grid=False,background=bg)
    assert img.size==(400,240)
    assert img.getpixel((10,10))==(91,55,55)
    assert img.getpixel((140,140))!=(91,55,55)
    out=tmp_path/'export.png';export_map(m,out,background=bg)
    assert Image.open(out).size==(640,384)


def test_old_map_and_old_roster_still_work(tmp_path):
    d=new_campaign('Compatibility');m=new_map('Old map',7,7);d['maps']=[m]
    c=new_character('Captain',True,'Pathfinder 2e');c['stats']={'AC':'20','HP':'50'}
    d['roster']=[c];e=new_encounter('Fight');add_combatant(e,c['id']);d['encounters']=[e]
    d['book_outline']=suggest_outline(d)
    path=tmp_path/'project.campaign.json';save_campaign(d,path);loaded=load_campaign(path)
    assert loaded['maps'][0]['tiles']==m['tiles']
    pdf=tmp_path/'book.pdf';export_book(loaded,pdf)
    assert pdf.stat().st_size>2500

def test_scene_excerpt_retrieval_does_not_default_to_unrelated_appendix():
    from source_order import scene_context_excerpts
    text='The Search\nFirst investigate the guards.\n'+(' Other lore.'*3000)+'\nCouncil Meeting\nAldric asks for evidence.'
    excerpt=scene_context_excerpts(text,[('a','The Search'),('b','Council Meeting')])
    assert 'First investigate the guards' in excerpt
    assert 'Aldric asks for evidence' in excerpt
    assert 'SCENE a' in excerpt and 'SCENE b' in excerpt
