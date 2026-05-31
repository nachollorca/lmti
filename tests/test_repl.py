"""Tests for lmti.repl."""

from pathlib import Path

from lmdk.datatypes import AssistantMessage

from lmti import repl
from lmti.commands import LoopSignal
from lmti.config import Config


class _FakeSession:
    """Stands in for prompt_toolkit.PromptSession inside the REPL."""

    def __init__(self, inputs):
        self.inputs = list(inputs)

    def prompt(self, *args, **kwargs):
        if not self.inputs:
            raise EOFError
        item = self.inputs.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def _install_fake_session(monkeypatch, inputs):
    fake = _FakeSession(inputs)
    monkeypatch.setattr(repl, "PromptSession", lambda **kwargs: fake)
    return fake


def test_run_handles_keyboard_interrupt(monkeypatch, console):
    monkeypatch.setattr(repl, "_repl", lambda *a, **k: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(repl, "Console", lambda **k: console)
    repl.run(Config())
    assert "Bye" in console.export_text()


def test_repl_eof_breaks(monkeypatch, console):
    _install_fake_session(monkeypatch, [EOFError()])
    repl._repl(Config(), console)


def test_repl_dispatches_command_break(monkeypatch, console):
    _install_fake_session(monkeypatch, ["/exit"])
    repl._repl(Config(), console)


def test_repl_dispatches_continue_then_eof(monkeypatch, console):
    _install_fake_session(monkeypatch, ["/new", EOFError()])
    repl._repl(Config(), console)


def test_repl_skips_empty_input(monkeypatch, console):
    _install_fake_session(monkeypatch, ["", EOFError()])
    repl._repl(Config(), console)


def test_repl_sends_message_and_saves(monkeypatch, console):
    _install_fake_session(monkeypatch, ["hello", EOFError()])

    monkeypatch.setattr(
        "lmti.repl.ui.stream_response",
        lambda **kwargs: "world",
    )
    saved = []
    monkeypatch.setattr(
        "lmti.repl.save_conversation",
        lambda msgs, path: saved.append((list(msgs), path)) or Path("/tmp/x.jsonl"),
    )
    repl._repl(Config(), console)
    assert saved
    msgs, _ = saved[0]
    assert msgs[0].content == "hello"
    assert isinstance(msgs[1], AssistantMessage)


def test_repl_handles_send_error(monkeypatch, console):
    _install_fake_session(monkeypatch, ["hi", EOFError()])

    def boom(**kwargs):
        raise RuntimeError("upstream down")

    monkeypatch.setattr("lmti.repl.ui.stream_response", boom)
    handled = []
    monkeypatch.setattr(
        "lmti.repl.handle_error",
        lambda exc, cfg, cons: handled.append(type(exc).__name__),
    )
    repl._repl(Config(), console)
    assert handled == ["RuntimeError"]


def test_repl_signals(monkeypatch, console, config_paths):
    """Cover the LoopSignal.BREAK / CONTINUE branches in dispatch."""
    _install_fake_session(monkeypatch, ["/render", "/exit"])
    monkeypatch.setattr("lmti.repl.dispatch", _scripted_dispatch())
    repl._repl(Config(), console)


def _scripted_dispatch():
    signals = iter([LoopSignal.CONTINUE, LoopSignal.BREAK])

    def _d(command, config, state, console):
        return next(signals)

    return _d
