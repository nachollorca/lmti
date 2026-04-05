"""/copy command — copy a message or conversation to the clipboard."""

import json
import shutil
import subprocess

from lmdk.datatypes import Message, UserMessage
from prompt_toolkit import PromptSession
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


# ? Do we need this? UserMessage inherits from Message
# we should have UserMessage().role equaling to "user", no?
def _message_role(msg: Message) -> str:
    """Return ``"user"`` or ``"assistant"`` for a message."""
    return "user" if isinstance(msg, UserMessage) else "assistant"


def _format_message_preview(index: int, msg: Message) -> str:
    """Return a one-line preview string for a message."""
    role = _message_role(msg)
    preview = msg.content[:_MESSAGE_PREVIEW_LENGTH].replace("\n", " ")
    ellipsis = "…" if len(msg.content) > _MESSAGE_PREVIEW_LENGTH else ""
    return f"  {index}. [{role}] {preview}{ellipsis}"


def _build_copy_payload(messages: list[Message], idx: int) -> tuple[str, str]:
    """Build the clipboard text and a human-readable label for a copy choice.

    Args:
        messages: The conversation history.
        idx: 1-based index; ``len(messages) + 1`` means the whole conversation.

    Returns:
        A ``(payload, label)`` tuple.
    """
    if idx == len(messages) + 1:
        lines = [json.dumps({"role": _message_role(m), "content": m.content}) for m in messages]
        return "\n".join(lines), "conversation (JSONL)"

    msg = messages[idx - 1]
    return msg.content, f"{_message_role(msg)} message #{idx}"


def handle_copy(console: Console, messages: list[Message]) -> None:
    """Prompt the user to pick a message or the whole conversation to copy."""
    if not messages:
        ui.print_panel(console, "No messages to copy.")
        return

    console.print()
    console.print("[bold]Copy to clipboard:[/bold]")
    # ? Shouldn't we use ui.prompt_selection() here?
    for i, msg in enumerate(messages, 1):
        console.print(_format_message_preview(i, msg))
    console.print(f"  {len(messages) + 1}. [dim]Entire conversation (JSONL)[/dim]")
    console.print()

    session = PromptSession()
    upper_bound = len(messages) + 1

    while True:
        choice = session.prompt("Select an item number (empty to cancel): ").strip()
        if not choice:
            return
        if choice.isdigit() and 1 <= int(choice) <= upper_bound:
            idx = int(choice)
            break

    payload, label = _build_copy_payload(messages, idx)

    if _copy_to_clipboard(payload):
        ui.print_panel(console, f"Copied {label} to clipboard.")
    else:
        ui.print_panel(
            console,
            "No clipboard tool found. Install xclip, xsel, or wl-copy.",
            border_style="red",
        )
