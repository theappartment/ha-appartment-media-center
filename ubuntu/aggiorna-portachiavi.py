#!/usr/bin/env python3
"""Install the narrowly scoped Ubuntu backend update, retaining existing changes."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil
import tempfile

HARDWARE_METHOD = '''    async def dismiss_keyring_prompt(self):
        # Separate process bounds X11 connection and response time.
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'app.keyring_prompt', cwd=str(ROOT),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        try:
            output, _ = await asyncio.wait_for(process.communicate(), timeout=5)
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()
        if process.returncode:
            raise RuntimeError('Chiusura portachiavi non riuscita nella sessione X11')
        return json.loads(output)

'''


def replace_once(text, old, new):
    if new in text:
        return text
    if text.count(old) != 1:
        raise ValueError('Versione backend non riconosciuta: nessun file modificato')
    return text.replace(old, new, 1)


def update(root):
    app = root / 'app'
    sources = {name: (app / name).read_text() for name in ('models.py', 'controller.py', 'hardware.py')}
    updated = dict(sources)
    s = sources['models.py']
    for marker in ("action: Literal[", "elif self.action in ('reload',"):
        lines = s.splitlines(keepends=True)
        found = [i for i, line in enumerate(lines) if marker in line]
        if len(found) != 1:
            raise ValueError('Schema comandi non riconosciuto: nessun file modificato')
        i = found[0]
        lines[i] = replace_once(lines[i], "'release_screen',", "'release_screen', 'dismiss_keyring_prompt',")
        s = ''.join(lines)
    updated['models.py'] = s
    s = replace_once(sources['controller.py'], "return {'feature_stage':", "return {'capabilities': ['dismiss_keyring_prompt'], 'feature_stage':")
    updated['controller.py'] = replace_once(s, "if command.action == 'sync_content':\n", "if command.action == 'dismiss_keyring_prompt':\n            return await self.hw.dismiss_keyring_prompt()\n        elif command.action == 'sync_content':\n")
    s = replace_once(sources['hardware.py'], 'import signal\n', 'import signal\nimport sys\n')
    updated['hardware.py'] = replace_once(s, '    async def browser(self):\n', HARDWARE_METHOD + '    async def browser(self):\n')
    updated['keyring_prompt.py'] = Path(__file__).with_name('keyring_prompt.py').read_text()
    changes = {}
    for name, content in updated.items():
        compile(content, name, 'exec')
        path = app / name
        if not path.exists() or path.read_text() != content:
            changes[name] = content
    if not changes:
        print('Aggiornamento già presente. Riavvia il servizio se non lo hai ancora fatto.')
        return
    backup_root = root / '.local-backups'
    backup_root.mkdir(exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix='keyring-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-', dir=backup_root))
    for name in changes:
        if (app / name).exists():
            shutil.copy2(app / name, backup / name)
    for name, content in changes.items():
        path = app / name
        with tempfile.NamedTemporaryFile(mode='w', dir=app, delete=False) as tmp:
            tmp.write(content)
            temp_path = Path(tmp.name)
        temp_path.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
        temp_path.replace(path)
    print('Aggiornamento installato. Backup:', backup)
    print('Per attivarlo: systemctl --user restart appartment-media-center.service')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', type=Path, default=Path.home() / 'media-center')
    args = parser.parse_args()
    try:
        update(args.path.resolve())
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + '\n')
