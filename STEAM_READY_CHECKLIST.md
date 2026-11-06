# Steam Ready Checklist — Campaign Forge

**Project:** Campaign Forge (Windows-first tabletop campaign creator)  
**Baseline:** Public GitHub community beta v1.0.0 (source distribution)  
**Established:** 2026-11-06  
**Owner decision:** Spend **$0** on Campaign Forge during development. No Steam Direct fee, paid API, paid model, commercial PDF library, signing certificate, or other paid service without the owner's later approval. AI must remain optional for core editing/PDF functions.

This is the **living master checklist** for readiness to distribute Campaign Forge on Steam. Update statuses only after confirming evidence, tests, or completed deliverables. A version named 1.0.0 is **not** evidence of Steam readiness.

**Legend:** [x] Verified/implemented (scope noted); [ ] Pending; [~] Partially working, needs more testing.  
**Priority:** P0 = required before we call it Steam ready; P1 = major polish / scope decision; P2 = later/optional.  
**Policy:** We will not add large new features merely to fill the checklist. We will focus on a coherent, safe, usable first Steam version.

## A. Foundation and core application (P0)

- [x] **GitHub source beta published.** Campaign Forge v1.0.0 is in [the repository](https://github.com/liamupchurch-hue/CampaignForge); source-only, not a compiled Windows installer.
- [x] **Official logo approved.** Gold/ember CF forge crest chosen for project branding. *Only the identity is complete; required Steam-sized artwork is not.*
- [~] **Official Windows executable icon.** Multi-resolution CF `.ico` generated from the approved crest, included in the v1.1.0-beta.1 feature-branch `assets` and PyInstaller build script. Source/packaging tests pass; actual Windows rebuilt icon and signing/reputation tests remain open.
- [x] **PDF preview no longer uses PyMuPDF.** Source uses pypdf/pypdfium2, and owner tested opening and previewing an existing campaign on Windows. The full Windows distribution dependency audit is still pending.
- [x] **Core features work without AI in principle.** Campaign editing, PDF reading/preview/export have no required local models or paid API. Keep this contract.
- [~] **End-to-end primary workflow reliable:** new campaign → save → close → reopen → edit → build book → export PDF. Some owner testing and automated tests passed, but perform dedicated release acceptance testing.
- [ ] **No data loss/regression bugs.** Verify save/Save As/Undo, malformed files, autosave or recovery strategy, crashes during save, and no accidental original manuscript overwrites.
- [ ] **Portable project + Archives backup.** Imported maps/images/linked files must be included or accurately identified when moving projects; restore must work after a clean reinstall.
- [ ] **Backward compatibility.** Older .campaign.json projects open in the current version; migration is predictable and backups are maintained.
- [ ] **Errors must be understandable.** Invalid input, missing files, unavailable Ollama/ComfyUI, failed network or downloads should not hang or crash the application.

## B. Finish and polish the features already started (P1; promote to P0 if advertised at launch)

- [~] **Roster & Bestiary usability.** Controls and scrolling fixed in v0.7.1; validate save/reopen, combat vs narrative mode, and Encounter Builder reuse on real Windows sessions.
- [~] **Character-sheet import.** Text PDFs/TXT import works in tests; scanned image/PDF interpretation needs real local-vision model testing and explicit user review of extracted stats.
- [~] **Book Architect.** Improve chronology, chapter grouping, repeated material warnings, DM vs player-facing organization, whole-book preview, and exports. Avoid editing source campaign facts without approval.
- [~] **PDF publishing fidelity.** Verify headings, tables, maps, images, page breaks and fonts; some imported manuscript images are not yet embedded.
- [~] **Cartography.** Verify map backgrounds, custom PNG props, snapping, rotation, resizing, save/reload, and exported maps; ensure linked assets travel with projects.
- [~] **Oracle project edits.** Existing preview/approve/Undo and source-grounding are in place; validate that the model cannot silently rewrite unrelated campaign fields or invent source facts.
- [ ] **In-app Help / onboarding.** Clear first-run guided tour; plain-English feature instructions; error-help links; explain optional local vs cloud AI and pricing before any API operation.
- [ ] **Accessible UX.** Keyboard navigation, readable font scaling/contrast, no clipped controls at standard Windows resolutions, tooltip clarity and screen-reader-friendly labeling where feasible.
- [ ] **Choose a v1 Steam feature set.** Don't advertise unimplemented rules validation, Hero Lab Classic .por, or full AI-powered image generation.

## C. Optional AI integrations (P1 or P2; NOT required for basic app)

- [x] **No model weights, ComfyUI, Ollama, GPU drivers or API keys bundled in the source beta.**
- [ ] **Local model discovery and capabilities.** Detect installed Ollama models and supported text/vision skills; don't claim every model supports every function.
- [~] **Built-in ComfyUI Art Studio — SDXL LIVE PASSED; multi-model beta.3 READY FOR TESTING.** Owner generated an image successfully through the ComfyUI-connected Art Studio. The [draft PR #2](https://github.com/liamupchurch-hue/CampaignForge/pull/2) now includes v1.1.0-beta.3 source: family-specific Low/Medium/High presets, installed model status, and experimental Z-Image Turbo / FLUX.1 Schnell/Dev workflow routing. Missing encoder/VAE components are reported before generation. **139 local tests + 7 subtests passed**, including simulated GUI and API tests. New model families still require live Windows GPU verification; signed/legally audited Windows redistribution remains pending. [Issue #1](https://github.com/liamupchurch-hue/CampaignForge/issues/1). No models or credentials bundled.
- [~] **ComfyUI Desktop model folder experience.** Source-level finder and explicit Settings → Storage → Shared Models instructions are in the development branch; tests pass, Windows dialog verification still pending. Owner separately confirmed Comfy Desktop generated a 1024×1024 fantasy map with SDXL Base 1.0; CF's new in-app integration is awaiting live Windows verification.
- [ ] **Robust AI permissions.** Never send documents, images or personal data to cloud providers without deliberate consent; no covert background calls; preview AI edits; allow disable-all-AI mode.
- [ ] **API billing explanations.** Bring-your-own key, no auto-billing by Campaign Forge, readable usage warnings, safe key storage and redaction in diagnostics; never promise to control third-party charges.
- [ ] **External model/API terms.** Users independently install and license optional models. Campaign Forge needs a documented integration/third-party terms review for the interfaces and any downloader it implements. Do not assume unbundled implies *zero* legal or security obligations.
- [ ] **Steam AI content disclosure.** Evaluate how the finished app's AI features and any AI-generated store/shipped art should be described in Steam's Content Survey; document appropriate safeguards.

## D. Windows installation and release engineering (P0)

- [ ] **Produce a self-contained Windows build.** Customers should not need to install Python/pip or run a .bat script. Current build_windows.bat is for an unpublished PyInstaller onedir experiment, not a tested commercial installer.
- [~] **First desktop and second-computer laptop smoke tests PASSED for 4 core functions (owner-reported, 2026-11-06).** The properly transferred onedir `CampaignForge.exe` launches on both machines; create/save/reopen, existing campaign book preview, and PDF export pass on both. **Still pending:** specifically testing offline, confirming the laptop has no separate Python installation, a truly clean Windows environment, and bundled notices. See [standalone test procedure](docs/STANDALONE_WINDOWS_TEST.md).
- [~] **Second-computer one-folder portability PASS; clean installation NOT VERIFIED.** Laptop now launches the correctly transferred executable and repeats the desktop's core workflow. Initial missing `python313.dll` error was consistent with moving the exe without its supporting `_internal` directory. Still test on a known Python-free Windows installation, verify offline operation and data/Archive locations.
- [ ] **App startup, close, uninstall and update.** No unnecessary administrator access; proper icon and display name; user data stays outside the app installation directory and survives upgrades/uninstall as expected.
- [ ] **Reproducible build pipeline.** Pin and hash dependencies, automate a clean build in a documented environment, generate release checksums, and archive build inputs.
- [ ] **Windows automated CI.** Run unit/regression tests and at least one executable smoke test; continue manual GUI testing on real Windows hardware.
- [ ] **Performance and memory checks.** Load large campaigns, render long PDFs, import documents, and test 16 GB/32 GB RAM configurations and CPU-only operation.
- [ ] **Crash diagnostics.** Safe local logging with paths/tokens/content redacted; an opt-in issue report export; no surprise telemetry or uploads.
- [ ] **Security assessment.** Dependency vulnerability scan, safe archive extraction/path handling, project-file input validation, network opt-in, key storage, external process boundaries, and user-controlled AI actions.
- [ ] **Binary legal/notice audit.** Include direct + transitive licenses/attributions for Python, PDFium/pypdfium2, pypdf, ReportLab, Pillow, python-docx, packaging tool, shipped fonts/icons and native DLLs. Test actual distributed binary, not only source requirements.
- [~] **Smart App Control and signing — correctly packaged exe PASSED laptop trial (2026-11-06).** Smart App Control previously blocked downloaded source `build_windows.bat`; the properly packaged executable now launches and passes core tests on the laptop (owner-reported). This **does not** prove it will work on every Windows installation or establish publisher trust. Continue assessing signed distribution for general release. No need to buy a certificate during development.
- [ ] **Windows release test plan.** Installation, upgrade, save migration, offline use, firewall, antivirus, non-admin accounts, failed download and backup recovery.

## E. Product, rights and support (P0)

- [ ] **Rights/license review.** Confirm copyright and distribution rights to original source, AI-assisted artwork (including logo), fonts, UI assets, bundled examples, game-rule text and any third-party content before commercial release.
- [ ] **Choose commercial redistribution terms.** Current LICENSE is limited personal-evaluation source access. Decide commercial end-user license, contributions and future source availability before Steam.
- [ ] **Privacy and terms review.** Clear no-telemetry claim only if verified, third-party API data transfer warning, crash logs, account/key handling, AI errors, data loss and fair limitation-of-liability language; professional legal review if appropriate.
- [ ] **Safe sample campaign.** Ship only invented or licensed examples; do not distribute private Midnight at Misrath manuscripts or unlicensed copyrighted rulebooks.
- [ ] **Support system.** GitHub issue templates, release notes, known issues, support/contact route and privacy-safe log collection.
- [ ] **Regular QA.** Weekly review of public GitHub feedback; reproduce reported bugs, regression-test fixes, and publish safe routine updates where tool access permits.
- [ ] **Version strategy.** Separate source-beta versioning from Steam build numbers, maintain migration notes and changelog, use clear rollback/recovery plans.

## F. Steam store and publishing (P0 at launch; **defer all costs**)

- [ ] **Select Steam category/positioning for campaign-authoring software.** Confirm appropriate Steamworks product listing and accurate descriptions.
- [ ] **Create Steam-sized branding.** The crest exists, but we still need title legibility on store capsules, library artwork, a clear full-name logotype and at least five genuine screenshots of working UI.
- [ ] **Record real walkthrough/demo media.** Show creating a campaign, roster, map, Oracle as optional, and finished PDF. No simulated or unimplemented features presented as real.
- [ ] **Accurate system requirements.** Minimum Windows version, storage, RAM, CPU, display requirements; separate optional GPU/VRAM requirements for local AI.
- [ ] **Choose price and distribution model.** Free/paid choice and future support model decided before onboarding; no fee due during development.
- [ ] **Steamworks onboarding (later, owner action).** Complete identity, tax and bank information privately, agree to Valve's terms, and pay the Steam Direct fee only with explicit approval. Official current Steam Direct fee is **US$100 per app**, recoupable after **US$1,000 adjusted gross revenue** (subject to Steam terms).
- [ ] **Steam timing.** For new partners/products, plan for the currently documented 30-day post-fee waiting period and at least 2 weeks with a public Coming Soon page; confirm rules when actually scheduling launch.
- [ ] **Steam store review.** Submit accurate store content and a near-final build, plan for review and corrections before release.
- [ ] **SteamPipe release setup.** Configure app/depots, launch options, supported OS, beta branch, install tests, updates and rollback.
- [ ] **Pre-Steam GitHub release channel.** When the executable passes dependency/license, privacy/security, and clean-Windows packaging checks, publish each tested standalone Windows distribution as a **versioned GitHub Release** asset and keep older releases available. No fork needed; avoid distributing partial onedir files or unreviewed binaries.
- [ ] **Final GO / NO-GO.** Steam installs/launches on clean machines, advertised features work, data stays safe, license/rights/privacy reviews complete, store materials match reality, and owner authorizes paid onboarding and release.

## G. Nice-to-have AFTER launch (P2; not blockers unless we change scope)

- [ ] More elaborate autonomous Book Architect improvements and manuscript chronology.
- [ ] Broader Pathfinder 2e / D&D mechanics validation, character-sheet presets and external format importers.
- [ ] Native ComfyUI generation within Campaign Forge, multiple image workflows and richer props.
- [ ] Optional Steam Cloud synchronization, achievements or Workshop integration **only if they demonstrably help users**.
- [ ] Additional operating systems, collaboration, languages, and more integrated help/tutorial video.

## Suggested order of work

1. **P0 first: Windows distribution feasibility** — build an unpublished exe, inspect bundled dependency licenses, and test without Python installed.
2. **P0: Data durability** — save/load, backup/restore, portable Archives, project version migration.
3. **P1: Editor quality** — Book Architect, Roster, maps, imported images, clear onboarding; decide exact launch feature promises.
4. **P0: Security and repeatable test suite** — reliable clean builds and regression tests.
5. **Later only: Steamworks payment, store assets, review and release** after owner authorizes spending.

## Change log for this checklist

- **2026-11-06:** ComfyUI Art Studio SDXL live generation passed on owner's Windows PC. Development v1.1.0-beta.3 adds experimental FLUX.1 and Z-Image Turbo workflows and model-family quality presets; live tests of these new families remain pending.
- **2026-11-06 (development build):** GitHub feature branch `feature/comfy-art-studio-v1.1.0-beta.1` contains new Art Studio UI, positive/negative prompts, localhost ComfyUI API queue/poll/image retrieval, optional Archives/map integration, and CF icon. 122 tests passed under Xvfb, GitHub Python CI passed. Live owner ComfyUI Windows test is next; main v1.0.0 release is unchanged.
- **2026-11-06:** Received API-format `image_sdxl_simple` JSON from the working owner ComfyUI instance; committed sanitized default workflow and `comfy_bridge.py` under `assets/workflows` and repo root. Integration tests pass locally. Connecting app UI and live output retrieval is still pending.
- **2026-11-06:** ComfyUI Desktop instance confirmed generating a 1024×1024 SDXL Base 1.0 fantasy map; built-in CF workflow/API integration still pending.
- **2026-11-06:** Owner requested built-in ComfyUI workflow presets and seamless local artwork generation, plus versioned standalone builds in GitHub Releases. Documented feature scope in [Issue #1](https://github.com/liamupchurch-hue/CampaignForge/issues/1). Work remains pending; external models/ComfyUI stay optional and unbundled.
- **2026-11-06:** Recorded ComfyUI setup usability issue and published source-level folder guidance/discovery fix; Windows confirmation and ComfyUI workflow integration remain pending.
- **2026-11-06 (laptop retest):** With the correctly packaged executable and supporting files, user confirms launch/save-and-reopen/existing-book preview/PDF export all pass on laptop, matching desktop tests. Prior DLL failure traced to incomplete one-folder transfer. Offline and known Python-free checks remain open.
- **2026-11-06 (laptop photo 2):** Compiled exe now starts far enough to show PyInstaller loader error about `Downloads\\_internal\\python313.dll`; exe is shown at Downloads root. Most likely deployment was incomplete (onedir `_internal` not transferred). Corrective test: retain the entire `dist\\CampaignForge` folder structure. No changes to code until retested.
- **2026-11-06 (photo correction):** Exact dialog is Smart App Control, and Explorer shows `build_windows.bat` selected in downloaded source. Earlier shorthand implying that the compiled exe was blocked was premature; compiled exe remains untested on laptop. Security compatibility remains open. Desktop's 4/5 smoke-test results remain valid.
- **2026-11-06:** Owner reported first standalone exe smoke test: launch, save/reopen, preview and PDF export passed (4 of 5); offline operation not yet tested. One-folder independence and clean-machine tests remain open.
- **2026-11-06:** Created master Steam Ready Checklist after GitHub v1.0.0 source beta release and owner confirmation of Windows PDF preview. Based on README, KNOWN_ISSUES, BUILDING, RELEASE_AUDIT_CHECKLIST and official Steamworks documentation.

## Official references (recheck before launch)

- [Steamworks onboarding](https://partner.steamgames.com/doc/gettingstarted/onboarding)
- [Steam Direct fee](https://partner.steamgames.com/doc/gettingstarted/appfee)
- [Steam release process](https://partner.steamgames.com/doc/store/releasing)
- [Steam review process](https://partner.steamgames.com/doc/store/review_process)
- [SteamPipe delivery](https://partner.steamgames.com/doc/sdk/uploading)
- [Steam store graphical assets](https://partner.steamgames.com/doc/store/assets)
- [Steam content survey / AI disclosure](https://partner.steamgames.com/doc/gettingstarted/contentsurvey)
