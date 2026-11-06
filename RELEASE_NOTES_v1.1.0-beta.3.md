# Campaign Forge v1.1.0-beta.3 — Multi-Model Art Studio (source test build)

## Included
- Existing CF campaign editor, Cartography image-generation window, positive/negative prompts, preview, save-as-PNG and The Archives support.
- Model discovery from the running local ComfyUI instance: SDXL/SD checkpoint, Z-Image Turbo, FLUX.1 Schnell/Dev.
- Built-in, architecture-specific workflow graph construction using only recognized ComfyUI core nodes; checks presence of companion text encoders and VAE without downloading them.
- Family-specific Low / Medium / High presets, manual size and steps, seed input. Negative prompt and CFG are **ignored** for Z-Image and FLUX; their sampling uses compatible fixed defaults.
- SDXL install status checker remains part of the separate SDXL Base download screen; it does not erase existing installed model files.

## Not included
- Model weights, ComfyUI, Ollama, PyTorch GPU drivers, paid APIs or cloud services.
- An audited/signed Windows installer or precompiled Windows .exe.
- FLUX.2, Z-Image Base, quantization-specific custom extensions, custom nodes, remote Comfy servers or automatic model downloading.

## Test status
- 139 Python tests and 7 subtests passed locally (X virtual display); Z-Image graph/UI integration and API submissions simulated.
- User successfully generated with SDXL on a previous beta using ComfyUI Desktop; **no live GPU generation verified yet** for Z-Image Turbo / FLUX or this new Windows source build.

## Setup and reporting
1. Unzip into a NEW folder without overwriting existing Campaign Forge files. Keep backups.
2. Start your own ComfyUI instance and confirm models under its `models` directories.
3. Run start_windows.bat, Cartography > Generate Image (ComfyUI) > Find / Connect.
4. Choose a listed model; check status for missing encoder/VAE. Generate and inspect results.
5. If the render fails, share the sanitized ComfyUI queue error (no private campaigns or paths).

Stay on this development build until testing is completed. No model files or service keys are bundled.
