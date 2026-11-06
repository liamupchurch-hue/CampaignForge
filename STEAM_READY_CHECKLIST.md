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
- [ ] **ComfyUI integration decision.** Current setup guidance exists; actual generation through ComfyUI's local execution API is not wired in. Implement and test only if we choose it as a Steam launch feature.
- [ ] **Robust AI permissions.** Never send documents, images or personal data to cloud providers without deliberate consent; no covert background calls; preview AI edits; allow disable-all-AI mode.
- [ ] **API billing explanations.** Bring-your-own key, no auto-billing by Campaign Forge, readable usage warnings, safe key storage and redaction in diagnostics; never promise to control third-party charges.
- [ ] **External model/API terms.** Users independently install and license optional models. Campaign Forge needs a documented integration/third-party terms review for the interfaces and any downloader it implements. Do not assume unbundled implies *zero* legal or security obligations.
- [ ] **Steam AI content disclosure.** Evaluate how the finished app's AI features and any AI-generated store/shipped art should be described in Steam's Content Survey; document appropriate safeguards.

## D. Windows installation and release engineering (P0)

- [ ] **Produce a self-contained Windows build.** Customers should not need to install Python/pip or run a .bat script. Current build_windows.bat is for an unpublished PyInstaller onedir experiment, not a tested commercial installer.
- [ ] **First local build smoke test (next action).** Run the existing `build_windows.bat` on Windows and complete [the standalone test procedure](docs/STANDALONE_WINDOWS_TEST.md). Do not mark complete until the generated exe launches, saves/opens, previews/exports PDFs, and runs separately from the source folder.
- [ ] **Verify clean machine installation.** Test on fresh Windows 10/11 accounts, with no Python, development folders, Ollama or ComfyUI.
- [ ] **App startup, close, uninstall and update.** No unnecessary administrator access; proper icon and display name; user data stays outside the app installation directory and survives upgrades/uninstall as expected.
- [ ] **Reproducible build pipeline.** Pin and hash dependencies, automate a clean build in a documented environment, generate release checksums, and archive build inputs.
- [ ] **Windows automated CI.** Run unit/regression tests and at least one executable smoke test; continue manual GUI testing on real Windows hardware.
- [ ] **Performance and memory checks.** Load large campaigns, render long PDFs, import documents, and test 16 GB/32 GB RAM configurations and CPU-only operation.
- [ ] **Crash diagnostics.** Safe local logging with paths/tokens/content redacted; an opt-in issue report export; no surprise telemetry or uploads.
- [ ] **Security assessment.** Dependency vulnerability scan, safe archive extraction/path handling, project-file input validation, network opt-in, key storage, external process boundaries, and user-controlled AI actions.
- [ ] **Binary legal/notice audit.** Include direct + transitive licenses/attributions for Python, PDFium/pypdfium2, pypdf, ReportLab, Pillow, python-docx, packaging tool, shipped fonts/icons and native DLLs. Test actual distributed binary, not only source requirements.
- [ ] **Evaluate Windows executable reputation/signing.** Signing is not assumed mandatory for Steam, but assess warning dialogs, publisher identity and cost/security tradeoffs; do not purchase a certificate during development without approval.
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

- **2026-11-06:** Created master Steam Ready Checklist after GitHub v1.0.0 source beta release and owner confirmation of Windows PDF preview. Based on README, KNOWN_ISSUES, BUILDING, RELEASE_AUDIT_CHECKLIST and official Steamworks documentation.

## Official references (recheck before launch)

- [Steamworks onboarding](https://partner.steamgames.com/doc/gettingstarted/onboarding)
- [Steam Direct fee](https://partner.steamgames.com/doc/gettingstarted/appfee)
- [Steam release process](https://partner.steamgames.com/doc/store/releasing)
- [Steam review process](https://partner.steamgames.com/doc/store/review_process)
- [SteamPipe delivery](https://partner.steamgames.com/doc/sdk/uploading)
- [Steam store graphical assets](https://partner.steamgames.com/doc/store/assets)
- [Steam content survey / AI disclosure](https://partner.steamgames.com/doc/gettingstarted/contentsurvey)
