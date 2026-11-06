"""Safe, field-scoped editing requests for the Local and Greater Oracle.

A targeted request NEVER offers the entire project for editing. General
consultations continue to use the separate, existing context builder.
"""
from __future__ import annotations

import json
import re

from oracle_session import clean_markdown

FIELD_SYSTEM_INSTRUCTIONS = """You are an expert editor helping a tabletop RPG Dungeon Master.
The DM selected ONE text field to improve. Rewrite ONLY that field.
Other campaign information is BACKGROUND REFERENCE ONLY, not material to edit.
Preserve the existing facts, names, point of view, humor, secrecy, and authorial intent.
Do not add scenes, new characters, mechanics, quests, or unrelated material.
Keep the revision approximately the same length unless the DM explicitly asks for a different length.
If the field is blank, draft ONLY from source evidence that was supplied. Never invent plot or people to fill the gap.
Return ONLY the finished replacement text for that field. Absolutely no explanation,
commentary, questions, metadata, prompt repetitions, bullet-point feedback, or labels.
Never write words like FIELD, ORIGINAL TEXT, REVISED VERSION, or CAMPAIGN CONTEXT
as labels. Do not include Markdown headings or fences. This text will appear directly
in an editor and must be ready to paste without cleaning by the DM."""

DEFAULT_FIELD_REQUEST = (
    "Improve the selected text for clarity, readability and atmosphere while keeping "
    "its scope, established details and approximate length."
)

MAX_TARGET_CHARS = 17000


def make_field_context(data: dict, target: dict, include_refs: bool = False) -> str:
    """Small amount of *read-only* lore; no sprawling chapter bodies.

    The original field is supplied separately and is the only editable content.
    """
    bits = []
    for key, label, limit in (("title", "Campaign", 150), ("system", "System", 90),
                              ("tone", "Tone", 200)):
        value = str(data.get(key) or "").strip()
        if value:
            bits.append(f"{label}: {value[:limit]}")
    # Premise needs setting for factual consistency; other fields may also
    # benefit, but never give the model the full main story arc or chapters.
    if not (target.get("kind") == "overview" and target.get("key") == "setting"):
        setting = str(data.get("setting") or "").strip()
        if setting:
            bits.append("Setting (background only): " + setting[:850])
    # Provide names without story sections, where category-bearing lists exist.
    entries = data.get("entries") or []
    names = [str(item.get("title", "")).strip() for item in entries[:24]
             if isinstance(item, dict) and item.get("title")]
    if names:
        bits.append("Existing chapter / entity names (reference only): " + "; ".join(names)[:700])
    if include_refs:
        refs = data.get("references") or []
        if refs:
            item = refs[0]
            bits.append("Optional reference excerpt (reference only): " + str(item.get("text") or "")[:450])
    return "\n".join(bits) or "No background material supplied."


def field_request_messages(data: dict, request: str, target: dict, include_refs=False,
                           source_context="", source_grounded=False) -> list[dict]:
    original = str(target.get("baseline") or "")
    if len(original) > MAX_TARGET_CHARS:
        raise ValueError("This field is too long for a single field edit. Split this entry into smaller sections before using Improve with Oracle.")
    label = str(target.get("label") or "Selected field")[:200]
    instructions = (request or DEFAULT_FIELD_REQUEST).strip()
    if source_grounded:
        from oracle_grounding import SOURCE_RULES
        system = FIELD_SYSTEM_INSTRUCTIONS + "\n" + SOURCE_RULES
        if not original.strip() and not source_context.strip():
            raise InvalidFieldRevision("The field is blank and no readable source excerpts are available. Upload a manuscript under The Archives or enable the imported references, or explicitly choose Brainstorm mode.")
    else:
        system = FIELD_SYSTEM_INSTRUCTIONS
    body = ("EDITING TASK: Produce ONLY the complete replacement for this selected field.\n"
            f"Selected field name: {label}\n"
            "SOURCE DOCUMENT EXCERPTS (HIGHEST PRIORITY; REFERENCE ONLY):\n"
            + (source_context or "No source excerpts supplied") + "\n\n"
            "BACKGROUND LORE — DO NOT REWRITE OR COPY:\n"
            + make_field_context(data, target, False if source_grounded else include_refs) + "\n\n"
            "ONLY TEXT YOU MAY EDIT:\n"
            + (original or "(currently blank)") + "\n\n"
            "DM'S INSTRUCTIONS FOR THIS FIELD ONLY:\n"
            + instructions + "\n\nOUTPUT: Return only the replacement field text. No labels or other sections.")
    return [{"role": "system", "content": system},
            {"role": "user", "content": body}]


