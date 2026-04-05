"""Command registry, dispatch, and key-binding builder."""

from dataclasses import dataclass, field
from enum import Enum, auto

from lmdk.datatypes import Message
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console

from lmti import ui
from lmti.config import Config


@dataclass(frozen=True, slots=True)
class Command:
    """Definition of a single REPL command."""

    # TODO: move the comments for the attributes to the docstring

    description: str
    binding: str  # prompt-toolkit key format, e.g. "c-q"
    handler: str | None  # dotted module path or None for inline commands


COMMANDS: dict[str, Command] = {
    "exit": Command("Exit the application", "c-q", None),
    "new": Command("Start a new conversation", "c-n", None),
    "model": Command("Switch the current model", "c-l", "commands.model"),
    "render": Command("Toggle Markdown rendering", "c-r", None),
    "system": Command("Set or clear the system instruction", "c-i", None),
    "copy": Command("Copy a message or conversation", "c-c", "commands.copy"),
}


class LoopSignal(Enum):
    """Signal returned by dispatch to control the main REPL loop."""

    CONTINUE = auto()
    BREAK = auto()
    NOOP = auto()


@dataclass
class KeyBindingState:
    """Mutable state shared between key-binding handlers and the REPL loop.

    prompt-toolkit key handlers cannot return values — they can only call
    ``event.app.exit()`` to break out of the prompt.  This object acts as a
    side-channel: a handler writes the command name into :attr:`action`, and
    the REPL reads it after ``session.prompt()`` returns.
    """

    action: str | None = field(default=None)


def build_key_bindings(state: KeyBindingState) -> KeyBindings:
    """Generate key bindings from the COMMANDS registry.

    Args:
        state: Shared mutable state; ``state.action`` is set on key press.
    """
    kb = KeyBindings()

    for name, cmd_def in COMMANDS.items():
        # Capture *name* in a default argument so closures don't share the loop variable.
        def _make_handler(cmd_name: str):
            def _handler(event):
                state.action = cmd_name
                event.app.exit(result="")

            return _handler

        kb.add(cmd_def.binding)(_make_handler(name))

    # Consider the special case of new lines
    @kb.add("escape", "enter")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    return kb


def build_completer() -> WordCompleter:
    """Derive a ``WordCompleter`` from the COMMANDS registry."""
    words = ["/" + k for k in COMMANDS]
    meta = {"/" + k: v.description for k, v in COMMANDS.items()}
    return WordCompleter(words, meta_dict=meta, sentence=True)


def resolve_command(keybinding_action: str | None, text: str) -> str | None:
    """Normalise a keybinding action or ``/slash`` input into a canonical command name.

    Args:
        keybinding_action: Command name set by a key binding handler (e.g. ``"model"``),
            or ``None`` when the user submitted text normally.
        text: The raw text from the prompt input.

    Returns:
        A command name, or ``None`` for regular text.
    """
    if keybinding_action:
        return keybinding_action
    if text.startswith("/"):
        name = text.lstrip("/")
        if name in COMMANDS:
            return name
    return None


def dispatch(command: str, config: Config, messages: list[Message], console: Console) -> LoopSignal:
    """Execute *command* and return a loop signal."""
    match command:
        case "exit":
            return LoopSignal.BREAK

        case "new":
            messages.clear()
            ui.print_rule(console, "[bold]new conversation[/bold]")
            return LoopSignal.CONTINUE

        case "model":
            from lmti.commands.model import handle_model

            handle_model(console, config)
            return LoopSignal.CONTINUE

        case "render":
            config.settings.render_markdown = not config.settings.render_markdown
            config.save()
            status = "enabled" if config.settings.render_markdown else "disabled"
            ui.print_panel(console, f"Markdown rendering [bold]{status}[/bold]")
            return LoopSignal.CONTINUE

        case "system":
            config.settings.system_instruction = ui.prompt_system_instruction(console, config)
            config.save()
            status_msg = (
                f"System instruction set to: [italic]{config.settings.system_instruction}[/italic]"
                if config.settings.system_instruction
                else "System instruction cleared."
            )
            ui.print_panel(console, status_msg)
            return LoopSignal.CONTINUE

        case "copy":
            from lmti.commands.copy import handle_copy

            handle_copy(console, messages)
            return LoopSignal.CONTINUE

        case _:
            return LoopSignal.NOOP
