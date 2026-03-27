"""Interactive TUI for chatting with language models."""

from enum import Enum, auto

from lmdk import complete
from lmdk.datatypes import AssistantMessage, Message, UserMessage
from lmdk.errors import APIPermissionError, AuthenticationError
from lmdk.provider import load_provider
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from lmti.config import Config

COMMAND_META = {
    "/exit": "Exit the application (Ctrl+Q)",
    "/new": "Start a new conversation (Ctrl+N)",
    "/model": "Switch the current model (Ctrl+O)",
    "/render": "Toggle Markdown rendering (Ctrl+R)",
    "/system": "Set or clear the system instruction (Ctrl+S)",
}

COMMANDS = list(COMMAND_META.keys())


class LoopSignal(Enum):
    """Signal returned by the command handler to control the main loop."""

    CONTINUE = auto()  # Skip to next iteration.
    BREAK = auto()  # Exit the loop.
    NOOP = auto()  # Not a command; proceed with normal message flow.


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

    @kb.add("c-s")
    def _system(event):
        session_state["action"] = "system"
        event.app.exit(result="")

    @kb.add("escape", "enter")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    return kb


def _switch_model(console: Console, config: Config) -> str:
    """Prompt the user to pick a new model.

    Returns:
        The newly selected model identifier.
    """
    console.print()
    console.print("[bold]Available models:[/bold]")
    for i, m in enumerate(config.models, 1):
        marker = " [dim](current)[/dim]" if m == config.settings.model else ""
        console.print(f"  {i}. {m}{marker}")
    console.print()

    model_completer = WordCompleter(config.models)
    session = PromptSession()

    while True:
        choice = session.prompt(
            "Select a model index or provide an identifier: ", completer=model_completer
        )
        choice = choice.strip()

        if not choice:
            return config.settings.model

        selected = _parse_model_choice(choice, config.models)
        if selected:
            return selected

        console.print(
            "[red]Error:[/red] Invalid model format. Use 'provider:model_id' or a number."
        )


def _set_system_instruction(console: Console, config: Config) -> str | None:
    """Prompt the user to set a new system instruction.

    Returns:
        The new system instruction, or None if cleared.
    """
    console.print()
    console.print("[bold]System Instruction:[/bold]")
    if config.settings.system_instruction:
        console.print(
            Panel(config.settings.system_instruction, border_style="dim", title="current")
        )
    else:
        console.print("  [dim]No system instruction set.[/dim]")
    console.print()

    session = PromptSession()
    new_instruction = session.prompt("Enter new system instruction (empty to clear): ").strip()

    return new_instruction or None


def _parse_model_choice(choice: str, available_models: list[str]) -> str | None:
    """Parse a model choice string into a model identifier.

    Args:
        choice: The user's input string.
        available_models: List of known model identifiers.

    Returns:
        The matched model identifier, or None if invalid.
    """
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(available_models):
            return available_models[idx - 1]
        return None

    # Treat as a direct model identifier if it looks like one.
    if ":" in choice:
        parts = choice.split(":")
        if len(parts) == 2 and all(parts):
            return choice

    return None


def _stream_response(
    console: Console,
    model: str,
    messages: list[Message],
    render: bool = True,
    system_instruction: str | None = None,
) -> str:
    """Stream an assistant response and render it with Rich.

    Returns:
        The full assistant response text.
    """
    token_stream = complete(
        model=model, prompt=messages, stream=True, system_instruction=system_instruction
    )

    full_response = ""
    renderable = Markdown(full_response) if render else full_response
    with Live(renderable, console=console, refresh_per_second=30) as live:
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


def _handle_command(
    command: str, config: Config, messages: list[Message], console: Console
) -> LoopSignal:
    """Dispatch a single command and mutate *config* / *messages* accordingly."""
    match command:
        case "exit":
            return LoopSignal.BREAK
        case "new":
            messages.clear()
            console.print()
            console.print(Rule("[bold]new conversation[/bold]", characters="═", style="dim"))
            console.print()
            return LoopSignal.CONTINUE
        case "model":
            config.settings.model = _switch_model(console, config)
            config.save()
            console.print()
            console.print(
                Panel(
                    f"Model switched to [bold]{config.settings.model}[/bold]",
                    border_style="dim",
                    padding=(0, 1),
                    expand=False,
                )
            )
            console.print()
            return LoopSignal.CONTINUE
        case "render":
            config.settings.render_markdown = not config.settings.render_markdown
            config.save()
            status = "enabled" if config.settings.render_markdown else "disabled"
            console.print()
            console.print(
                Panel(
                    f"Markdown rendering [bold]{status}[/bold]",
                    border_style="dim",
                    padding=(0, 1),
                )
            )
            console.print()
            return LoopSignal.CONTINUE
        case "system":
            config.settings.system_instruction = _set_system_instruction(console, config)
            config.save()

            status_msg = (
                f"System instruction set to: [italic]{config.settings.system_instruction}[/italic]"
                if config.settings.system_instruction
                else "System instruction cleared."
            )
            console.print()
            console.print(Panel(status_msg, border_style="dim", padding=(0, 1), expand=False))
            console.print()
            return LoopSignal.CONTINUE
        case _:
            return LoopSignal.NOOP


