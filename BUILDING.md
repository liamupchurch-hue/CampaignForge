# Building Campaign Forge on Windows (maintainers/testers)

This repository is distributed as Python **source** and not a signed installer.
For ordinary testing, run `start_windows.bat` instead of building an executable.

To produce a local, **unpublished** Windows executable:

1. Install Python 3.11+ with the Windows `py` launcher.
2. Run `start_windows.bat` to create the project's virtual environment.
3. Close the app and run `build_windows.bat` to install PyInstaller and build a `--onedir` executable.
4. The resulting local executable is in `dist\CampaignForge\CampaignForge.exe`.

**Do not redistribute the built executable yet:** packaging dependencies in a binary triggers redistribution obligations. Before shipping an `.exe` or installer, audit and include all notices for PyInstaller, Python, pypdfium2/PDFium (including bundled native components), Pillow, ReportLab and the complete resolved dependency graph. Sign binaries and perform Windows Defender/SmartScreen and real-install testing before a commercial release.

No model weights, GPU drivers, ComfyUI, or Ollama are needed to build the basic application. They are not included in the repository or generated executable unless explicitly and independently added.
