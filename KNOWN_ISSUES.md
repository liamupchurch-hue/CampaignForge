# Known limitations — v1.1.0-beta.3 source test build

- Project edits proposed by local AI require user approval; generated chronology or labels may still be wrong.
- The Roster and scanned PDF/JPEG/PNG interpretation depend on templates and compatible local models; sheet extraction may be inaccurate.
- Some imported manuscript images are not embedded in the published PDF.
- Hero Lab Classic `.por` import and comprehensive Pathfinder/D&D mechanics validation are not implemented.
- The new **Generate Image (ComfyUI)** interface and API adapter have passed simulated local server tests, but have **not yet been tested against an actual running Comfy Desktop instance on Windows**. Port/model/version differences and GPU memory issues may require adjustments.
- Image generation is purely local with SDXL Base and compatible core nodes. ComfyUI and model installation remain separate and optional; no automatic instance management or custom workflow graph editing is included.
- Stop waiting pauses Campaign Forge's status monitoring; it does not interrupt another process's queued ComfyUI GPU job.
- Imported maps and custom assets rely on the local Archives; moving project JSON alone does not necessarily preserve linked files.
- Full automated manuscript chronology and duplicate resolution remain incomplete.
- The ZIP is a Python-based prototype and may install packages from the internet on first run; it is not a signed Windows executable.
- Live Windows/GPU configurations, network failures, and large-model downloads have not been exhaustively tested.

Please search existing Issues before reporting duplicates. The maintainer may not be able to respond immediately.

- Low/Medium/High only change image size and sampling steps; perceived artistic quality may require different compatible checkpoints, a refiner or improved prompt/model settings. No new models bundled.

## Experimental local ComfyUI model routing (beta.3)

- Z-Image Turbo and FLUX.1 require separately installed diffusion weights, text encoders and VAE in the folders ComfyUI indexes. If CF reports missing companion files, check the running ComfyUI installation; do not copy models into the Campaign Forge installation folder.
- Only **Z-Image Turbo** and **FLUX.1 Schnell/Dev** are recognized among newer diffusion architectures. Other AI architectures or unusual quantizations can require separate graphs/custom nodes and remain unsupported.
- Z-Image Turbo / FLUX ignore the negative prompt and CFG fields; SDXL and standard Stable Diffusion honor them. Checkpoints with ambiguous filenames may be classified as standard SD and require verification.
- Live Z-Image and FLUX GPU runs have not been verified by the owner; some models may exhaust available VRAM. The v1.1.0-beta.3 source build is not a signed Windows executable.
