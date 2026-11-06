# Changelog

## v1.1.0-beta.1 — ComfyUI local Art Studio test build (2026-11-06)

- Added a **Generate Image (ComfyUI)** button inside Cartography, opening a dedicated Art Studio with positive/negative prompts, four starter presets, image size, steps, CFG and seed settings.
- Uses the verified seven-node SDXL Base 1.0 workflow supplied by the owner; it submits to a running **local** ComfyUI instance only after user approval. Detects local ports 8188/8000 or accepts another explicit loopback port. No AI model or cloud API is required.
- Polls the ComfyUI job, retrieves an output image, previews it, saves a PNG or copies it to campaign Archives. A map-background link is optional and requires confirmation.
- Added Comfy Desktop checkpoints folder help, tests and the project's approved CF crest as a Windows application icon.
- Local tests: 118 passed + 1 GUI test skipped without a display; with virtual display: 119 passed, including mocked ComfyUI generation / Archives import. **Actual ComfyUI Windows GPU/API integration still needs testing.**
- The new release is Python **source code** plus build scripts. No precompiled/signed Windows binary, models, Ollama, ComfyUI or API keys are bundled. No third-party binary distribution audit is claimed.

## v1.0.0 — First GitHub community beta (source package)

- Prepared public testing package with stable 1.0.0 version labels and GitHub issue templates.
- Continued v0.7.2 free PDF reading and rendering; no AI required for ordinary PDF tasks.
- Included beta/API/data/privacy warnings and source-available personal evaluation terms.
- Removed local caches, smoke-only development scripts, and all personal example project files from the release.
- AI models, Ollama, ComfyUI, GPU drivers and API credentials are not bundled.
- No compiled/signed Windows binary is included in this initial public source release.

## v0.7.2 — Free PDF library compatibility (review candidate; not public)

- Removed runtime dependency on PyMuPDF; replaced PDF text extraction with `pypdf` and PDF rendering with `pypdfium2`.
- Updated character-sheet PDF imports, vision-page preprocessing, and full/selected Book Preview without requiring local AI for ordinary PDF operations.
- Replaced old PDF-specific dependency messages and updated source-package licensing notices.
- Added regression checks for PDF text import, image rendering and absence of PyMuPDF in active application code.
- Application source licensing and full license/asset review remain open before a public GitHub release.


## v0.7.1 — Reliability & Creative Tools Update

- Fixed Roster Save/New/Import buttons being clipped at ordinary window heights by placing essential controls above a scrolling combat editor.
- Rebuilt blank/hidden character-stat import review as a labeled Treeview with visible Apply and Cancel actions; expanded inline labeled-stat extraction.
- Fixed Archives filename search for image-only documents and added explicitly named, local-only archived-image descriptions via vision-capable Ollama.
- Added restricted Oracle Plan project edits / Undo actions with validation, a preview and explicit DM confirmation (no code execution).
- Added entire-book preview shortcut, player-safe/DM-only outline categories for new templates and non-destructive duplicate-content warnings.
- Added map prop resizing, rotation and grid footprints, plus validated custom image prop imports copied to The Archives.
- Added guided optional ComfyUI and SDXL Base 1.0 model installation/download, with resume and SHA256 verification. Actual generation is in external ComfyUI, not yet in Campaign Forge.
- Preserved v0.7.0 JSON project compatibility and existing archives. Backend tests and Linux virtual desktop checks performed; actual Windows/Ollama still requires user testing.

# Campaign Forge v0.7.0 — Creator Studio

- New original dark studio theme with compact geometric header and modern brass/teal navigation.
- Structured character combat editor with per-field inputs and system-specific field visibility, without changing legacy saved stats.
- Reviewed import of labeled stats from PDF/TXT; optional, local-only Ollama vision import of first scanned page or JPEG/PNG/WebP with explicit approval.
- In-app PDF book proof with zoom/navigation and selected-section preview; temporary proof files are deleted on closing the window.
- Original-manuscript heading ordering and optional Local Oracle scene-order suggestions with strict ID validation and explicit confirmation.
- Cartography background-image import via Archives, editable vector props and terrain overlays, high-resolution PNG export, plus corresponding PDF map integration.
- Existing 0.6.x projects, Archives, Encounter Builder, Oracle source precedence, diagnostic import and saves remain supported.
- Deliberately not included: full local image generation, paid art library downloads, automated web rules research, Hero Lab Classic `.por` support, or one-click diagnostic bundle.

# Campaign Forge v0.6.1 — Source-First Oracle Patch

