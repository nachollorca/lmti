"""Tests for lmti.history."""

import json
from datetime import UTC, datetime

import pytest
from lmdk.datatypes import AssistantMessage, UserMessage

from lmti import history


@pytest.fixture(autouse=True)
def _redirect_history_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_DIR", tmp_path)
    return tmp_path


def test_filename_timestamp_roundtrip():
    name = history._timestamp_to_filename()
    parsed = history._filename_to_timestamp(name)
    assert isinstance(parsed, datetime)
    assert parsed.tzinfo == UTC


def test_read_preview_short(tmp_path):
    p = tmp_path / "f.jsonl"
    p.write_text(json.dumps({"role": "user", "content": "hello"}) + "\n")
    assert history._read_preview(p) == "[user] hello"


def test_read_preview_long(tmp_path):
    p = tmp_path / "f.jsonl"
    p.write_text(json.dumps({"role": "user", "content": "x" * 200}) + "\n")
    preview = history._read_preview(p)
    assert preview.endswith("…")
    assert "x" * history.PREVIEW_LENGTH in preview


def test_read_preview_unreadable(tmp_path):
    p = tmp_path / "f.jsonl"
    p.write_text("not json\n")
    assert history._read_preview(p) == "[unreadable]"


def test_save_conversation_writes_jsonl(tmp_path):
    msgs = [UserMessage("hi"), AssistantMessage("yo")]
    path = history.save_conversation(msgs)
    lines = path.read_text().strip().split("\n")
    assert json.loads(lines[0]) == {"role": "user", "content": "hi"}
    assert json.loads(lines[1]) == {"role": "assistant", "content": "yo"}


def test_save_conversation_overwrites_existing_path(tmp_path):
    target = tmp_path / "fixed.jsonl"
    history.save_conversation([UserMessage("a")], target)
    history.save_conversation([UserMessage("b")], target)
    assert "b" in target.read_text()
    assert "a" not in target.read_text()


def test_save_conversation_enforces_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "MAX_CONVERSATIONS", 3)
    # Pre-populate with 5 stale files.
    for i in range(5):
        (tmp_path / f"2020-01-0{i + 1}T00-00-00.jsonl").write_text("{}\n")
    history.save_conversation([UserMessage("new")])
    remaining = sorted(p.name for p in tmp_path.glob("*.jsonl"))
    assert len(remaining) == 3
    # Oldest removed first.
    assert "2020-01-01T00-00-00.jsonl" not in remaining


def test_list_conversations_sorts_newest_first(tmp_path):
    (tmp_path / "2020-01-01T00-00-00.jsonl").write_text(
        json.dumps({"role": "user", "content": "old"}) + "\n"
    )
    (tmp_path / "2025-06-15T12-00-00.jsonl").write_text(
        json.dumps({"role": "user", "content": "new"}) + "\n"
    )
    (tmp_path / "garbage.jsonl").write_text("{}\n")  # bad name, skipped
    metas = history.list_conversations()
    assert len(metas) == 2
    assert metas[0].timestamp.year == 2025


def test_list_conversations_missing_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "HISTORY_DIR", tmp_path / "does-not-exist")
    assert history.list_conversations() == []


def test_load_conversation(tmp_path):
    p = tmp_path / "c.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "q"})
        + "\n"
        + json.dumps({"role": "assistant", "content": "a"})
        + "\n"
        + "\n"  # blank line should be skipped
    )
    msgs = history.load_conversation(p)
    assert len(msgs) == 2
    assert isinstance(msgs[0], UserMessage)
    assert isinstance(msgs[1], AssistantMessage)
    assert msgs[1].content == "a"
