from image_setup import candidate_checkpoint_dirs, checkpoints_help_text


def test_existing_local_and_legacy_models_found(tmp_path):
    home, local, roaming = (tmp_path/item for item in ('home', 'local', 'roaming'))
    first=local/'Comfy-Desktop'/'ComfyUI-Shared'/'models'/'checkpoints'
    second=home/'ComfyUI-Shared'/'models'/'checkpoints'
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    found=candidate_checkpoint_dirs(home=home,localappdata=local,appdata=roaming)
    assert first.resolve() in found
    assert second.resolve() in found


def test_finder_does_not_create_missing_model_folders(tmp_path):
    home, local, roaming = (tmp_path/item for item in ('home','local','roaming'))
    assert candidate_checkpoint_dirs(home=home,localappdata=local,appdata=roaming)==[]
    assert not local.exists()


def test_help_mentions_desktop_settings_and_art_studio():
    t=checkpoints_help_text()
    assert 'Storage' in t and 'Shared Models' in t and 'Generate Image' in t
