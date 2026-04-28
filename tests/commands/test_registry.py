"""Tests for the command registry, completer, and key bindings."""

from lmti.commands import (
    COMMANDS,
    KeyBindingState,
    _format_binding,
    build_completer,
    build_key_bindings,
    resolve_command,
)


def test_resolve_command_keybinding_action():
    assert resolve_command(keybinding_action="model", text="") == "model"


def test_resolve_command_slash():
    assert resolve_command(keybinding_action=None, text="/exit") == "exit"


def test_resolve_command_unknown_slash():
    assert resolve_command(keybinding_action=None, text="/nope") is None


def test_resolve_command_plain_text():
    assert resolve_command(keybinding_action=None, text="hello world") is None


def test_format_binding():
    assert _format_binding("escape m") == "Alt+M"


def test_build_completer_words_and_meta():
    completer = build_completer()
    assert set(completer.words) == {"/" + name for name in COMMANDS}
    assert "Alt+M" in completer.meta_dict["/model"]


def test_build_key_bindings_registers_all_commands():
    state = KeyBindingState()
    kb = build_key_bindings(state=state)
    # Each command + the Alt+Enter newline binding.
    assert len(kb.bindings) == len(COMMANDS) + 1


def test_key_binding_handler_sets_state_action():
    state = KeyBindingState()
    kb = build_key_bindings(state=state)

    # Find the binding for "exit" (escape q) and invoke its handler with a fake event.
    def _key_strs(b):
        return [k.value if hasattr(k, "value") else k for k in b.keys]

    exit_binding = next(b for b in kb.bindings if _key_strs(b) == ["escape", "q"])

    class _App:
        def exit(self, result=""):
            self.exited = True

    class _Event:
        app = _App()

    exit_binding.handler(_Event())
    assert state.action == "exit"


def test_alt_enter_inserts_newline():
    kb = build_key_bindings(state=KeyBindingState())

    def _key_strs(b):
        return [k.value if hasattr(k, "value") else k for k in b.keys]

    newline_binding = next(b for b in kb.bindings if _key_strs(b) == ["escape", "c-m"])
    inserted = []

    class _Buffer:
        def insert_text(self, text):
            inserted.append(text)

    class _Event:
        current_buffer = _Buffer()

    newline_binding.handler(_Event())
    assert inserted == ["\n"]
