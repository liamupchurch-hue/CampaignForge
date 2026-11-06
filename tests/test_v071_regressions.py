from pathlib import Path
import tempfile,sys,pytest
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forge_library import Archive
from archive_vision import match_requested_image
from character_sheets import parse_sheet_text
from campaign_data import new_campaign,new_entry,new_map
from forge_book import suggest_outline
from project_actions import normalize_plan,apply_actions,summarize_actions
from map_tools import render_map,export_map
from book_quality import quality_findings


def test_archives_match_image_filenames_and_prefixes(tmp_path):
    library=Archive(tmp_path/'lib');project='this-campaign'
    pic=tmp_path/'Secure Docks of Hollowford.png';Image.new('RGB',(200,120),'red').save(pic)
    other=tmp_path/'Blackreef Harbor.png';Image.new('RGB',(200,120),'blue').save(other)
    library.add(pic,'campaign',project);library.add(other,'campaign',project)
    assert len(library.search('Sec',project))==1
    assert len(library.search('Secure',project))==1
    assert len(library.search('Docks',project))==1
    assert library.search('Secure Docks',project)[0]['name']==pic.name
    assert match_requested_image(library,project,'Please describe the file labeled Secure Docks in Archives')['name']==pic.name


def test_text_sheet_inline_and_separate_rows():
    result=parse_sheet_text('AC: 21\nHP: 145\nSTR: 13\nCHA: 14\nSpeed: 30 ft\nAC 20, HP 70')
    assert result['AC']=='21' and result['HP']=='145' and result['CHA']=='14'
    assert result['Speed']=='30 ft'


def example_project():
    d=new_campaign('Hollowford');a=new_entry('Quest','The Search','Collect evidence.');b=new_entry('Chapter','Council Meeting','After Captain Rowan is defeated.')
    d['entries']=[a,b];d['book_outline']=suggest_outline(d);return d,a,b


def test_project_edits_only_approved_fields_and_undo_snapshot():
    project,a,b=example_project()
    original=__import__('copy').deepcopy(project)
    sections={s['title']:s for s in project['book_outline']['sections']}
    sid=sections['Adventure Chapters']['id']
    changes=[{'op':'reorder_section','section_id':sid,'ordered_ids':[b['id'],a['id']]},
             {'op':'update_field','field':'pitch','value':'Corruption in a trade city.'}]
    clean=normalize_plan({'changes':changes},project)
    outcome=apply_actions(project,clean)
    assert project==original
    assert [n['id'] for n in next(s for s in outcome['book_outline']['sections'] if s['id']==sid)['nodes']]==[b['id'],a['id']]
    assert outcome['pitch']=='Corruption in a trade city.'
    assert 'REORDER' in summarize_actions(project,clean)


def test_project_change_rejects_command_and_missing_nodes():
    p,a,b=example_project();sid=next(s for s in p['book_outline']['sections'] if s['title']=='Adventure Chapters')['id']
    with pytest.raises(ValueError):normalize_plan({'changes':[{'op':'run_python','code':'import os'}]},p)
    with pytest.raises(ValueError):normalize_plan({'changes':[{'op':'reorder_section','section_id':sid,'ordered_ids':[a['id']]}]},p)
    with pytest.raises(ValueError):normalize_plan({'changes':[{'op':'move_entry','entry_id':'fake','section_id':sid,'position':0}]},p)


def test_new_outline_splits_player_lore_from_secrets():
    p=new_campaign();p['entries']=[new_entry('Location','Stone Market','Market',False),new_entry('Secret','Magia Nati','Hidden plan',True)]
    outline=suggest_outline(p)
    sections={s['title']:{n['id'] for n in s['nodes']} for s in outline['sections']}
    assert p['entries'][0]['id'] in sections['Player Guide']
    assert p['entries'][1]['id'] in sections['Setting & DM Background']


def test_repeated_entries_flagged_without_auto_deletion():
    p=new_campaign();p['entries']=[new_entry('Item','Hourglass of Haste','It freezes time for one round.'*5),new_entry('Item','Hourglass of Haste','It freezes time for one round.'*5)]
    assert quality_findings(p)
    assert len(p['entries'])==2


def test_custom_image_prop_size_and_rotation(tmp_path):
    m=new_map('Old docks',12,10)
    prop=tmp_path/'table.png';Image.new('RGBA',(200,75),(200,0,0,255)).save(prop)
    m['objects']=[{'kind':'Custom','x':4,'y':4,'w':2,'h':1,'rotation':90,'asset_archive_id':'ref'}]
    rendered=render_map(m,size=32,grid=False,asset_resolver=lambda i:prop)
    assert rendered.size==(384,320)
    assert rendered.getpixel((4*32+32,4*32+10))!=(214,205,186)
    dest=tmp_path/'out.png';export_map(m,dest,asset_resolver=lambda i:prop)
    assert dest.exists()


def test_sd_xl_download_resumable_and_hash_verified(tmp_path,monkeypatch):
    import hashlib
    import image_setup as im
    data=b'mock checkpoint bytes'
    monkeypatch.setattr(im,'MODEL_SHA256',hashlib.sha256(data).hexdigest())
    root=tmp_path/'models'/'checkpoints';root.mkdir(parents=True)
    target=root/im.MODEL_FILE
    class Reply:
        def __init__(self):
            self.status=200;self.headers={'Content-Length':str(len(data))};self.i=0
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):
            if self.i:return b''
            self.i=1;return data
    class Opener:
        def open(self,*args,**kwargs):return Reply()
    updates=[]
    out=im.download_checkpoint(target,lambda message,pct:updates.append((message,pct)),__import__('threading').Event(),Opener())
    assert out.exists() and out.read_bytes()==data
    assert not target.with_name(target.name+'.part').exists()
    assert updates[-1][1]==100
