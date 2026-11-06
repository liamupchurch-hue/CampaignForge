"""Conservative, review-first character-sheet extraction for Campaign Forge.

Never fills missing numbers, never interprets a game rule, and never sends data
outside localhost. Image understanding requires a user-installed local vision model.
"""
from __future__ import annotations
import base64, io, json, re, urllib.request
from pathlib import Path
from PIL import Image

# Keys are intentionally rules-neutral. The caller displays unknown fields for review.
ALIASES = {
    'armor class':'AC', 'armour class':'AC', 'ac':'AC',
    'hit points':'HP', 'hit point':'HP', 'hp':'HP',
    'fortitude':'Fortitude', 'reflex':'Reflex', 'will':'Will',
    'perception':'Perception', 'speed':'Speed', 'movement':'Speed',
    'level':'Level', 'challenge rating':'Challenge', 'challenge':'Challenge', 'cr':'Challenge',
    'strength':'STR', 'dexterity':'DEX', 'constitution':'CON',
    'intelligence':'INT', 'wisdom':'WIS', 'charisma':'CHA',
    'str':'STR', 'dex':'DEX', 'con':'CON', 'int':'INT', 'wis':'WIS', 'cha':'CHA',
    'attack':'Attack', 'strike':'Strike', 'damage':'Damage',
    'skills':'Skills', 'saving throws':'Saving Throws',
}
FIELDS = tuple(dict.fromkeys(ALIASES.values()))
MAX_PAGES = 4
MAX_FILE_MB = 24


def extract_text_file(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>MAX_FILE_MB*1024*1024:
        raise ValueError('Character sheet file is missing or too large (24 MB maximum).')
    suffix=path.suffix.lower()
    if suffix=='.pdf':
        from pypdf import PdfReader
        reader=PdfReader(str(path),strict=False)
        if reader.is_encrypted:
            try: reader.decrypt('')
            except Exception as exc: raise ValueError('The PDF is encrypted. Please unlock it before importing.') from exc
        return '\n'.join((page.extract_text() or '') for page in reader.pages[:MAX_PAGES])[:50000]
    if suffix in ('.txt','.md'):
        return path.read_text(encoding='utf-8-sig',errors='replace')[:50000]
    raise ValueError('Selectable-text extraction supports PDF, TXT, and MD. Images require Local Oracle vision.')


def parse_sheet_text(text):
    """Find clearly labelled values without inventing any statistics."""
    if not isinstance(text,str):raise TypeError('Text must be a string')
    results={}; lines=text.splitlines()
    # Also accept clear inline labels such as "AC 17, HP 42, Speed 30 ft".
    inline=re.compile(r'\b(AC|HP|STR|DEX|CON|INT|WIS|CHA|CR)\s*[:=]?\s*([+\-]?\d+(?:\s*ft)?)\b',re.I)
    for line in lines:
        if len(line)>300:continue
        matches=list(inline.finditer(line))
        for match in matches:
            label=ALIASES.get(match.group(1).lower())
            if label and label not in results:results[label]=match.group(2).strip()
    for line in lines:
        line=line.strip().strip('•')
        if not line or len(line)>250:continue
        match=re.match(r'^([A-Za-z][A-Za-z /]{0,30})\s*[:\-]\s*([^\r\n]+)$',line)
        if not match:
            # Explicit common inline short labels such as AC 18, HP 38
            match=re.match(r'^(AC|HP|STR|DEX|CON|INT|WIS|CHA|CR)\s+([+\-]?\d[\w\s+\-/().]*)$',line,re.I)
        if not match:continue
        label=match.group(1).strip().lower()
        canonical=ALIASES.get(label)
        if not canonical:continue
        value=match.group(2).strip().rstrip(';,')
        if not value or len(value)>100:continue
        # Require numeric evidence on numeric fields; never manufacture a number.
        if canonical in {'AC','HP','Level','Challenge','Fortitude','Reflex','Will','Perception','STR','DEX','CON','INT','WIS','CHA'} and not re.search(r'\d',value):
            continue
        results.setdefault(canonical,value)
    return results


def image_payload(path):
    """Resizes user-selected picture/pages for locally running vision model."""
    path=Path(path)
    if not path.is_file() or path.stat().st_size>MAX_FILE_MB*1024*1024:
        raise ValueError('Image must be 24 MB or smaller.')
    if path.suffix.lower()=='.pdf':
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(str(path))
        try:
            if not len(doc): raise ValueError('Empty PDF')
            page=doc[0]
            try:
                bitmap=page.render(scale=1.7)
                try: img=bitmap.to_pil().convert('RGB')
                finally: bitmap.close()
            finally: page.close()
        finally: doc.close()
    elif path.suffix.lower() in ('.jpg','.jpeg','.png','.webp'):
        img=Image.open(path).convert('RGB')
    else:raise ValueError('Supported image formats: PNG, JPEG, WebP, or PDF page 1.')
    img.thumbnail((1700,1700),Image.Resampling.LANCZOS)
    buff=io.BytesIO();img.save(buff,format='JPEG',quality=82,optimize=True)
    return base64.b64encode(buff.getvalue()).decode('ascii')


def parse_vision_result(answer):
    """Accept only explicit key/value pairs. Unknown keys ignored, no inference."""
    if isinstance(answer,str):
        stripped=answer.strip()
        if stripped.startswith('```'):
            stripped=re.sub(r'^```(?:json)?\s*|\s*```$', '', stripped, flags=re.I)
        try:obj=json.loads(stripped)
        except json.JSONDecodeError:return parse_sheet_text(answer)
    else:obj=answer
    if not isinstance(obj,dict):return {}
    obj=obj.get('stats',obj)
    if not isinstance(obj,dict):return {}
    out={}
    for key,val in obj.items():
        canonical=ALIASES.get(str(key).strip().lower())
        if canonical and isinstance(val,(str,int,float)):
            value=str(val).strip()[:100]
            if value and value.lower() not in ('null','unknown','n/a','not shown'):
                if canonical in {'AC','HP','Level','Challenge','Fortitude','Reflex','Will','Perception','STR','DEX','CON','INT','WIS','CHA'} and not re.search(r'\d',value):continue
                out[canonical]=value
    return out


def recognize_local_vision(path, model, timeout=180):
    """Opt-in Ollama localhost image extraction. No cloud fallback."""
    if not model or not re.fullmatch(r'[\w.\-:/]+', model):raise ValueError('Choose a local Ollama vision-capable model.')
    pic=image_payload(path)
    prompt=('Read only fields explicitly visible on this tabletop RPG character sheet. '
            'Return ONLY a JSON object mapping printed field labels to their literal values. '
            'Recognize AC, HP, Level, Challenge, Perception, Fortitude, Reflex, Will, Speed, '
            'STR, DEX, CON, INT, WIS, CHA, Attack, Strike, Damage. '
            'Never invent or calculate missing numbers. Omit missing or illegible fields. '
            'Copy the characters precisely. Do not infer game system.')
    body={'model':model,'stream':False,'messages':[{'role':'user','content':prompt,'images':[pic]}],
          'options':{'temperature':0}}
    req=urllib.request.Request('http://127.0.0.1:11434/api/chat',
                               data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req,timeout=timeout) as response:
        content=json.loads(response.read(2*1024*1024).decode('utf-8'))
    return parse_vision_result(content.get('message',{}).get('content',''))
