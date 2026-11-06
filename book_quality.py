"""Non-destructive book diagnostics for DM review, never automatic rewriting."""
from __future__ import annotations
from difflib import SequenceMatcher
import re


def _normalize(s):return re.sub(r'\s+',' ',re.sub(r'[^\w\s]',' ',str(s).casefold())).strip()


def quality_findings(data):
    findings=[]
    entries=data.get('entries',[])
    by_title={}
    for e in entries:
        title=_normalize(e.get('title',''))
        if title and title in by_title:
            findings.append(f"Repeated entry title: {e.get('title')} (separate records). Check for duplication.")
        by_title[title]=e
        text=_normalize(e.get('content',''))
        # Detect repeated substantive lines/paragraphs in the same imported entry.
        paragraphs=[_normalize(s) for s in re.split(r'\n\s*\n',e.get('content','')) if len(_normalize(s))>=75]
        if len(paragraphs)!=len(set(paragraphs)):
            findings.append(f"Repeated paragraph within '{e.get('title','')}'; review import before publishing.")
        sentences=[_normalize(s) for s in re.split(r'(?<=[.!?])\s+',e.get('content','')) if len(_normalize(s))>75]
        if len(sentences)!=len(set(sentences)):
            findings.append(f"Repeated description in '{e.get('title','')}'; review source versions.")
    # Compare related items for potentially duplicated mechanics.
    items=[e for e in entries if e.get('category')=='Item']
    for i,a in enumerate(items):
        for b in items[i+1:]:
            a_text=_normalize(a.get('content',''));b_text=_normalize(b.get('content',''))
            if len(a_text)>100 and len(b_text)>100 and SequenceMatcher(None,a_text,b_text,autojunk=True).ratio()>.86:
                findings.append(f"Possible duplicate item descriptions: '{a['title']}' and '{b['title']}'.")
                if len(findings)>=30:return findings
    return findings
