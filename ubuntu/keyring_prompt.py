"""Cancel visible GCR dialogs on the local X11 session without touching secrets."""
import json
import os
import subprocess
from pathlib import Path
import time
from Xlib import X, error
from Xlib.display import Display
from Xlib.protocol.event import ClientMessage

PROMPTERS = {'/usr/libexec/gcr-prompter', '/usr/lib/gcr/gcr-prompter'}


def is_prompter(window, pid_atom):
    """Match both window class and the executable owned by this user."""
    if window.get_wm_class() != ('gcr-prompter', 'Gcr-prompter'):
        return False
    prop = window.get_full_property(pid_atom, X.AnyPropertyType)
    if prop is None or len(prop.value) != 1:
        return False
    try:
        process = Path('/proc') / str(int(prop.value[0]))
        return (process.stat().st_uid == os.getuid()
                and str((process / 'exe').resolve(strict=True)) in PROMPTERS)
    except (OSError, ValueError):
        return False


def dismiss():
    display = Display()
    try:
        root = display.screen().root
        clients = root.get_full_property(display.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
        if clients is None:
            raise RuntimeError('Elenco finestre X11 non disponibile')
        pid_atom = display.intern_atom('_NET_WM_PID')
        delete = display.intern_atom('WM_DELETE_WINDOW')
        protocols = display.intern_atom('WM_PROTOCOLS')
        targets = []
        for wid in clients.value:
            window = display.create_resource_object('window', int(wid))
            try:
                if not is_prompter(window, pid_atom) or window.get_attributes().map_state != X.IsViewable:
                    continue
                if delete not in (window.get_wm_protocols() or []):
                    raise RuntimeError('La finestra portachiavi non supporta la chiusura')
                window.send_event(ClientMessage(window=window, client_type=protocols,
                                               data=(32, [delete, X.CurrentTime, 0, 0, 0])))
                targets.append(window)
            except error.BadWindow:
                continue  # The user may already have dismissed it.
        display.sync()
        remaining = list(targets)
        deadline = time.monotonic() + 1.5
        while remaining and time.monotonic() < deadline:
            for window in list(remaining):
                try:
                    visible = window.get_attributes().map_state == X.IsViewable
                except error.BadWindow:
                    visible = False
                if not visible:
                    remaining.remove(window)
            if remaining:
                time.sleep(.05)
        if remaining:
            raise RuntimeError('La finestra portachiavi non si è chiusa')
        return {'closed': len(targets)}
    finally:
        display.close()


if __name__ == '__main__':
    try:
        shell = subprocess.run(
            ['/usr/bin/python3', str(Path(__file__).with_name('keyring_shell.py'))],
            capture_output=True, text=True, timeout=3, check=True)
        closed = json.loads(shell.stdout)['closed']
        print(json.dumps({'closed': closed + dismiss()['closed']}))
    except Exception:
        # Do not expose desktop/window metadata through the API or logs.
        raise SystemExit(1)
