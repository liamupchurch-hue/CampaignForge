# Known limitations — v1.0.0 public beta

- Project edits proposed by local AI require user approval; generated chronology or labels may still be wrong.
- The Roster and scanned PDF/JPEG/PNG interpretation depend on templates and compatible local models; sheet extraction may be inaccurate.
- Some imported manuscript images are not embedded in the published PDF.
- Hero Lab Classic `.por` import and comprehensive Pathfinder/D&D mechanics validation are not implemented.
- Image-model downloads are optional; in-app image generation is not yet wired to ComfyUI's execution server.
- Imported maps and custom assets rely on the local Archives; moving project JSON alone does not necessarily preserve linked files.
- Full automated manuscript chronology and duplicate resolution remain incomplete.
- The ZIP is a Python-based prototype and may install packages from the internet on first run; it is not a signed Windows executable.
- Live Windows/GPU configurations, network failures, and large-model downloads have not been exhaustively tested.

Please search existing Issues before reporting duplicates. The maintainer may not be able to respond immediately.
