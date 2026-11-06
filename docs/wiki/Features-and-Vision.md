# Features and Vision

## The idea behind Campaign Forge

Campaign planning is often spread across documents, spreadsheets, maps, character sheets, notes, and creative tools. Campaign Forge aims to make those pieces feel like **one coherent workshop**.

Rather than replacing a Game Master's imagination, the application should make it easier to preserve, connect, revise, and publish their ideas.

Our guiding goals are:

- **One creative workspace:** lore, locations, plots, characters, encounters, maps, and source material.
- **Creator control:** the user—not an AI model—decides what becomes part of the campaign.
- **Useful without AI:** core project editing, Archives, and PDF production must work without model downloads or subscriptions.
- **Optional assistance:** locally installed AI and explicitly configured external services can help with writing, organization, and artwork.
- **Portable, durable projects:** campaigns and linked assets should survive updates and moves between computers.
- **A satisfying final product:** an organized, readable campaign book rather than a collection of disconnected notes.

## Current public beta (v1.0.0)

| Area | Current capability |
| --- | --- |
| Campaign editing | Create, organize, save, and reopen campaign material |
| The Archives | Keep manuscript/reference material and images; separate backup required |
| Roster & Bestiary | Record narrative characters and optional combat statistics |
| Encounters | Link existing character/creature records to encounters |
| Cartography | Map backgrounds, terrain, grid props, markers, and image export |
| Book Architect | Organize material, preview sections and full books, export PDF |
| The Oracle | Optional local Ollama or separately configured external API assistance |
| Character-sheet import | Partial text extraction and optional reviewed image interpretation |

These features are in an **experimental source beta**, so individual workflows still need polish, bug fixes, and comprehensive Windows testing.

## Experimental work, not yet part of v1.0.0

The [Art Studio development work](https://github.com/liamupchurch-hue/CampaignForge/pull/2) connects to an independently installed local ComfyUI instance. It explores positive/negative prompts, Low/Medium/High presets, model-status checks, image preview, and saving generated artwork to The Archives.

SDXL generation has been tested by the project owner. FLUX and Z-Image workflow support is **experimental**, depends on compatible model components, and needs further live GPU testing. Changing the selected model must never silently substitute another one.

## What Campaign Forge is *not* yet

- A fully automated D&D or Pathfinder rules-validation engine.
- A replacement for a virtual tabletop (VTT).
- A guaranteed accurate AI writer, character-sheet reader, or chronological editor.
- A fully portable one-file campaign package.
- A signed, tested, commercially ready Windows installer.
- A Steam product currently available for purchase.

## The end goal

The intended first polished release is a **Windows desktop campaign-creation and publishing tool** that feels welcoming to a nonprogrammer. A successful release should be installable, reasonably accessible, reliable with user data, simple to back up, and honest about the limitations of optional AI.

A future Steam launch is a **goal, not a promise or scheduled date**. Core stability, safe saves, distribution rights, and real-user testing come before store publication.

For the detailed engineering checklist, see [Steam Ready Checklist](https://github.com/liamupchurch-hue/CampaignForge/blob/main/STEAM_READY_CHECKLIST.md).
