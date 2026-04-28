"""Tests for /history."""

from datetime import UTC, datetime
from pathlib import Path

from lmdk.datatypes import AssistantMessage, UserMessage

from lmti.commands import history as history_cmd
from lmti.commands.history import handle_history
from lmti.history import ConversationMeta
from lmti.repl import ReplState


def test_handle_history_empty(console, monkeypatch):
    monkeypatch.setattr(history_cmd, "list_conversations", lambda: [])
    state = ReplState()
    handle_history(console, state)
    assert state.messages == []


def _meta(name="a"):
    return ConversationMeta(
        path=Path(f"/tmp/{name}.jsonl"),
        timestamp=datetime(2025, 1, 2, 3, 4, 5, tzinfo=UTC),
        preview="[user] hi",
    )


def test_handle_history_cancel(console, monkeypatch):
    monkeypatch.setattr(history_cmd, "list_conversations", lambda: [_meta()])
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: None)
    state = ReplState()
    handle_history(console, state)
    assert state.messages == []


def test_handle_history_loads_selected(console, monkeypatch):
    meta = _meta()
    monkeypatch.setattr(history_cmd, "list_conversations", lambda: [meta])
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 1)
    monkeypatch.setattr(
        history_cmd,
        "load_conversation",
        lambda path: [UserMessage("q"), AssistantMessage("a")],
    )
    state = ReplState()
    handle_history(console, state, render_markdown=True)
    assert [m.content for m in state.messages] == ["q", "a"]
    assert state.conversation_path == meta.path


def test_handle_history_no_markdown(console, monkeypatch):
    monkeypatch.setattr(history_cmd, "list_conversations", lambda: [_meta()])
    monkeypatch.setattr("lmti.ui.prompt_selection", lambda *a, **k: 1)
    monkeypatch.setattr(history_cmd, "load_conversation", lambda path: [AssistantMessage("plain")])
    state = ReplState()
    handle_history(console, state, render_markdown=False)
    assert state.messages[0].content == "plain"
