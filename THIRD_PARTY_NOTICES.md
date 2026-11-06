# Third-party components and external downloads

Campaign Forge uses Python packages in `requirements.txt`; the Windows starter may download them automatically on first launch. Each package has its own terms and license. This **source ZIP does not include third-party package binaries**; `pip` installs dependencies separately on the user's machine. A compiled Windows binary would require a resolved dependency and bundled-license audit, including PDFium dependency notices. The maintainer has not independently certified every transitive dependency, so check actual installed distributions before redistributing a binary.

| Component | How used | Important note |
|---|---|---|
| pypdf | Text extraction from PDFs | BSD-3-Clause; <https://github.com/py-pdf/pypdf> |
| pypdfium2 + PDFium | In-app PDF rendering and scanned-page character imports | pypdfium2 is Apache-2.0 / BSD-3-Clause; PDFium uses a BSD-style license plus licenses for bundled dependencies. Keep upstream license notices with any binary redistribution. <https://pypi.org/project/pypdfium2/> |
| ReportLab | PDF generation | Verify current package license and retain notices as applicable. |
| Pillow, python-docx | Local document and image processing | Keep corresponding distribution notices; review installed versions. |
| OpenAI Python client / API | Optional cloud consultation | Separate API billing, provider terms, and data transfer may apply. |
| Ollama | Optional local text/vision models | Not bundled; user chooses installed models. Review individual model licenses. |
| ComfyUI | Optional external image-generation workflow | Not bundled; separate software installation and updates. Review project and model licenses. |
| SDXL Base 1.0 | Optional model download | Not bundled; review model card and CreativeML Open RAIL++-M terms before use. |

This repository does not bundle PyTorch, GPU drivers, Hugging Face model weights, Ollama models, or ComfyUI. Installer links and downloaded content are controlled by their respective publishers, not Campaign Forge.

**No AI model redistribution:** Ollama and ComfyUI are optional user-installed applications. SDXL weights are not included. The optional in-app SDXL downloader requires the user to review its model terms before explicitly downloading. The code may not bypass authentication or acceptance requirements set by model publishers.
