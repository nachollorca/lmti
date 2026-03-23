"""Interactive TUI for chatting with language models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from lmdk import complete
from lmdk.datatypes import AssistantMessage, Message, UserMessage
from lmdk.errors import AuthenticationError, PermissionError as lmdkPermissionError
from lmdk.provider import load_provider
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.rule import Rule

from lmti.secrets import save_api_key, save_default_model, save_render_setting

AVAILABLE_MODELS = [
    "mistral:mistral-small-2603",
    "mistral:mistral-large-2512vertex",
    "vertex:gemini-2.5-flash",
]

COMMAND_META = {
    "/exit": "Exit the application (Ctrl+Q)",
    "/new": "Start a new conversation (Ctrl+N)",
    "/model": "Switch the current model (Ctrl+O)",
    "/render": "Toggle Markdown rendering (Ctrl+R)",
}

COMMANDS = list(COMMAND_META.keys())


class LoopSignal(Enum):
    """Signal returned by the command handler to control the main loop."""

    CONTINUE = auto()  # Skip to next iteration.
    BREAK = auto()  # Exit the loop.
    NOOP = auto()  # Not a command; proceed with normal message flow.


@dataclass
class SessionState:
    """Mutable state for the interactive session."""

    model: str
    render: bool
    messages: list[Message] = field(default_factory=list)
    console: Console = field(default_factory=Console)


def _build_key_bindings(session_state: dict) -> KeyBindings:
    """Build key bindings for the prompt session.

    Args:
        session_state: Mutable dict shared with the main loop to signal actions.
    """
    kb = KeyBindings()

    @kb.add("c-q")
    def _exit(event):
        session_state["action"] = "exit"
        event.app.exit(result="")

    @kb.add("c-n")
    def _new(event):
        session_state["action"] = "new"
        event.app.exit(result="")

    @kb.add("c-o")
    def _model(event):
        session_state["action"] = "model"
        event.app.exit(result="")

    @kb.add("c-r")
    def _render(event):
        session_state["action"] = "render"
        event.app.exit(result="")

    @kb.add("escape", "enter")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    return kb


def _switch_model(console: Console, current_model: str) -> str:
    """Prompt the user to pick a new model.

    Args:
        console: Rich console for output.
        current_model: The currently active model identifier.

    Returns:
        The newly selected model identifier.
    """
    console.print()
    console.print("[bold]Available models:[/bold]")
    for i, m in enumerate(AVAILABLE_MODELS, 1):
        marker = " [dim](current)[/dim]" if m == current_model else ""
        console.print(f"  {i}. {m}{marker}")
    console.print(f"  {len(AVAILABLE_MODELS) + 1}. Enter a custom model")
    console.print()

    model_completer = WordCompleter(AVAILABLE_MODELS)
    session = PromptSession()
    choice = session.prompt("Select model (number or identifier): ", completer=model_completer)
    choice = choice.strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(AVAILABLE_MODELS):
            return AVAILABLE_MODELS[idx - 1]
        if idx == len(AVAILABLE_MODELS) + 1:
            custom = session.prompt("Enter model identifier (provider:model): ")
            return custom.strip()

    # Treat as a direct model identifier if it looks like one.
    if choice:
        return choice

    return current_model


def _stream_response(
    console: Console, model: str, messages: list[Message], render: bool = True
) -> str:
    """Stream an assistant response and render it with Rich.

    Args:
        console: Rich console for output.
        model: The model identifier.
        messages: The conversation history.
        render: Whether to render as Markdown.

    Returns:
        The full assistant response text.
    """
    token_stream = complete(model=model, prompt=messages, stream=True)

    full_response = ""
    renderable = Markdown(full_response) if render else full_response
    with Live(renderable, console=console, refresh_per_second=15) as live:
        for token in token_stream:
            full_response += token
            live.update(Markdown(full_response) if render else full_response)

    return full_response


def _resolve_command(action: str | None, text: str) -> str | None:
    """Normalise keybinding actions and slash commands into a canonical name.

    Returns:
        A command name (e.g. ``"exit"``, ``"new"``), or ``None`` for regular text.
    """
    if action:
        return action
    if text.startswith("/") and f"/{text.lstrip('/')}" in COMMANDS:
        return text.lstrip("/")
    return None


def _handle_command(command: str, state: SessionState) -> LoopSignal:
    """Dispatch a single command and mutate *state* accordingly."""
    match command:
        case "exit":
            return LoopSignal.BREAK
        case "new":
            state.messages.clear()
            state.console.print()
            state.console.print(Rule("[bold]new conversation[/bold]"))
            state.console.print()
            return LoopSignal.CONTINUE
        case "model":
            state.model = _switch_model(state.console, state.model)
            save_default_model(state.model)
            state.console.print(f"\n[dim]Model switched to:[/dim] {state.model}\n")
            return LoopSignal.CONTINUE
        case "render":
            state.render = not state.render
            save_render_setting(state.render)
            status = "enabled" if state.render else "disabled"
            state.console.print(f"\n[dim]Markdown rendering {status}.[/dim]\n")
            return LoopSignal.CONTINUE
        case _:
            return LoopSignal.NOOP


def _handle_error(exc: Exception, state: SessionState) -> None:
    """Handle errors during response generation."""
    if isinstance(exc, (AuthenticationError, lmdkPermissionError)):
        provider_name = exc.provider.removesuffix("Provider").lower()
        provider_cls = load_provider(provider_name)
        key_name = provider_cls.api_key_name

        state.console.print(
            f"\n[bold red]Error:[/bold red] API key for [bold]{provider_name}[/bold] "
            "is missing or incorrect."
        )
        state.console.print(f"[dim]Expected environment variable:[/dim] {key_name}\n")

        key_session = PromptSession()
        api_key = key_session.prompt(f"Enter your {key_name}: ").strip()

        if api_key:
            save_api_key(key_name, api_key)
            state.console.print("[green]Key saved to ~/.config/lmti/.env[/green]\n")
    else:
        state.console.print(f"\n[bold red]Error:[/bold red] {exc}\n")

    if state.messages:
        state.messages.pop()


def _send_message(text: str, state: SessionState) -> None:
    """Append a user message, stream the assistant reply, and handle errors."""
    state.messages.append(UserMessage(content=text))

    state.console.print()
    state.console.print(Rule("[bold blue]You[/bold blue]"))
    state.console.print(Markdown(text) if state.render else text)
    state.console.print()
    state.console.print(Rule("[bold green]Assistant[/bold green]"))

    try:
        response_text = _stream_response(
            state.console, state.model, state.messages, render=state.render
        )
        state.messages.append(AssistantMessage(content=response_text))
        state.console.print()
    except Exception as exc:
        _handle_error(exc, state)


def run(model: str) -> None:
    """Run the interactive REPL.

    Args:
        model: Initial model identifier (provider:model).
    """
    import os

    render = os.environ.get("MARKDOWN_RENDER", "true").lower() == "true"
    state = SessionState(model=model, render=render)

    keybinding_action: dict[str, str | None] = {"action": None}
    completer = WordCompleter(COMMANDS, meta_dict=COMMAND_META, sentence=True)
    kb = _build_key_bindings(keybinding_action)
    style = Style.from_dict({"prompt": "ansigreen"})
    session = PromptSession(key_bindings=kb, completer=completer, style=style)

    state.console.print(Rule("[bold]lmti[/bold]"))
    state.console.print(f"[dim]Model:[/dim] {model}")
    state.console.print("[dim]Alt+Enter[/dim] for newlines  [dim]Forward slash[/dim] for commands")
    state.console.print()

    while True:
        keybinding_action["action"] = None

        try:
            user_input = session.prompt([("class:prompt", "❯ ")])
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()
        command = _resolve_command(keybinding_action["action"], text)

        if command:
            signal = _handle_command(command, state)
            if signal is LoopSignal.BREAK:
                break
            if signal is LoopSignal.CONTINUE:
                continue

        if not text:
            continue

        _send_message(text, state)
