"""The installer preserves local changes and validates before writing."""
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('update_keyring', Path(__file__).parents[1] / 'ubuntu/aggiorna-portachiavi.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def fixture_backend(tmp_path):
    app = tmp_path / 'app'
    app.mkdir()
    (app / 'models.py').write_text("from typing import Literal\nclass Command:\n    action: Literal['release_screen', 'sync_content']\n    def check(self):\n        if False: pass\n        elif self.action in ('reload', 'release_screen', 'sync_content'): pass\n")
    (app / 'controller.py').write_text("# local customization\nclass Controller:\n    def status(self):\n        return {'feature_stage': 3}\n    async def apply(self, command):\n        if command.action == 'sync_content':\n            return {}\n")
    (app / 'hardware.py').write_text('import signal\nclass Hardware:\n    async def browser(self):\n        pass\n')
    return app


def test_update_and_idempotence(tmp_path):
    app = fixture_backend(tmp_path)
    before = {p.name: p.read_bytes() for p in app.iterdir()}
    installer.update(tmp_path)
    assert 'local customization' in (app / 'controller.py').read_text()
    assert (app / 'keyring_prompt.py').exists()
    after = {p.name: p.read_bytes() for p in app.iterdir()}
    backups = list((tmp_path / '.local-backups').iterdir())
    assert len(backups) == 1
    assert {p.name: p.read_bytes() for p in backups[0].iterdir()} == before
    installer.update(tmp_path)
    assert after == {p.name: p.read_bytes() for p in app.iterdir()}
    assert len(list((tmp_path / '.local-backups').iterdir())) == 1


def test_unknown_version_leaves_all_files_untouched(tmp_path):
    app = fixture_backend(tmp_path)
    (app / 'controller.py').write_text('print("unsupported")\n')
    before = {p.name: p.read_bytes() for p in app.iterdir()}
    with pytest.raises(ValueError):
        installer.update(tmp_path)
    assert before == {p.name: p.read_bytes() for p in app.iterdir()}
    assert not (tmp_path / '.local-backups').exists()
