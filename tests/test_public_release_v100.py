from pathlib import Path


def test_public_version_label_and_no_restrictive_pdf_dependency():
    root = Path(__file__).resolve().parent.parent
    app = (root / 'app.py').read_text(encoding='utf-8')
    req = (root / 'requirements.txt').read_text(encoding='utf-8').lower()
    assert 'APP_VERSION = "1.1.0-beta.4"' in app
    assert 'pymupdf' not in req and 'pypdfium2' in req
    assert 'pypdf' in req


def test_beta_notices_and_no_bundled_models():
    root = Path(__file__).resolve().parent.parent
    for f in ('LICENSE', 'README.md','BETA_DISCLAIMER.md','API_AND_DATA_NOTICE.md','PRIVACY.md','THIRD_PARTY_NOTICES.md'):
        assert (root / f).is_file()
    assert not any(p.suffix.lower() in {'.safetensors','.ckpt','.gguf','.pt','.pth','.onnx'} for p in root.rglob('*'))
