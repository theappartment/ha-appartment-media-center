"""Recognize only the visible keyring dialog and its cancel control."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


def load_helper():
    atspi = SimpleNamespace(StateType=SimpleNamespace(SHOWING='showing', ENABLED='enabled'),
                            CoordType=SimpleNamespace(SCREEN=0), generate_mouse_event=Mock())
    spec = importlib.util.spec_from_file_location('keyring_shell_test', Path(__file__).parents[1] / 'ubuntu/keyring_shell.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict('sys.modules', {'gi': Mock(), 'gi.repository': SimpleNamespace(Atspi=atspi)}):
        spec.loader.exec_module(module)
    return module


class Node:
    def __init__(self, role, name='', children=(), shown=True):
        self.role, self.name, self.children, self.shown = role, name, children, shown
        self.action = Mock()
        self.action.get_n_actions.return_value = 0
        self.component = Mock()
        self.component.get_extents.return_value = SimpleNamespace(x=150, y=200, width=80, height=40)
    def get_role_name(self): return self.role
    def get_name(self):
        assert self.role != 'password text'
        return self.name
    def get_child_count(self): return len(self.children)
    def get_child_at_index(self, i): return self.children[i]
    def get_state_set(self): return SimpleNamespace(contains=lambda state: self.shown)
    def get_action_iface(self): return self.action
    def get_component_iface(self): return self.component


def test_unrelated_and_hidden_dialogs_untouched():
    m = load_helper()
    cancel = Node('push button', 'Cancel')
    assert not m.cancel_dialog(Node('dialog', children=[Node('label', 'Unsaved document'), cancel]))
    assert not m.cancel_dialog(Node('dialog', children=[Node('label', 'Unlock keyring'), cancel], shown=False))
    m.Atspi.generate_mouse_event.assert_not_called()
    cancel.action.do_action.assert_not_called()


def test_shell_cancel_uses_discovered_bounds_and_never_reads_password():
    m = load_helper()
    cancel = Node('push button', 'Cancel')
    dialog = Node('dialog', children=[Node('label', 'Default keyring locked'), Node('password text'), cancel])
    def click(*args):
        dialog.shown = False
        return True
    m.Atspi.generate_mouse_event.side_effect = click
    assert m.cancel_dialog(dialog)
    m.Atspi.generate_mouse_event.assert_called_once_with(190, 220, 'b1c')


def test_accessible_cancel_preferred():
    m = load_helper()
    cancel = Node('push button', 'Annulla')
    dialog = Node('dialog', children=[Node('label', 'Sblocca portachiavi'), cancel])
    cancel.action.get_n_actions.return_value = 1
    cancel.action.get_action_name.return_value = 'click'
    def action(index):
        dialog.shown = False
        return True
    cancel.action.do_action.side_effect = action
    assert m.cancel_dialog(dialog)
    m.Atspi.generate_mouse_event.assert_not_called()
