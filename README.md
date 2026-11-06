# Campaign Forge v1.1.0-beta.1 — Local Art Studio Test Build

> **EXPERIMENTAL SOURCE TEST BUILD — NOT A PUBLICLY AUDITED WINDOWS RELEASE.** Back up campaigns and Archives before testing. The original v1.0.0 source beta and its historical release notes are retained below. There is no ready-built Windows .exe in this ZIP; build a local exe using the Windows script if desired.

## NEW: ComfyUI AI Art Studio (v1.1.0-beta.1)

This test build introduces a **Generate Image (ComfyUI)** button inside **Cartography**. It opens a separate Art Studio with positive and negative prompt fields, four starter art types, model dropdown, image sizes, seed/steps/CFG, preview, PNG export and optional **Add to The Archives**. Map backgrounds are changed **only after you approve**.

**Quick local test:**

1. Download/extract this ZIP as a **new** folder; do not overwrite your working v1.0.0 installation.
2. On Windows, run `start_windows.bat` to install the existing Python dependencies locally and launch Campaign Forge, or run `build_windows.bat` after setup to build your own `dist\CampaignForge\CampaignForge.exe` executable (copy the whole folder).
3. Independently open **Comfy Desktop** and start your instance with the **SDXL Base 1.0** checkpoint already installed. ComfyUI, model files and GPU drivers are **not bundled**.
4. In Campaign Forge open **Cartography → Generate Image (ComfyUI)**. It checks **localhost ports 8188 and 8000**; if needed manually enter another local URL such as `http://127.0.0.1:8188` and click **Find / Connect**.
5. Confirm the `sd_xl_base_1.0.safetensors` checkpoint appears, enter a positive and negative prompt, choose **Generate Image**, approve the local GPU job, review the preview, then optionally save as PNG or copy to The Archives.
6. If you selected a map and generated a **Map background**, Campaign Forge can link the image to the map after a second approval. Save the campaign JSON separately. Archives copies must be included in backups.

**Limitations:** Live API execution on the owner's Windows installation remains **unverified**; a simulated ComfyUI endpoint and GUI have been tested. The Art Studio does not install or manage ComfyUI, provide cloud generation, use custom nodes, import a full instance, or guarantee accurate maps/text. Clicking **Stop waiting** does not cancel a queued ComfyUI GPU task. First generation may take several minutes and can fail when VRAM is insufficient. Only an explicitly configured **local** HTTP endpoint is accepted. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) and [Issue #1](https://github.com/liamupchurch-hue/CampaignForge/issues/1).

**Standalone Windows packages** remain unpublished pending third-party binary licensing review, security checks and a clean Windows test; unsigned file warnings may occur.

---

## Original v1.0.0 public beta background

> **EXPERIMENTAL SOFTWARE — BACK UP YOUR FILES.** Campaign Forge is a Windows-first Python desktop prototype for writing and organizing tabletop role-playing campaigns, characters, maps, encounters and books. The `1.0.0` label identifies the first public community-testing package, **not a stable or security-audited commercial product**. Crashes, incorrect AI outputs, data loss and broken exports are possible.
>
> **API charges and private data:** AI is optional. If you choose an external paid API, charges go to your own provider account. An OpenAI API account is separate from ChatGPT subscriptions. Cloud prompts may leave your device. Model downloads, internet bandwidth, and GPU use may have associated costs. [Read the API and data notice](API_AND_DATA_NOTICE.md), [beta risk notice](BETA_DISCLAIMER.md), and [privacy notes](PRIVACY.md).

## Start using Campaign Forge on Windows

