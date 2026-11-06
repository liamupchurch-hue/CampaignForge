# Campaign Forge v1.0.0 — Public Community Beta

**Status:** experimental Windows-first Python source preview; not a signed or compiled Windows installer.

## Included
- Campaign editor, Oracle writing tools and user-approved project-edit plans.
- Local Archives, Roster & Bestiary, Encounter Builder, Cartography and Book Architect.
- PDF reading and preview with free permissively licensed libraries (`pypdf`, `pypdfium2`), and PDF export via ReportLab.
- Optional local AI (Ollama, installed separately); optional cloud API (bring your own key and billing account); optional external ComfyUI image-generation workflow.
- Windows launcher, documentation, bug report and feature idea templates, tests and a synthetic example campaign.

## Release cautions
- This is a public **beta despite the 1.0.0 version number**. Back up your projects and Archives before experimenting.
- User-provided API keys and models are **not included**. Third-party APIs may charge you and send prompts off-device; verify billing and privacy settings with your provider.
- The included ZIP is **source code**. First run installs Python dependencies from PyPI. No packaged executable is included.
- No paid PDF license is required to use the source package, but third-party library licenses still apply to their own components.
- AI changes are not applied without explicit user approval, and may still be inaccurate. Validate all content and game rules.

See [BETA_DISCLAIMER.md](BETA_DISCLAIMER.md), [API_AND_DATA_NOTICE.md](API_AND_DATA_NOTICE.md), [LICENSE](LICENSE), and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Help shape the application by submitting an Issue through the repository's templates. Do not upload personal campaigns, secret tokens or proprietary content.
