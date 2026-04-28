"""Tests for /copy."""

import json

from lmdk.datatypes import AssistantMessage, UserMessage

from lmti.commands import copy as copy_mod
from lmti.commands.copy import (
    _build_copy_payload,
    _copy_to_clipboard,
    _format_message_preview,
    handle_copy,
)


def test_format_message_preview_short():
    assert _format_message_preview(UserMessage("hi")) == "[user] hi"


def test_format_message_preview_long():
    out = _format_message_preview(UserMessage("x" * 200))
    assert out.endswith("…")


def test_build_copy_payload_single_message():
    msgs = [UserMessage("hello")]
    payload, label = _build_copy_payload(msgs, 1)
    assert payload == "hello"
    assert "user" in label and "#1" in label


def test_build_copy_payload_whole_conversation():
    msgs = [UserMessage("q"), AssistantMessage("a")]
    payload, label = _build_copy_payload(msgs, 3)  # len + 1
    lines = payload.split("\n")
    assert json.loads(lines[0]) == {"role": "user", "content": "q"}
    assert "JSONL" in label


def test_copy_to_clipboard_no_tool(monkeypatch):
    monkeypatch.setattr("lmti.commands.copy.shutil.which", lambda _: None)
    assert _copy_to_clipboard("hi") is False


def test_copy_to_clipboard_success(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "lmti.commands.copy.shutil.which",
        lambda cmd: f"/usr/bin/{cmd}" if cmd == "xclip" else None,
    )

    def fake_run(args, input, check):
        captured["args"] = args
        captured["input"] = input
        return None

    monkeypatch.setattr("lmti.commands.copy.subprocess.run", fake_run)
    assert _copy_to_clipboard("hello") is True
    assert captured["args"] == ["/usr/bin/xclip", "-selection", "clipboard"]
    assert captured["input"] == b"hello"


def test_copy_to_clipboard_xsel(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "lmti.commands.copy.shutil.which",
        lambda cmd: "/usr/bin/xsel" if cmd == "xsel" else None,
    )

    def fake_run(args, input, check):
        captured["args"] = args
        return None

    monkeypatch.setattr("lmti.commands.copy.subprocess.run", fake_run)
    assert _copy_to_clipboard("hi") is True
    assert captured["args"] == ["/usr/bin/xsel", "--clipboard", "--input"]


def test_copy_to_clipboard_wl_copy_uses_default_args(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "lmti.commands.copy.shutil.which",
        lambda cmd: "/usr/bin/wl-copy" if cmd == "wl-copy" else None,
    )

    def fake_run(args, input, check):
        captured["args"] = args
        return None

    monkeypatch.setattr("lmti.commands.copy.subprocess.run", fake_run)
    assert _copy_to_clipboard("hi") is True
    assert captured["args"] == ["/usr/bin/wl-copy"]


def test_copy_to_clipboard_falls_through_on_error(monkeypatch):
    monkeypatch.setattr(
        "lmti.commands.copy.shutil.which",
        lambda cmd: f"/usr/bin/{cmd}" if cmd in ("xclip", "pbcopy") else None,
    )

    calls = []

    def fake_run(args, input, check):
        calls.append(args[0])
        if args[0].endswith("xclip"):
            raise OSError("nope")
        return None

    monkeypatch.setattr("lmti.commands.copy.subprocess.run", fake_run)
    assert _copy_to_clipboard("hi") is True
    assert calls[-1].endswith("pbcopy")


def test_handle_copy_no_messages(console):
    handle_copy(console, [])  # should just print and return; no exception


def test_handle_copy_cancel(console, monkeypatch):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: None)
    handle_copy(console, [UserMessage("hi")])


def test_handle_copy_success(console, monkeypatch):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 1)
    monkeypatch.setattr(copy_mod, "_copy_to_clipboard", lambda text: True)
    handle_copy(console, [UserMessage("hi")])


def test_handle_copy_no_clipboard_tool(console, monkeypatch):
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 1)
    monkeypatch.setattr(copy_mod, "_copy_to_clipboard", lambda text: False)
    handle_copy(console, [UserMessage("hi")])