- Uploaded manuscript passages now take precedence over AI-generated campaign notes when source-grounded writing is selected.
- Automatically enable reference and Archives search for new consultations; users retain opt-out controls.
- Introduce a selectable **Use uploaded lore** versus **Brainstorm new ideas** mode.
- Separate **Revise selected field** from **Ask / explain (no edits)**; attribution questions now use recent conversation context.
- For empty-field source-based drafts, require an exact supporting source quotation and reject unsupported named entities or unverifiable replies (local model retries once).
- Transcript shows which original source documents supplied excerpts; citations are advisory rather than guarantees.
- Preserve v0.6.0 Book Architect, Archives, Roster & Bestiary, and Cartography.

# v0.6.0 — Archives, Roster, and Book Architect

- Added local Archives, campaign/shared scope, keyword search, explicit Oracle excerpt retrieval, manual book link, and backup/restore.
- Added Roster & Bestiary with optional combat statistics, basic JSON importing, legacy NPC copying, and reusable linked combatants in Encounter Builder.
- Added rule-system-aware stat label templates and approved external reference links (no automatic browsing).
- Rebuilt publishing around an editable book outline and suggested D&D, Pathfinder, setting-guide, and DM-binder templates.
- Added structured combat and noncombat PDF output; explicit image Archive attachments can appear in DM exports.
- Preserved v0.5.2 project format and existing importer/Oracle integration.
- Not yet available: validated Hero Lab schema handling, `.por` import, mechanics balancing, OCR, web research, or advanced cartography.

# v0.5.2 — Field-only Oracle revisions and safer project saves (released)

- Use the campaign title as the suggested name for a new `.campaign.json` file instead of `my-campaign`.
- Add a visible **Save As** toolbar control and Ctrl+Shift+S shortcut for creating a separate version.
- Suggest sequential `v2`, `v3`, etc. filenames instead of defaulting to an existing project file.
- Remember the most recently used project folder locally (no campaign content stored in recent-project metadata).
- Save (Ctrl+S) updates an opened/saved project without opening the Save As dialog every time; Save As creates a separate file.
- Display the active project filename in the app window title, with an asterisk for unsaved changes.
- A failed Save As leaves the previous project's save destination untouched.
- First save still requires explicit user selection; importing a DOCX does not silently guess which saved JSON is the same campaign.


- Separate "Improve with Oracle" from general whole-campaign consultation.
- Send only the selected field as editable text, with a brief read-only lore reference.
- Remove internal FIELD / ORIGINAL TEXT markers from the editable question.
- Parse common model response wrappers and reject echoed internal instructions.
- Retry malformed local field revisions once; reject clearly oversized replies by default.
- Preserve side-by-side comparison, Append, Replace, Undo and other campaign content.

# v0.5.1 — Handout category support

- Recognize Handout as a native category across the importer, Chronicles, and PDF publishing.
- Map handout/handouts/illustration/visual reference/map image AI values without the six false “unknown category” warnings seen in the example campaign.
- Include Handout among the AI organizer category choices; no AI model or API changes.
- DOCX embedded-image extraction is not included; only extractable text and captions are imported.

# Release notes

## 0.5.0 — Writing Studio

- Added field-linked Improve with Oracle for Premise, Setting, Main Story Arc and Chronicle entries.
- Added user-approved side-by-side append/replace comparisons, merge consultation and field Undo.
- Added current-session scrollable transcript, clean text copying, export .txt and exit-time save/discard prompt.
- Added per-notice opt-out with local settings.
- Cleaned Markdown markers in displayed and copied replies; adjusted writing prompts.
- Rebuilt header and navigational icon assets at higher quality; collapsible Oracle setup panel.
- Kept all v0.4.0 recovery/diagnostic and download-progress functionality.
- Did not implement future Help → Report a Problem diagnostics bundling.

# Campaign Forge — Release history

## v0.4.0 — Import resilience and workspace refresh
- Retry a malformed AI manuscript passage one time; preserve recoverable replies.
- Keep failed passages as unselected Needs Review entries instead of discarding prior successful passages.
- Record local diagnostic summaries with limited raw AI responses; diagnostics may contain private campaign excerpts.
- Normalize common plural/case variations of campaign categories while keeping uncertain secret material DM-only.
- Add the Import Analysis Report viewer to see warnings without an excessively long status line.
- Shorter, uninterrupted weathered-map header with built-in rounded utility buttons and icon-backed tabs.
- Main workspace scrollbar independent of in-editor text/list scrolling.
- Help window (F1) with plain-language documentation for all five primary sections.
- Automated regression test for malformed final passage and a virtual desktop UI check.

## v0.3.4 — Long manuscripts
- Split local-AI manuscript analysis into manageable passages with progress and cancellation.

## v0.3.3 — Download diagnostics
- Model download speed in MB/s and Mbps, with live progress and status.
