# Campaign Forge v1.1.0-beta.4 — No Silent Model Fallback

**Development test build, not a commercial or signed Windows release.**

## Fix
The ComfyUI Art Studio previously could choose the first available model when the model you had selected went missing. That could silently use SDXL instead of the intended model.

In beta.4:
- No model substitution is allowed. If your selected model is missing on reconnect, the model field is cleared and Generate is disabled.
- With several compatible models installed, select the model explicitly.
- Just before each GPU job, Campaign Forge asks the **running** ComfyUI server to confirm the exact model and any required text encoders/VAE. Changed/missing files stop the request.
- Model filenames are shown in generation confirmation and job status, and the model dropdown is locked while a job is running.
- **SDXL Low/Medium/High quality settings are unchanged.**

## Windows test instructions
1. Extract this ZIP to a **new** folder without overwriting beta.3, and run `start_windows.bat`. Keep your existing ComfyUI Desktop instance running.
2. In **Cartography → Generate Image (ComfyUI)** press **Find / Connect**.
3. If only SDXL is installed, it should be selected automatically. With multiple ready models, choose one explicitly.
4. Generate a normal SDXL test image and confirm its selected checkpoint is shown before submission.
5. If a chosen model is removed/unavailable, generation should stop with a warning, **not** generate a fallback image.
6. Use **Check model status** after adding/removing models. Confirm models aren't silently downloaded and no installed SDXL files are disturbed.

## Verification and limits
- Local Python and virtual-display suite: **153 tests passed and 7 subtests passed** (including fake API responses and graphical missing-model regression).
- No live beta.4 ComfyUI/GPU test has been performed. Z-Image Turbo/FLUX.1 workflows remain experimental.
- Source ZIP only: Python application, `.bat` launcher/builder, README and tests. No precompiled Windows `.exe`, AI weights or API keys.
- Commercial distribution of compiled Windows binaries still requires dependency/license/security review.
