"""Interactive TUI for chatting with language models."""

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.rule import Rule

from lmtk import get_response

AVAILABLE_MODELS = [
    "mistral:mistral-small-2603",
    "vertex:gemini-2.5-flash",
]

COMMANDS = ["/exit", "/new", "/model"]


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


def _stream_response(console: Console, model: str, messages: list[dict]) -> str:
    """Stream an assistant response and render it with Rich.

    Args:
        console: Rich console for output.
        model: The model identifier.
        messages: The conversation history.

    Returns:
        The full assistant response text.
    """
    token_stream = get_response(model=model, messages=messages, stream=True)

    full_response = ""
    with Live(Markdown(full_response), console=console, refresh_per_second=12) as live:
        for token in token_stream:
            full_response += token
            live.update(Markdown(full_response))

    return full_response


def run(model: str) -> None:
    """Run the interactive REPL.

    Args:
        model: Initial model identifier (provider:model).
    """
    console = Console()
    messages: list[dict] = []
    session_state: dict = {"action": None}

    completer = WordCompleter(COMMANDS, sentence=True)
    kb = _build_key_bindings(session_state)
    session = PromptSession(key_bindings=kb, completer=completer)

    console.print(Rule("[bold]lmsh[/bold]"))
    console.print(f"[dim]Model:[/dim] {model}")
    console.print(
        "[dim]Ctrl+Q[/dim] exit  [dim]Ctrl+N[/dim] new chat  [dim]Ctrl+O[/dim] switch model"
    )
    console.print()

    while True:
        session_state["action"] = None

        try:
            user_input = session.prompt("You> ")
        except (EOFError, KeyboardInterrupt):
            break

        # Handle key-binding triggered actions.
        action = session_state["action"]
        if action == "exit":
            break
        if action == "new":
            messages.clear()
            console.print()
            console.print(Rule("[bold]new conversation[/bold]"))
            console.print()
            continue
        if action == "model":
            model = _switch_model(console, model)
            console.print(f"\n[dim]Model switched to:[/dim] {model}\n")
            continue

        text = user_input.strip()
        if not text:
            continue

        # Handle slash commands typed explicitly.
        if text == "/exit":
            break
        if text == "/new":
            messages.clear()
            console.print()
            console.print(Rule("[bold]new conversation[/bold]"))
            console.print()
            continue
        if text == "/model":
            model = _switch_model(console, model)
            console.print(f"\n[dim]Model switched to:[/dim] {model}\n")
            continue

        # Regular message.
        messages.append({"role": "user", "content": text})
        console.print()
        console.print(Rule("[bold blue]You[/bold blue]"))
        console.print(Markdown(text))
        console.print()
        console.print(Rule("[bold green]Assistant[/bold green]"))

        try:
            response_text = _stream_response(console, model, messages)
        except Exception as exc:
            console.print(f"\n[bold red]Error:[/bold red] {exc}\n")
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": response_text})
        console.print()
