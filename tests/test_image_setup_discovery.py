from pathlib import Path
import image_setup


def test_discovers_existing_modern_and_legacy_comfy_checkpoint_folders(tmp_path):
    home = tmp_path / 'user'
    local = tmp_path / 'local'
    roaming = tmp_path / 'roaming'
    modern = local / 'Comfy-Desktop' / 'ComfyUI-Shared' / 'models' / 'checkpoints'
    legacy = home / 'ComfyUI-Shared' / 'models' / 'checkpoints'
    modern.mkdir(parents=True)
    legacy.mkdir(parents=True)
    discovered = image_setup.candidate_checkpoint_dirs(home=home,localappdata=local,appdata=roaming)
    assert modern.resolve() in discovered
    assert legacy.resolve() in discovered
    assert len(discovered) == 2


def test_absent_folder_is_not_created_or_inferred(tmp_path):
    home=tmp_path/'u'
    local=tmp_path/'l'
    roaming=tmp_path/'a'
    assert image_setup.candidate_checkpoint_dirs(home=home,localappdata=local,appdata=roaming) == []
    assert not local.exists()


def test_help_explains_manual_custom_directory_and_download_limitations():
    help_text=image_setup.checkpoints_help_text()
    assert 'Shared Models' in help_text
    assert 'checkpoint' in help_text
    assert 'custom' in help_text.lower()
    assert 'does not send generation jobs' in help_text
