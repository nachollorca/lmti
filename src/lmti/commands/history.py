"""/history command — resume a previous conversation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown

from lmti import ui
from lmti.history import list_conversations, load_conversation

if TYPE_CHECKING:
    from lmti.repl import ReplState


def _format_timestamp(meta) -> str:
    """Return a human-readable local timestamp string."""
    local = meta.timestamp.astimezone()
    return local.strftime("%Y-%m-%d %H:%M:%S")


def _render_conversation(console: Console, state: ReplState, *, render_markdown: bool) -> None:
    """Re-render every message in the loaded conversation."""
    for msg in state.messages:
        ui.print_header(console, msg.role)
        if render_markdown and msg.role == "assistant":
            console.print(Markdown(msg.content))
        else:
            console.print(msg.content)
    console.print()


def handle_history(console: Console, state: ReplState, *, render_markdown: bool = True) -> None:
    """Prompt the user to pick a conversation to resume."""
    conversations = list_conversations()
    if not conversations:
        ui.print_panel(console, "No conversation history.")
        return

    items = [f"[dim]{_format_timestamp(m)}[/dim]  {m.preview}" for m in conversations]

    idx = ui.prompt_selection(console, "Conversation history:", items)
    if idx is None or not isinstance(idx, int):
        return

    meta = conversations[idx - 1]
    loaded = load_conversation(meta.path)

    state.messages.clear()
    state.messages.extend(loaded)
    state.conversation_path = meta.path

    _render_conversation(console, state, render_markdown=render_markdown)
    ui.print_panel(console, f"Resumed conversation from [bold]{_format_timestamp(meta)}[/bold]")
