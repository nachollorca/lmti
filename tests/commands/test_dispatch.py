"""Tests for lmti.commands.dispatch."""

from pathlib import Path

import pytest

from lmti.commands import LoopSignal, dispatch
from lmti.config import Config
from lmti.repl import ReplState


@pytest.fixture
def state():
    s = ReplState()
    s.messages.append(type("M", (), {"role": "user", "content": "hi"})())
    s.conversation_path = Path("/tmp/whatever")
    return s


def test_dispatch_exit(state, console):
    config = Config()
    assert dispatch("exit", config, state, console) is LoopSignal.BREAK


def test_dispatch_unknown(state, console):
    assert dispatch("zzz", Config(), state, console) is LoopSignal.NOOP


def test_dispatch_new_clears_state(state, console):
    config = Config()
    assert dispatch("new", config, state, console) is LoopSignal.CONTINUE
    assert state.messages == []
    assert state.conversation_path is None


def test_dispatch_render_toggles_and_saves(state, console, tmp_path, monkeypatch):
    monkeypatch.setattr("lmti.config.CONFIG_PATH", tmp_path / "c.yaml")
    config = Config()
    assert config.settings.render_markdown is True
    dispatch("render", config, state, console)
    assert config.settings.render_markdown is False
    dispatch("render", config, state, console)
    assert config.settings.render_markdown is True


def test_dispatch_system_sets_instruction(state, console, tmp_path, monkeypatch):
    monkeypatch.setattr("lmti.config.CONFIG_PATH", tmp_path / "c.yaml")
    monkeypatch.setattr("lmti.ui.prompt_system_instruction", lambda console, config: "be terse")
    config = Config()
    dispatch("system", config, state, console)
    assert config.settings.system_instruction == "be terse"


def test_dispatch_system_clears_instruction(state, console, tmp_path, monkeypatch):
    monkeypatch.setattr("lmti.config.CONFIG_PATH", tmp_path / "c.yaml")
    monkeypatch.setattr("lmti.ui.prompt_system_instruction", lambda console, config: None)
    config = Config()
    config.settings.system_instruction = "old"
    dispatch("system", config, state, console)
    assert config.settings.system_instruction is None


def _make_spy():
    calls = []

    def _spy(*args, **kwargs):
        calls.append((args, kwargs))

    return _spy, calls


def test_dispatch_model_calls_handler(state, console, monkeypatch):
    spy, calls = _make_spy()
    monkeypatch.setattr("lmti.commands.model.handle_model", spy)
    config = Config()
    assert dispatch("model", config, state, console) is LoopSignal.CONTINUE
    assert calls == [((console, config), {})]


def test_dispatch_copy_calls_handler(state, console, monkeypatch):
    spy, calls = _make_spy()
    monkeypatch.setattr("lmti.commands.copy.handle_copy", spy)
    dispatch("copy", Config(), state, console)
    assert calls[0][0] == (console, state.messages)


def test_dispatch_history_calls_handler(state, console, monkeypatch):
    spy, calls = _make_spy()
    monkeypatch.setattr("lmti.commands.history.handle_history", spy)
    config = Config()
    dispatch("history", config, state, console)
    assert calls[0][0] == (console, state)
    assert calls[0][1] == {"render_markdown": config.settings.render_markdown}


def test_dispatch_undo_calls_handler(state, console, monkeypatch):
    spy, calls = _make_spy()
    monkeypatch.setattr("lmti.commands.undo.handle_undo", spy)
    dispatch("undo", Config(), state, console)
    assert calls[0][0] == (console, state)
