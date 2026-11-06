# Campaign Forge v1.1.0-beta.1 — Windows source test build

This beta adds a local ComfyUI AI Art Studio in Cartography: positive and negative prompts, checkpoint and image-size selection, Generate button, preview, PNG export, and opt-in Archives/map insertion. It uses a built-in seven-node SDXL workflow. Models, ComfyUI, and paid cloud tools remain optional and unbundled.

**Not a Windows executable:** run `start_windows.bat` from the extracted source folder or compile your own personal test binary with `build_windows.bat` after dependencies install. Keep the entire `dist/CampaignForge` folder; do not distribute binary packages until notices/security reviews are complete.

**Testing:** local mocked ComfyUI server and GUI flow verified. **No live Windows ComfyUI API smoke test yet**. Visit issue #1 for integration tracking.

**Additional improvement:** new approved CF crest bundled as a Windows icon. Windows executable icon requires rebuilding; source UI uses it on Windows when supported.

**Known limitations:** Generated images can be inaccurate; stop-waiting does not kill GPU jobs; imported assets live in local Archives and need separate backups. Core app remains functional without AI.
