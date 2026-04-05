"""Rich / prompt-toolkit rendering helpers.

All display logic lives here — no business logic.
"""

from typing import Literal

from lmdk import complete
from lmdk.datatypes import Message
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from lmti.config import Config


# TODO: use print_panel for new chat too
# There is no need to have a different kind of separator for new chats
# Lets use these panels for all system information that does not modify the message list in any way
def print_panel(
    console: Console, content: str | Text, *, border_style: str = "dim", **panel_kwargs
) -> None:
    """Print a Rich Panel wrapped in blank lines."""
    console.print()
    console.print(
        Panel(content, border_style=border_style, padding=(0, 1), expand=False, **panel_kwargs)
    )
    console.print()


# TODO: this can be removed
def print_rule(
    console: Console,
    label: str,
    *,
    align: Literal["left", "center", "right"] = "center",
    style: str = "dim",
    characters: str = "═",
) -> None:
    """Print a Rich Rule wrapped in blank lines."""
    console.print()
    console.print(Rule(label, align=align, style=style, characters=characters))
    console.print()


# TODO: we can have a print_rule function that takes "role" instead of having two functions
def print_user_header(console: Console) -> None:
    """Print the 'You' header rule."""
    console.print()
    console.print(Rule("[bold green]You[/bold green]", align="left", style="green"))


def print_assistant_header(console: Console) -> None:
    """Print the 'Assistant' header rule."""
    console.print()
    console.print(Rule("[bold blue]Assistant[/bold blue]", align="left", style="blue"))


# ? How does this handle wrong inputs (empty or out of index or not digit)?
def prompt_selection(
    console: Console,
    title: str,
    items: list[str],
    *,
    prompt_text: str = "Select an item number (empty to cancel): ",
) -> int | None:
    """Show a numbered list and prompt for a 1-based index.

    Returns:
        The selected 1-based index, or ``None`` on cancel.
    """
    console.print()
    console.print(f"[bold]{title}[/bold]")
    for i, item in enumerate(items, 1):
        console.print(f"  {i}. {item}")
    console.print()

    session = PromptSession()
    while True:
        choice = session.prompt(prompt_text).strip()
        if not choice:
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return int(choice)


def prompt_system_instruction(console: Console, config: Config) -> str | None:
    """Prompt the user to set or clear the system instruction.

    Returns:
        The new system instruction, or ``None`` if cleared.
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


def stream_response(
    console: Console,
    model: str,
    messages: list[Message],
    *,
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
    renderable: Markdown | str = Markdown(full_response) if render else full_response
    with Live(renderable, console=console, refresh_per_second=30) as live:
        for token in token_stream:
            full_response += token
            live.update(Markdown(full_response) if render else full_response)

    return full_response


def print_welcome(console: Console, config: Config) -> None:
    """Print the welcome banner."""
    # TODO: show a string version of commands.COMMANDS with dim and stuff for help
    welcome_text = Text.from_markup(
        f"[dim]Model:[/dim]  {config.settings.model}\n"
        "[dim]Alt+Enter[/dim] for newlines  ·  [dim]/ (forward slash)[/dim] for commands"
    )
    console.print(Panel(welcome_text, border_style="dim", expand=False))
    console.print()
