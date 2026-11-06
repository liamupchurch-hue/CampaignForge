import copy, json, sys, zipfile
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forge_library import Archive
from forge_roster import new_character,new_encounter,add_combatant,import_json_characters
from forge_book import suggest_outline,node_title,outline_node_ids
from campaign_data import new_campaign,new_entry,save_campaign,load_campaign
from pdf_book import export_book
from pypdf import PdfReader

def test_archive_scope_search_backup(tmp_path):
    a=Archive(tmp_path/'store');p=tmp_path/'rules.txt';p.write_text('A flaming ward blocks a doorway.\nThe silver bridge holds.',encoding='utf8')
    public_id=a.add(p,'shared','',category='Rules')
    private_id=a.add(p,'campaign','campaign-123',category='Lore')
    assert len(a.list('campaign-123'))==2
    assert len(a.list('other-campaign'))==1
    assert len(a.search('flaming ward','campaign-123'))==2
    with pytest.raises(PermissionError):a.get(private_id,'another-campaign')
    zip_path=tmp_path/'backup.zip';a.backup(zip_path)
    with zipfile.ZipFile(zip_path) as z:
        assert 'archive_manifest.json' in z.namelist()
        assert len([s for s in z.namelist() if s.startswith('files/')])==2
    a.delete(private_id,'campaign-123')
    assert len(a.list('campaign-123'))==1
    restored=Archive(tmp_path/'new-store')
    assert restored.restore(zip_path)==2
    assert restored.get(private_id,'campaign-123')['text_content'].startswith('A flaming ward')

def test_roster_encounter_links_and_import(tmp_path):
    c=new_character('Captain Rowan',True,'Pathfinder 2e');c['stats']={'AC':'23','HP':'76'}
    e=new_encounter('Dock confrontation');add_combatant(e,c['id'],2);add_combatant(e,c['id'],1)
    assert e['combatants']==[{'character_id':c['id'],'count':3}]
    path=tmp_path/'export.json';path.write_text(json.dumps({'characters':[{'name':'Grog','AC':16,'HP':25,'bio':'Guard'}]}))
    imported=import_json_characters(path,'D&D 5e (2024)')
    assert imported[0]['name']=='Grog' and imported[0]['stats']['AC']=='16'
    assert 'review' in imported[0]['source'].lower()

def test_outline_and_project_reopen(tmp_path):
    p=new_campaign('The Ashen Compass');p['entries']=[new_entry('Quest','The Search','Find the ledger'),new_entry('Chapter','Council Meeting','Talk to Aldric')]
    outline=suggest_outline(p,'Pathfinder Adventure')
    nodes=[n for s in outline['sections'] for n in s['nodes']]
    assert ('entry',p['entries'][0]['id']) in outline_node_ids(outline)
    p['book_outline']=outline
    path=tmp_path/'midnight.campaign.json';save_campaign(p,path)
    d=load_campaign(path)
    assert d['project_id']==p['project_id']
    assert d['book_outline']['sections'][0]['title']=='Adventure Overview'
    # Old files from v0.5.2 remain readable.
    prior={k:v for k,v in p.items() if k not in ('project_id','book_outline','book_template','roster','encounters')}
    prior_path=tmp_path/'old.json';prior_path.write_text(json.dumps(prior))
    old=load_campaign(prior_path)
    assert 'project_id' in old and 'roster' in old and 'book_outline' in old

def test_pdf_chronology_combat_noncombat_and_archive(tmp_path):
    d=new_campaign('The Test Adventure');d['pitch']='A port city mystery.'
    q1=new_entry('Quest','The Search','Beginning of the investigation.')
    q2=new_entry('Chapter','The Council Meeting','After the search ends.')
    d['entries']=[q1,q2]
    npc=new_character('Tuk',False,'Pathfinder 2e');npc['bio']='Tavern keeper.';npc['stats']={'AC':'999'}
    guard=new_character('Town Guard',True,'Pathfinder 2e');guard['stats']={'AC':'20','HP':'40','Strike':'+12'}
    d['roster']=[npc,guard]
    enc=new_encounter('Dock Fight');enc['description']='Fog covers the pier.';add_combatant(enc,guard['id'],3);d['encounters']=[enc]
    d['book_outline']=suggest_outline(d,'Pathfinder Adventure')
    a=Archive(tmp_path/'archives');art=tmp_path/'map.png'
    from PIL import Image as PILImage
    PILImage.new('RGB',(1000,600),'white').save(art)
    ident=a.add(art,'campaign',d['project_id'],category='Maps')
    section=next(s for s in d['book_outline']['sections'] if s['title']=='Maps & Handouts')
    section['nodes'].append({'type':'archive','id':ident})
    pdf=tmp_path/'book.pdf';export_book(d,pdf,archive=a)
    assert pdf.exists() and pdf.stat().st_size>3000
    text=' '.join(p.extract_text() for p in PdfReader(str(pdf)).pages)
    assert 'The Search' in text and text.index('Beginning of the investigation')<text.index('After the search ends')
    assert 'Tuk' in text and 'Tavern keeper' in text and '999' not in text
    assert 'Dock Fight' in text and 'Town Guard' in text
    assert 'AC: 20' in text
    assert len(PdfReader(str(pdf)).pages)>=3