1. Install Python **3.11 or newer** with the Windows launcher (`py`) from [python.org](https://www.python.org/downloads/windows/).
2. Download the source ZIP from GitHub (**Code → Download ZIP**) and extract it to a folder you control, **outside** `Program Files`.
3. In the extracted `CampaignForge` folder, double-click **`start_windows.bat`**. Review the first-run notice. The startup script creates a local `.venv` and installs Python dependencies from `requirements.txt` using `pip` (internet required the first time).
4. Open or create a campaign, and save it to a `.campaign.json` file. Back up campaign projects and Archives separately. If you used an older Campaign Forge version, **keep the old folder and test with a copy of your saved campaign first**.

**This ZIP is Python source, not an `.exe` installer or digitally signed Windows program.** [Windows build instructions](BUILDING.md) are for maintainers and testers who understand executable dependencies. Windows SmartScreen or antivirus may warn about unfamiliar scripts; never bypass security warnings without reviewing the source.

## What is free and optional?

- No purchase or subscription is required for Campaign Forge's main editor, PDF reading, book preview or PDF export.
- **Neither AI models nor Ollama, ComfyUI, API credentials, PyTorch or GPU drivers are bundled in this ZIP.** Local Ollama and ComfyUI can be installed separately at the user's choice.
- Cloud AI is **opt-in** and may incur usage charges through a provider. Campaign Forge cannot set or guarantee your external provider spending limits.
- Optional image-model setup links to ComfyUI and SDXL model terms and supports a **user-approved** download. The separate model's license and use restrictions remain with its publisher. No model is silently installed.

## Help improve the beta

Use GitHub [Issues](https://github.com/liamupchurch-hue/CampaignForge/issues) to report bugs and suggest features. The issue forms ask for reproducible steps and scrubbed screenshots. **Never publish API keys, logs with private paths, unpublished manuscripts, or personal data.** Read [CONTRIBUTING.md](CONTRIBUTING.md) and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) first.

## License and third-party components

Campaign Forge's original code is **source-available for personal evaluation**, **not an open-source grant for commercial reuse or redistribution**. See [LICENSE](LICENSE). Third-party Python packages install separately from PyPI under their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Binary packages may require additional license notices. No claim of a comprehensive security or legal audit is made.

## What changed for 1.0.0

- The previous v0.7.2 PDF pipeline is retained: `pypdf` reads text and `pypdfium2` renders preview pages, with no PyMuPDF requirement.
- New public-release version identifiers, clearer first-run and optional-model notices, GitHub feedback forms and publication documentation.
- No AI model is bundled or required for normal PDF operations. The app has been tested on Windows opening and previewing an existing campaign; it is still a public beta.

## What was improved in v0.7.1

### First priority: Character-creation buttons and import review

The controls to **New character**, import sheets, and **Save character changes** have been moved above the flexible character editor. They stay accessible without scrolling below the screen. The Combat statistics area itself has a scrollbar. Switch on **Combat character** to edit stats; narrative-only NPCs have no stat block in the book. Remember: **Save character changes** updates the record in memory. **Save (Ctrl+S)** saves the whole campaign file.

**Read PDF / image character sheet:** A replacement review window now lists each recognized label and value, lets you edit/check the selected value, and keeps **Apply selected fields** visible. TXT and text PDFs can extract clearly labeled numeric statistics offline. JPEG, PNG and scanned PDFs require an installed **vision-capable** local Ollama model and explicit approval, with imperfect recognition possible. No values are invented when unreadable. Testing against a real Windows Ollama server is still required.

### Archives search and Oracle image descriptions

The Archives now searches **filenames** as well as indexed contents, including partial names of PNG/JPEG maps. In Local Oracle conversational mode, ask e.g. **"Describe the image called Harbor Gate in The Archives"** to route a named archived image to the local vision-capable model. Unselected images aren't automatically sent. Text queries still use source excerpts. Cloud image sharing is not included.

### Oracle project changes, behind explicit approval

The Oracle now has **Plan project edits…** and **Undo project edits** buttons under Creative Consultation, using Local Oracle. Write the request, such as "move the Council Meeting after Captain Rowan's investigation", then click Plan project edits. The Oracle may propose only a restricted, validated set of actions: moving existing entries, reordering complete sections, editing campaign fields, editing a story entry, or creating a story entry. A review dialog displays all proposed changes. **Nothing is applied until you approve; there is no execution of shell commands or modification of application files.** If the model cannot produce a safe plan, nothing changes. This is not yet a general autonomous agent or a guaranteed accurate story editor.

Under **Bind the Tome**, the **Plan whole-book changes with Oracle** button prepares a suitable request. Review all proposed chronology and classification carefully. **Check outline** now warns about possible duplicated descriptions; it does not silently delete or rewrite them. Newly generated outlines separate player-visible public locations/lore from DM-only secrets. Previous manual outlines remain unchanged until you explicitly request a new layout.

The **Preview entire book** action is accessible in both the header and the outline controls, and uses a temporary PDF (not a permanent Download).

### Cartography: rotation, grid footprints, custom image props

Choose a prop; click on the map to select it. **Prop size** sets the footprint (1x1, 1x2, 2x2, etc.) for new props; **Resize selected** changes the selected item's footprint; **Rotate 90°** rotates it. Props snap to grid locations as they're dragged. **Import PNG prop…** accepts a user image (minimum 32x32 pixels), shows a confirmation with resolution and selected footprint, and stores a local Archive copy before placing it. Existing map backgrounds and PNG exports continue to work. Export includes external prop art as long as its Archive files are available. For portable projects, back up both project JSON and Archives.

### Optional image-model download: ComfyUI + SDXL Base

Open **Cartography → AI image model setup** (also offered under **The Oracle → Creative Consultation → Local Oracle**) for guided setup. The window opens the official ComfyUI installer site and license page, and can **download the official SDXL Base 1.0 checkpoint (~6.94 GB)** into the *ComfyUI/models/checkpoints* folder that you choose. It supports partial downloads, shows progress and verifies SHA-256 before completing. Check model license and available disk space and bandwidth first. ComfyUI is separate software; v1.1.0-beta.1 adds a local Art Studio Generate button in Cartography, but still requires ComfyUI running independently. None of the multi-gigabyte model files are bundled. This installer was not live-tested against the full 6.94 GB download on Windows.

## Known limitations that remain

- Hero Lab `.por` portfolio import and complete system-validated Pathfinder/D&D stat blocks are future work.
- AI planning is restricted to supported project changes and may produce poor scene chronology; always review before applying.
- Archived image understanding and scanned character extraction require a compatible image-capable Ollama model and may misread text or map symbols.
- No one-click error-diagnostic ZIP yet; we intentionally deferred that idea.
- Full images from manuscript DOCX files are not always preserved in a published campaign PDF. Keep the original source and Archives backup.
- Local in-app SDXL image generation is now included as an experimental interface to external ComfyUI (not bundled); it still needs a live Windows user test.

## Previous v0.7.0 features (still available)

### Modern creator-studio interface

A new original dark interface with teal and brass accents, crisp navigation icons, a compact banner, and the existing full-page scrollbar. No third-party artwork or font files are shipped with the app.

### Roster & Bestiary — structured combat fields

Open **Roster** → **Characters & Creatures**, select or create a character, check **Combat character**, and open **Combat statistics**. AC, HP, Level or Challenge, Speed, saving throws, attributes, attacks and damage have individual fill-in boxes. Relevant fields adapt to D&D or Pathfinder; legacy/freeform and additional fields remain in the lower panel. Unknown stats should remain blank; all numbers require DM verification.

**Read PDF / image character sheet:** Choose a selectable-text PDF or TXT file for local literal field extraction. For a scanned PDF or JPEG/PNG/WebP image, you may opt in to local vision using an installed **vision-capable** Ollama model (e.g., Gemma 3 4B or 12B). This works through `127.0.0.1` and does not upload the sheet to a cloud provider. The model may misread text: review and edit the proposed fields and explicitly approve each import. Only the *first PDF page* is used in the current image analysis path, and a text PDF reads at most four pages. File limit: 24 MB. This is not a general-purpose OCR engine; no numbers are invented when no readable information exists.

To connect a local model, open **The Oracle → Creative Consultation → Local Oracle** and follow the Ollama instructions. Models and Ollama themselves are not included in the Campaign Forge ZIP.

### Bind the Tome — in-app PDF preview

Open **Bind the Tome** and create or review the Book Architect outline.

- **Preview book** opens an internal, paginated proof with previous/next and zoom. It creates a temporary PDF and removes it when you close the preview—nothing is saved in Downloads.
- **Preview selected section / entry** previews only your selected outline subtree.
- **Suggest original manuscript order** looks for exact scene headings in a text-indexed manuscript stored under **The Archives**. It shows the proposed order and moves only recognized scenes after your approval; unmatched scenes are not removed.
- **Ask Local Oracle for scene order** uses your selected local model to propose a scene sequence based on a source manuscript. It must return the exact set of existing scene IDs. You review the result before anything changes. The AI can still get chronology wrong. This is an optional enhancement, not a guaranteed automatic story organizer.

Save the campaign JSON separately from PDF publishing. The editable outline remains the source of truth for the final exported PDF.

### Cartography — layered map foundation

Select or create a map under **Cartography**.

- **Import map background** selects PNG/JPG/WebP and copies it to your local **Archives**, then links it to the current map.
- **Paint** terrain on the map. Floor tiles are transparent over an imported background; non-floor tiles overwrite their cells.
- **Props:** Choose Crate, Barrel, Tree, Stairs, Table, Doorway or Marker. Click **Place / drag props**, click to add a prop, drag it to move it, and right-click to remove one. These are original vector symbols (no copied commercial sprite library).
- **Export PNG** renders the map at 64 pixels per square (up to 3840px on a 60-square dimension). It includes background, terrain, props and grid.
- Existing maps remain compatible. D&D Beyond uploading is manual.

**Important:** A campaign JSON stores the link to the background image, not the image bytes. To move your project to another computer, also use **The Archives → Export library backup** and restore it there. Deleting the archived background can break the link. A future release may add fully portable project bundles.

## What stays from earlier versions

Source-first Local Oracle consultations and conversation history, PDF/DOCX manuscript import with passage diagnostics, local and optional paid AI, The Archives and its ZIP backup, Encounter Builder links to roster characters, Book Architect templates, manual PDF exports, Undo, and Save/Save As.

## Scope and safety notes

- The application **does not** automatically browse D&D or Pathfinder rules sites; rules source links open in your browser.
- AI-assisted character stats, story structure and scanned-sheet extraction must be reviewed by the DM. There is no balance/rules validation engine.
- In-app AI image **generation**, automated Hero Lab `.por` import, polished asset packs, and commercial-quality battle-map tools are still planned and are **not** bundled in v0.7.0.
- A standalone `.exe` installer has not been produced. The included `build_windows.bat` can package the application on Windows, but it requires additional build tools and testing.
- Keep copyrighted rulebooks in your private Archives; do not reproduce licensed content in published books without permission.
- For problems, use **F1 Help** and the existing Oracle import analysis report; the future one-click diagnostic bundle is intentionally deferred.

## Files

`app.py`: Windows GUI. `campaign_data.py`: editable project storage. `forge_ui_mixins.py`: Archives, Roster and Book Architect screens. `character_sheets.py`: local reviewed extraction. `forge_preview.py`: PDF proof window. `source_order.py`: heading and AI-order validation. `map_tools.py`: original layered map renderer. `oracle_providers.py`: Ollama/OpenAI integration. `pdf_book.py`: PDF publishing.

For development regression tests run `python -m pytest -q tests` (pytest is only required for developers). The released build was tested with Tkinter under a Linux virtual display, not on your physical Windows computer; Ollama vision and cloud AI require live testing on a configured device.

See `CHANGELOG.md` for the version history.
