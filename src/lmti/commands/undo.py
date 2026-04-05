"""/undo command — go back to a previous user message."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from lmti import ui
from lmti.history import save_conversation

if TYPE_CHECKING:
    from lmti.repl import ReplState

_MESSAGE_PREVIEW_LENGTH = 80


def _format_user_preview(content: str) -> str:
    """Return a one-line preview string for a user message."""
    preview = content[:_MESSAGE_PREVIEW_LENGTH].replace("\n", " ")
    ellipsis = "…" if len(content) > _MESSAGE_PREVIEW_LENGTH else ""
    return f"[user] {preview}{ellipsis}"


def handle_undo(console: Console, state: ReplState) -> None:
    """Prompt the user to pick a previous user message to return to."""
    # Collect user messages with their indices in the full message list.
    user_entries = [(i, msg) for i, msg in enumerate(state.messages) if msg.role == "user"]

    if not user_entries:
        ui.print_panel(console, "No messages to undo.")
        return

    items = [_format_user_preview(msg.content) for _, msg in user_entries]

    idx = ui.prompt_selection(console, "Undo to:", items)
    if idx is None or not isinstance(idx, int):
        return

    # idx is 1-based selection; map to position in state.messages.
    msg_index = user_entries[idx - 1][0]

    # Truncate everything from the selected user message onward.
    removed = len(state.messages) - msg_index
    del state.messages[msg_index:]

    if not state.messages:
        # Selected the first user message — behaves like /new.
        state.conversation_path = None
        ui.print_panel(console, "[bold]Conversation cleared.[/bold]")
    else:
        save_conversation(state.messages, state.conversation_path)
        ui.print_panel(
            console,
            f"Undone — removed {removed} message{'s' if removed != 1 else ''}.",
        )
