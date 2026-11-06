# Getting Started with Campaign Forge

This guide covers the **public v1.0.0 source beta**. The experimental Art Studio versions use a separate test package and may have additional controls.

## What you need

- A Windows PC.
- **Python 3.11 or newer**, installed from [python.org](https://www.python.org/downloads/windows/), including the Windows `py` launcher.
- An internet connection for the **first launch**, when Python dependencies are installed.
- A folder where you can keep your Campaign Forge application and saved projects.

You do **not** need an AI model, an API key, a paid account, or ComfyUI to write campaigns or export PDFs.

## Installation

1. Open the [Campaign Forge repository](https://github.com/liamupchurch-hue/CampaignForge).
2. Select **Code → Download ZIP** to get the public source version.
3. Extract the ZIP to a folder you control, **outside `Program Files`**.
4. Open the folder containing `app.py` and `start_windows.bat`.
5. Double-click **`start_windows.bat`**.
6. Read the first-run beta notice. The script creates a local Python environment (`.venv`) and installs the packages listed in `requirements.txt`.

The public ZIP is **source code**, not a signed Windows installer or a standalone `.exe`. If Windows blocks the script, do not disable or bypass security protection just to proceed. Review the source and use a trusted setup.

## Your first campaign

1. Create a new campaign, or open a campaign you already saved.
2. Add worldbuilding notes, scenes, people, places, and other campaign details.
3. Use **The Archives** for source material and images.
4. Explore **Roster & Bestiary**, **Cartography**, and **Bind the Tome** as needed.
5. Save the campaign to a `.campaign.json` file.
6. Preview and export a PDF when you're ready to assemble a book.

**Important:** Some buttons save edits to the application's current project, while **Save / Ctrl+S** writes the campaign file to disk. Save regularly.

## Backups and updating

A `.campaign.json` file does **not necessarily include** all imported images or map backgrounds. Use **The Archives → Export library backup** to preserve those assets as well.

For each update:

1. Keep the old working application folder until the new version is tested.
2. Back up the campaign file **and** the Archives.
3. Extract the new source version into a **separate folder**.
4. Open a **copy** of an existing campaign to confirm it still works.
5. Check images, linked assets, book preview, and PDF export before retiring the old version.

Optional ComfyUI model files are installed separately from Campaign Forge. Updating the Campaign Forge source folder **should not require reinstalling** the same SDXL checkpoint. If a development build cannot find it, use the model status/model folder controls rather than downloading a duplicate.

## Building a local executable (advanced)

Developers and testers can follow [BUILDING.md](https://github.com/liamupchurch-hue/CampaignForge/blob/main/BUILDING.md) to run `build_windows.bat`. This creates a PyInstaller **one-folder** build. Keep `CampaignForge.exe` together with its accompanying files, including `_internal`; moving the EXE alone can prevent it from starting.

This executable is a local test build, **not an audited or signed public installer**.

## Need help?

- [AI and Image Generation](AI-and-Image-Generation.md) for optional AI setup.
- [Known Issues](https://github.com/liamupchurch-hue/CampaignForge/blob/main/KNOWN_ISSUES.md) for current limitations.
- [GitHub Issues](https://github.com/liamupchurch-hue/CampaignForge/issues) for bugs and feature requests.

When reporting a problem, describe what you clicked, what happened, what you expected, and which Campaign Forge version you used. **Do not post private campaign manuscripts, API keys, personal paths, or sensitive logs.**
