# Campaign Forge — First Standalone Windows Build Test

**Status:** Local, unpublished experiment. **Cost:** $0.  
**Baseline:** GitHub source beta v1.0.0. This procedure is for testing, not a public binary release.

## Goal

Produce a **one-folder Windows executable** that can be launched without a separate Python installation. It should preserve normal campaign editing, PDF preview/export, and optional (not required) AI integrations.

## Build on a Windows PC

1. Keep a backup copy of any important `.campaign.json` files and Archives outside the source directory. Do not build against your only copy.
2. Extract the latest source ZIP or Git checkout into a folder you can edit (not under Program Files).
3. Run `start_windows.bat` once to create `.venv` and install dependencies; close the application.
4. Double-click **`build_windows.bat`**. It uses local Python to install PyInstaller and builds a `--onedir --windowed` app. Internet access may be required for this one-time setup.
5. If the build succeeds, look for **`dist\CampaignForge\CampaignForge.exe`**. **Keep the entire `dist\CampaignForge` folder together.** The executable by itself is not portable.
6. Launch `CampaignForge.exe` directly, without `start_windows.bat`. Test on a copy of your campaign.
7. For a stronger independence test, copy the **whole** `dist\CampaignForge` folder to another location or a clean Windows machine/account without Python. Launch the executable directly. Do not assume this works until verified.

## First test results reported by owner — 2026-11-06

- **PASS:** `CampaignForge.exe` launched without starting the Python launcher.
- **PASS:** Created, saved, closed, and reopened a new campaign.
- **PASS:** Opened an existing campaign copy and previewed its book.
- **PASS:** Exported the book to PDF.
- **NOT TESTED:** Core editing while disconnected from the internet.
- **LAPTOP PASS (subsequent test, 2026-11-06):** Transferred correctly packaged executable launches on second Windows machine; owner confirms the same four core tests pass there.
- **NOT YET VERIFIED:** Specifically offline operation; whether the laptop lacks Python; clean-account install; full backup/Archive handling.

These are owner-observed outcomes, not independently reproduced Windows tests. They establish an initial working executable but do not yet establish independent redistribution readiness.

### Next two quick checks

1. **Offline test:** Save and close the app. Temporarily disconnect Wi-Fi/Ethernet, launch the .exe, open a **copy** of a campaign, edit text, save/reopen and preview/export a PDF. Do not invoke cloud APIs. Restore internet afterwards. If the app fails, record the exact step and error (redact any private paths/content).
2. **Relocation test:** Copy the **entire** `dist\\CampaignForge` directory (including `_internal` and all supporting files) to a completely separate folder, e.g. `C:\\CF-Standalone-Test\\CampaignForge`. Launch the copied .exe directly. Create a **new test campaign** and export its PDF. Never copy only the .exe. Keep the original installation until results are confirmed.

**A relocation test does not prove Python independence:** the strongest verification is a fresh Windows account/machine where Python is not installed, ideally with local AI services absent.

**Data locations:** Some Campaign Forge metadata and Archives live under `%LOCALAPPDATA%\\CampaignForge`. Always back up Archives as well as .campaign.json files before reinstalling, upgrading or running stress tests. Moving the executable folder does not necessarily move all user data.

## Core smoke test (check each on the standalone executable)

- [ ] Launch and close cleanly; reopen successfully.
- [ ] Start a new campaign, save a `.campaign.json`, close and reopen it.
- [ ] Open a copy of an existing older campaign and confirm saved content.
- [ ] Import a text PDF or DOCX and verify expected text.
- [ ] Preview the book PDF, navigate pages, and export a PDF.
- [ ] Open Roster & Bestiary, save a character, create an encounter using it, then save and reopen.
- [ ] Open Archives; import/search a file and verify linked maps still appear.
- [ ] Use normal editor functions with Ollama/ComfyUI uninstalled or offline.
- [ ] Verify error messages for unavailable optional Ollama/ComfyUI and cloud API are graceful.
- [ ] Check no API credentials, private campaign samples or user secrets are bundled in the dist folder.
- [ ] Verify system directories/user data locations behave correctly when run from a different folder.
- [ ] Check whether first-run notices/privacy and third-party notices are actually accessible in the executable distribution.

## If it fails

### Smart App Control blocked the source build script (photo-confirmed 2026-11-06)

The laptop screenshot identifies **Smart App Control** ("blocked a file that may be unsafe") and shows **`build_windows.bat` selected** in an extracted GitHub source folder (`CampaignForge-main`). This strongly suggests Windows blocked the downloaded **batch build script**, rather than the compiled `CampaignForge.exe`. Therefore, the first laptop test has **not yet exercised the standalone binary**.

**Test next without invoking a build script:**

1. On the desktop where PyInstaller worked, open `dist\\CampaignForge`. Zip **the entire `CampaignForge` folder**, including its `CampaignForge.exe` and all supporting files.
2. Transfer that ZIP to the laptop using your usual trusted method and extract it to an ordinary test folder.
3. With Smart App Control still On, try running `CampaignForge.exe` **directly**, not `build_windows.bat`, `start_windows.bat` or anything in the downloaded GitHub source tree.
4. If the executable is blocked too, capture its exact warning. This becomes a separate signed binary/reputation compatibility failure. Do not disable Smart App Control or Defender merely to proceed.
5. If it launches, exercise the main editor, save/reopen, and PDF export, then repeat offline (with no AI services).

Microsoft's published Smart App Control guidance explains it can block unrecognized code and files/scripts from the web. For later public distribution, consider properly signing shipped binaries and all executable components with an appropriately trusted publisher certificate. **Do not purchase any certificate during development without owner approval.**

**Updated status:** Windows laptop source-script block confirmed, but **properly transferred compiled executable now launches and repeats core tests successfully (owner report, 2026-11-06)**. Prior DLL error was from missing support files in onedir layout. Binary reputation/signing review is still required for general distribution.

Keep the console window from `build_windows.bat` open and capture the **first error**, not just the last line. Report whether failure happens during the build, at executable startup, or when opening a particular feature. A `--windowed` app may hide runtime tracebacks; a diagnostic console build may be needed later.

For any report, include Windows version, Python version used for the build, exact steps to reproduce, and a scrubbed screenshot/error text. **Do not share API keys, personal paths, or private campaign content.**

## Known limitations for this trial

- A `--onedir` package is not an installer or an MSI. It should be treated as a test output.
- Campaign Forge's first-run legal notice currently lives in `start_windows.bat`; an executable will need an in-app notice and bundled legal documents before public release.
- We have not audited the resulting binary's resolved dependency licenses and native DLLs. **Do not redistribute it yet.**
- Windows Defender and SmartScreen may flag unsigned unfamiliar executables. Do not weaken Windows security settings merely to run a test.
- This first test is **not** SteamPipe integration, code signing, a formal security review, or commercial release.

## Next engineering steps after first successful test

1. Resolve missing runtime assets/imports and any file paths that assume the source directory.
2. Store writable user data separately from program files; verify backups and upgrades.
3. Add official Campaign Forge icon, version metadata and an in-app first-run notice.
4. Make the build reproducible with locked dependencies, tests and bundled license notices.
5. Evaluate an installer/SteamPipe depot only after the onedir build passes a clean-machine test.

Reference: [PyInstaller usage documentation](https://pyinstaller.org/en/stable/usage.html).