def _handle_auth_error(
    exc: AuthenticationError | APIPermissionError, config: Config, console: Console
) -> None:
    """Handle missing or incorrect provider configuration."""
    provider_name = exc.provider.removesuffix("Provider").lower()
    provider_cls = load_provider(provider_name)
    required_vars = provider_cls.required_env
    if isinstance(required_vars, str):
        required_vars = (required_vars,)

    error_text = Text.from_markup(
        f"Configuration for [bold]{provider_name}[/bold] is missing or incorrect.\n"
        f"[dim]Required environment variables:[/dim] {', '.join(required_vars)}"
    )
    console.print()
    console.print(Panel(error_text, border_style="red", padding=(0, 1), expand=False))
    console.print()

    key_session = PromptSession()
    any_saved = False
    for var_name in required_vars:
        value = key_session.prompt(f"Enter {var_name}: ").strip()
        if value:
            config.set_api_key(var_name, value)
            any_saved = True

    if any_saved:
        console.print(
            Panel(
                "Configuration saved to [dim]~/.config/lmti/config.yaml[/dim]",
                border_style="green",
                padding=(0, 1),
                expand=False,
            )
        )
        console.print()


def _handle_import_error(exc: ImportError, config: Config, console: Console) -> None:
    """Handle missing provider dependencies."""
    import re

    match = re.search(r"lmdk\.providers\.(\w+)", str(exc))
    provider = match.group(1).capitalize() if match else "Unknown"

    console.print()
    console.print(
        Panel(
            f"[bold]{provider}[/bold] provider is not supported or missing dependencies.",
            border_style="red",
            padding=(0, 1),
            expand=False,
        )
    )

    config.settings.model = _switch_model(console, config)
    config.save()
    console.print()
    console.print(
        Panel(
            f"Model switched to [bold]{config.settings.model}[/bold]",
            border_style="dim",
            padding=(0, 1),
            expand=False,
        )
    )
    console.print()


def _handle_error(
    exc: Exception, config: Config, messages: list[Message], console: Console
) -> None:
    """Handle errors during response generation."""
    if isinstance(exc, (AuthenticationError, APIPermissionError)):
        _handle_auth_error(exc, config, console)
    elif isinstance(exc, ImportError) and "lmdk.providers." in str(exc):
        _handle_import_error(exc, config, console)
    else:
        console.print()
        console.print(
            Panel(
                str(exc),
                title="[bold red]error[/bold red]",
                border_style="red",
                padding=(0, 1),
                expand=False,
            )
        )
        console.print()

    if messages:
        messages.pop()


def _send_message(text: str, config: Config, messages: list[Message], console: Console) -> None:
    """Append a user message, stream the assistant reply, and handle errors."""
    messages.append(UserMessage(content=text))

    console.print()
    console.print(Rule("[bold green]You[/bold green]", align="left", style="green"))
    console.print(Markdown(text) if config.settings.render_markdown else text)
    console.print()
    console.print(Rule("[bold blue]Assistant[/bold blue]", align="left", style="blue"))

    try:
        response_text = _stream_response(
            console,
            config.settings.model,
            messages,
            render=config.settings.render_markdown,
            system_instruction=config.settings.system_instruction,
        )
        messages.append(AssistantMessage(content=response_text))
        console.print()
    except Exception as exc:
        _handle_error(exc, config, messages, console)


def run(config: Config) -> None:
    """Run the interactive REPL.

    Args:
        config: The application configuration (single source of truth).
    """
    console = Console(force_terminal=True)
    messages: list[Message] = []

    keybinding_action: dict[str, str | None] = {"action": None}
    completer = WordCompleter(COMMANDS, meta_dict=COMMAND_META, sentence=True)
    kb = _build_key_bindings(keybinding_action)
    style = Style.from_dict({"prompt": "ansigreen"})
    session = PromptSession(key_bindings=kb, completer=completer, style=style)

    welcome_text = Text.from_markup(
        f"[dim]Model:[/dim]  {config.settings.model}\n"
        "[dim]Alt+Enter[/dim] for newlines  ·  [dim]/ (forward slash)[/dim] for commands"
    )
    console.print(Panel(welcome_text, border_style="dim", expand=False))
    console.print()

    while True:
        keybinding_action["action"] = None

        try:
            user_input = session.prompt([("class:prompt", "❯ ")])
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()
        command = _resolve_command(keybinding_action["action"], text)

        if command:
            signal = _handle_command(command, config, messages, console)
            if signal is LoopSignal.BREAK:
                break
            if signal is LoopSignal.CONTINUE:
                continue

        if not text:
            continue

        _send_message(text, config, messages, console)
