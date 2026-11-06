"""Portable JSON campaign document model. No network, database, or account required."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

SCHEMA_VERSION = 1
CATEGORIES = ["Chapter", "Quest", "NPC", "Location", "Encounter", "Faction", "Item", "Lore", "Secret", "Session Notes", "Handout"]
SYSTEMS = ["D&D 5e (2014)", "D&D 5e (2024)", "Pathfinder 2e (Remaster)", "Pathfinder 2e (Legacy)", "Pathfinder 2e", "System-neutral", "Other"]


def new_campaign(title="Untitled Campaign"):
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": str(uuid.uuid4()),
        "roster": [],
        "encounters": [],
        "book_outline": None,
        "book_template": "Pathfinder Adventure",
        "title": title,
        "author": "",
        "system": "System-neutral",
        "levels": "",
        "tone": "",
        "pitch": "",
        "setting": "",
        "story_arc": "",
        "entries": [],
        "references": [],
        "maps": [],
    }


def new_entry(category="Chapter", title="New Entry", content="", gm_only=False):
    return {"id": str(uuid.uuid4()), "category": category, "title": title,
            "content": content, "gm_only": bool(gm_only)}


def new_map(title="New Map", cols=24, rows=16):
    if not (4 <= cols <= 60 and 4 <= rows <= 60):
        raise ValueError("Map dimensions must each be between 4 and 60.")
    return {"id": str(uuid.uuid4()), "title": title, "cols": cols, "rows": rows,
            "tiles": [["floor" for _ in range(cols)] for _ in range(rows)]}


def validate_campaign(data):
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("This is not a supported Campaign Forge project file (schema version 1 required).")
    # Older v0.5.x projects load unchanged; new features are initialized on open.
    data.setdefault('project_id',str(uuid.uuid4()))
    data.setdefault('roster',[])
    data.setdefault('encounters',[])
    data.setdefault('book_outline',None)
    data.setdefault('book_template','Pathfinder Adventure')
    for key in ("title", "entries", "references", "maps"):
        if key not in data:
            raise ValueError(f"Project file is missing required field: {key}")
    if not isinstance(data["entries"], list) or not isinstance(data["maps"], list):
        raise ValueError("The project's entry or map data is invalid.")
    for m in data["maps"]:
        cols, rows = m.get("cols", 0), m.get("rows", 0)
        if not isinstance(cols, int) or not isinstance(rows, int) or not (4 <= cols <= 60 and 4 <= rows <= 60):
            raise ValueError("A map has unsupported dimensions.")
        if len(m.get("tiles", [])) != rows or any(len(row) != cols for row in m["tiles"]):
            raise ValueError("A map's grid is malformed.")
    return data


def save_campaign(data, path):
    validate_campaign(data)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Write-then-replace guards against partially written project files.
    temp = dest.with_name(dest.name + ".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(dest)


def load_campaign(path):
    content = Path(path).read_text(encoding="utf-8")
    return validate_campaign(json.loads(content))


def sample_campaign():
    d = new_campaign("The Ashen Compass")
    d.update(author="Example Creator", system="System-neutral", levels="1–5",
             tone="Mystery and exploration",
             pitch="A compass points not north, but toward what its bearer most regrets.",
             setting="The coastal city of Greywake sits beside a sea that sometimes forgets its tide.",
             story_arc="The party recovers a peculiar compass, follows its shifting bearing, and discovers why the lighthouse went dark.")
    d["entries"] = [
        new_entry("Chapter", "Chapter One: The Unlit Lighthouse", "The party arrives during the annual Lantern Festival. Every flame goes out at midnight.\n\nOpening scene: The keeper's daughter offers a reward for finding her missing father."),
        new_entry("NPC", "Mara Venn, Harbor Cartographer", "Goal: Keep her father's disappearance secret.\nMannerism: Always checks the horizon before answering.\nClue: Her maps show a coastline that should not exist."),
        new_entry("Encounter", "The Drowned Archive", "Location: Flooded basement beneath the lighthouse.\nThreat: Unstable walkways and an unknown guardian.\nChoice: Rescue a trapped scholar or preserve the evidence."),
        new_entry("Secret", "The Keeper's Bargain", "The missing keeper once traded the town's memories for calm seas.", True),
    ]
    m = new_map("Lighthouse Cellar", 18, 12)
    for x in range(18):
        m["tiles"][0][x] = "wall"
        m["tiles"][11][x] = "wall"
    for y in range(12):
        m["tiles"][y][0] = "wall"
        m["tiles"][y][17] = "wall"
    for y in range(5, 11):
        for x in range(9, 17):
            m["tiles"][y][x] = "water"
    m["tiles"][0][8] = "door"
    d["maps"] = [m]
    return d
