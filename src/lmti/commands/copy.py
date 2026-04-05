"""/copy command — copy a message or conversation to the clipboard."""

import json
import shutil
import subprocess

from lmdk.datatypes import Message
from rich.console import Console

from lmti import ui

_MESSAGE_PREVIEW_LENGTH = 80


def _copy_to_clipboard(text: str) -> bool:
    """Copy *text* to the system clipboard.

    Returns:
        ``True`` on success, ``False`` if no clipboard tool was found.
    """
    candidates = ["xclip", "xsel", "wl-copy", "pbcopy"]
    for cmd in candidates:
        path = shutil.which(cmd)
        if path is None:
            continue
        args: list[str] = []
        match cmd:
            case "xclip":
                args = [path, "-selection", "clipboard"]
            case "xsel":
                args = [path, "--clipboard", "--input"]
            case _:
                args = [path]
        try:
            subprocess.run(args, input=text.encode(), check=True)  # noqa: S603
            return True
        except (subprocess.CalledProcessError, OSError):
            continue
    return False


def _format_message_preview(msg: Message) -> str:
    """Return a one-line preview string for a message."""
    preview = msg.content[:_MESSAGE_PREVIEW_LENGTH].replace("\n", " ")
    ellipsis = "…" if len(msg.content) > _MESSAGE_PREVIEW_LENGTH else ""
    return f"[{msg.role}] {preview}{ellipsis}"


def _build_copy_payload(messages: list[Message], idx: int) -> tuple[str, str]:
    """Build the clipboard text and a human-readable label for a copy choice.

    Args:
        messages: The conversation history.
        idx: 1-based index; ``len(messages) + 1`` means the whole conversation.

    Returns:
        A ``(payload, label)`` tuple.
    """
    if idx == len(messages) + 1:
        lines = [json.dumps({"role": m.role, "content": m.content}) for m in messages]
        return "\n".join(lines), "conversation (JSONL)"

    msg = messages[idx - 1]
    return msg.content, f"{msg.role} message #{idx}"


def handle_copy(console: Console, messages: list[Message]) -> None:
    """Prompt the user to pick a message or the whole conversation to copy."""
    if not messages:
        ui.print_panel(console, "No messages to copy.")
        return

    items = [_format_message_preview(msg) for msg in messages]
    items.append("[dim]Entire conversation (JSONL)[/dim]")

    idx = ui.prompt_selection(console, "Copy to clipboard:", items)
    if idx is None:
        return

    payload, label = _build_copy_payload(messages, idx)

    if _copy_to_clipboard(payload):
        ui.print_panel(console, f"Copied {label} to clipboard.")
    else:
        ui.print_panel(
            console,
            "No clipboard tool found. Install xclip, xsel, or wl-copy.",
            border_style="red",
        )
