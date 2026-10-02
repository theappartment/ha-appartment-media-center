"""Cancel only a visible GNOME Shell keyring dialog through accessibility."""
import json
import os
from pathlib import Path
import time
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi


def descendants(node, budget, depth=0):
    budget[0] -= 1
    if budget[0] < 0 or depth > 24:
        raise RuntimeError('Accessibility tree exceeds limit')
    if depth and not visible(node):
        return
    yield node
    if node.get_role_name() == 'password text':
        return  # Never read password contents or descend into the input.
    for index in range(node.get_child_count()):
        yield from descendants(node.get_child_at_index(index), budget, depth + 1)


def visible(node):
    return node.get_state_set().contains(Atspi.StateType.SHOWING)


def cancel_dialog(dialog):
    if not visible(dialog):
        return False
    nodes = list(descendants(dialog, [300]))
    labels = [n.get_name().casefold() for n in nodes if n.get_role_name() == 'label' and visible(n)]
    if not any('keyring' in text or 'portachiavi' in text for text in labels):
        return False
    buttons = [n for n in nodes if n.get_role_name() == 'push button'
               and n.get_name().strip().casefold() in ('cancel', 'annulla') and visible(n)]
    if len(buttons) != 1:
        raise RuntimeError('Keyring cancel button not identified')
    button = buttons[0]
    if not button.get_state_set().contains(Atspi.StateType.ENABLED):
        raise RuntimeError('Cancel button disabled')
    action = button.get_action_iface()
    actions = [i for i in range(action.get_n_actions())
               if action.get_action_name(i) in ('click', 'press', 'activate')]
    if actions:
        if not action.do_action(actions[0]):
            raise RuntimeError('Cancel action failed')
    else:
        # GNOME Shell 42 exposes the button but no AT-SPI actions.
        # Use its current accessible bounds, never hard-coded coordinates.
        bounds = button.get_component_iface().get_extents(Atspi.CoordType.SCREEN)
        if bounds.width <= 0 or bounds.height <= 0 or not visible(dialog) or not visible(button):
            raise RuntimeError('Cancel button is no longer visible')
        if not Atspi.generate_mouse_event(bounds.x + bounds.width // 2,
                                          bounds.y + bounds.height // 2, 'b1c'):
            raise RuntimeError('Cancel click failed')
    deadline = time.monotonic() + 1
    while visible(dialog):
        if time.monotonic() >= deadline:
            raise RuntimeError('Keyring dialog is still visible')
        time.sleep(.05)
    return True


def dismiss():
    Atspi.set_timeout(400, 700)
    desktop = Atspi.get_desktop(0)
    for index in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(index)
        if app.get_name() != 'gnome-shell':
            continue
        process = Path('/proc') / str(app.get_process_id())
        if process.stat().st_uid != os.getuid() or (process / 'exe').resolve().name != 'gnome-shell':
            continue
        # Stop as soon as the matching dialog closes; other dialogs are untouched.
        for node in descendants(app, [2000]):
            if node.get_role_name() == 'dialog' and cancel_dialog(node):
                return {'closed': 1}
    return {'closed': 0}


if __name__ == '__main__':
    try:
        print(json.dumps(dismiss()))
    except Exception:
        raise SystemExit(1)
