# Checklist for a later **binary/Steam** release

This source-only GitHub beta intentionally does **not** bundle Python dependencies, PDFium binaries, AI models or an installer. Its source-code license is in `LICENSE`. The following tasks remain before distributing Windows executables or on Steam:

- Resolve exact pinned dependency versions and review each direct and transitive license.
- Ship complete third-party license notices and any required source/notice files for PDFium and binary dependencies.
- Check PyInstaller and any bootloader licenses/notice conditions; audit generated DLLs and other binaries.
- Audit artwork, fonts, asset licenses, trademarks and game-rule text.
- Test clean Windows install and launcher, signed binary, security scanner, backups, AI/API safety and data handling.
- Review the project's beta/disclaimer/license wording with qualified legal counsel for commercial distribution.
- Consider changing the evaluation-only source license if accepting third-party source contributions.

**The project is not asserted to be legally certified or security audited.**
