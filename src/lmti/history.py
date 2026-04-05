"""Conversation history persistence.

Stores conversations as JSONL files in ``~/.lmti/history/``.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from lmdk.datatypes import AssistantMessage, Message, UserMessage

HISTORY_DIR = Path.home() / ".lmti" / "history"
MAX_CONVERSATIONS = 50
PREVIEW_LENGTH = 80


@dataclass(frozen=True, slots=True)
class ConversationMeta:
    """Lightweight summary of a stored conversation."""

    path: Path
    timestamp: datetime
    preview: str


def _timestamp_to_filename() -> str:
    """Generate a filesystem-safe filename from the current UTC time."""
    now = datetime.now(tz=timezone.utc)
    return now.strftime("%Y-%m-%dT%H-%M-%S") + ".jsonl"


def _filename_to_timestamp(name: str) -> datetime:
    """Parse a timestamp from a history filename."""
    stem = name.removesuffix(".jsonl")
    return datetime.strptime(stem, "%Y-%m-%dT%H-%M-%S").replace(tzinfo=timezone.utc)


def _read_preview(path: Path) -> str:
    """Read the first line of a JSONL file and return a truncated preview."""
    try:
        first_line = path.read_text().split("\n", 1)[0]
        data = json.loads(first_line)
        content = data.get("content", "")
        preview = content[:PREVIEW_LENGTH].replace("\n", " ")
        ellipsis = "…" if len(content) > PREVIEW_LENGTH else ""
        return f"[{data.get('role', '?')}] {preview}{ellipsis}"
    except (json.JSONDecodeError, OSError):
        return "[unreadable]"


def _enforce_cap() -> None:
    """Delete the oldest conversations when the count exceeds MAX_CONVERSATIONS."""
    files = sorted(HISTORY_DIR.glob("*.jsonl"), key=lambda p: p.name)
    excess = len(files) - MAX_CONVERSATIONS
    for f in files[:excess]:
        f.unlink(missing_ok=True)


def save_conversation(messages: list[Message], path: Path | None = None) -> Path:
    """Persist a conversation to disk.

    Args:
        messages: The conversation to save.
        path: Existing file to overwrite, or ``None`` to create a new one.

    Returns:
        The path the conversation was written to.
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    if path is None:
        path = HISTORY_DIR / _timestamp_to_filename()
    lines = [json.dumps({"role": m.role, "content": m.content}) for m in messages]
    path.write_text("\n".join(lines) + "\n")
    _enforce_cap()
    return path


def list_conversations() -> list[ConversationMeta]:
    """Return metadata for all stored conversations, newest first."""
    if not HISTORY_DIR.exists():
        return []
    metas: list[ConversationMeta] = []
    for p in HISTORY_DIR.glob("*.jsonl"):
        try:
            ts = _filename_to_timestamp(p.name)
        except ValueError:
            continue
        metas.append(ConversationMeta(path=p, timestamp=ts, preview=_read_preview(p)))
    metas.sort(key=lambda m: m.timestamp, reverse=True)
    return metas


def load_conversation(path: Path) -> list[Message]:
    """Read a JSONL conversation file back into Message objects."""
    messages: list[Message] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        role = data["role"]
        content = data["content"]
        if role == "assistant":
            messages.append(AssistantMessage(content))
        else:
            messages.append(UserMessage(content))
    return messages