class InvalidFieldRevision(ValueError):
    """An Oracle response is not suitable for automatic placement in a field."""


def clean_field_revision(raw: str) -> str:
    """Strip *known* leaked prompt envelopes, never rewrite legitimate prose.

    Unclear responses are rejected rather than risking unrelated material being
    automatically placed in the user's authored field.
    """
    value = str(raw or "").strip()
    if not value:
        raise InvalidFieldRevision("The Oracle returned no revised field text.")
    if value.startswith("{"):
        try:
            result = json.loads(value)
        except (ValueError, TypeError):
            result = None
        if isinstance(result, dict):
            for key in ("revision", "revised_text", "replacement", "text"):
                if isinstance(result.get(key), str) and result[key].strip():
                    value = result[key].strip()
                    break
    value = re.sub(r"\A```(?:markdown|text)?\s*\n([\s\S]*?)\n```\s*\Z", r"\1", value, flags=re.I)
    # Many smaller models repeat the preamble followed by a recognizable
    # revision heading. Only discard the header portion in that case.
    marker = re.search(r"(?im)^\s*(?:REVISED(?:\s+(?:TEXT|VERSION|FIELD|PREMISE|DRAFT))?|"
                       r"IMPROVED(?:\s+(?:TEXT|VERSION|PREMISE|DRAFT))?|"
                       r"FINAL(?:\s+(?:TEXT|VERSION|PREMISE|DRAFT))?|"
                       r"NEW(?:\s+(?:TEXT|VERSION|PREMISE|DRAFT))?|"
                       r"POLISHED(?:\s+(?:TEXT|VERSION|PREMISE|DRAFT))?|"
                       r"SUGGESTED\s+(?:REVISION|VERSION|TEXT))\s*:\s*",
                       value)
    if marker and (marker.start() < 650 or re.search(r"(?im)^\s*(?:FIELD|ORIGINAL TEXT)\s*:", value[:marker.start()])):
        value = value[marker.end():].strip()
    # Remove simple heading prefixes at the start; these are not campaign prose.
    value = re.sub(r"\A\s*(?:FIELD\s*:\s*[^\n]+\n)+", "", value, flags=re.I)
    value = re.sub(r"\A\s*(?:(?:Here(?:'s| is) (?:the |a )?(?:revised|improved) (?:version|text|premise))\s*:\s*\n?)", "", value, flags=re.I)
    # If the model merely echoed our input prompt, do not approve it as a field.
    if re.search(r"(?im)^\s*(?:ORIGINAL TEXT|ONLY TEXT YOU MAY EDIT|DM'S INSTRUCTIONS FOR THIS FIELD ONLY|CAMPAIGN CONTEXT|BACKGROUND LORE)\s*:", value):
        raise InvalidFieldRevision(
            "The Oracle repeated its instructions instead of returning one clean field revision. "
            "No campaign writing was changed. Try Consult again.")
    value = clean_markdown(value)
    if not value:
        raise InvalidFieldRevision("The Oracle did not provide usable revision text.")
    return value


def validate_field_scope(revision: str, target: dict, request: str) -> str:
    """Reject obviously oversized whole-campaign answers for field-edit tasks.

    The DM can explicitly ask for expansion. An ordinary Improve action should
    never silently replace a two-paragraph Premise with an entire campaign.
    """
    original = str(target.get("baseline") or "").strip()
    if len(original) < 50:
        return revision  # a blank or one-line seed may reasonably need elaboration
    permitted_expansion = bool(re.search(
        r"\b(expand|longer|lengthen|elaborate|more detail|extend|additional paragraphs)\b",
        (request or "").lower()))
    if not permitted_expansion and len(revision) > max(1100, int(len(original) * 2.5)):
        raise InvalidFieldRevision(
            "The Oracle generated substantially more than the selected field requires. "
            "Nothing has been changed. Try Consult again or explicitly ask to expand the field.")
    return revision
