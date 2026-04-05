"""Rich / prompt-toolkit rendering helpers.

All display logic lives here — no business logic.
"""

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


def print_panel(
    console: Console, content: str | Text, *, border_style: str = "dim", **panel_kwargs
) -> None:
    """Print a Rich Panel wrapped in blank lines."""
    console.print()
    console.print(
        Panel(content, border_style=border_style, padding=(0, 1), expand=False, **panel_kwargs)
    )


def print_header(console: Console, role: str) -> None:
    """Print a header rule for the given *role* (``'user'`` or ``'assistant'``)."""
    role_styles = {"user": ("green", "You"), "assistant": ("blue", "Assistant")}
    color, label = role_styles[role]
    console.print()
    console.print(Rule(f"[bold {color}]{label}[/bold {color}]", align="left", style=color))


def prompt_selection(
    console: Console,
    title: str,
    items: list[str],
    *,
    prompt_text: str = "Select an item number (empty to cancel): ",
    extra_option: str | None = None,
) -> int | str | None:
    """Show a numbered list and prompt for a 1-based index or an extra option.

    Returns:
        The selected 1-based index (int), the extra option text (str), or ``None`` on cancel.
    """
    console.print()
    console.print(f"[bold]{title}[/bold]", highlight=False)
    for i, item in enumerate(items, 1):
        console.print(f"  [green]{i}[/green]. {item}", highlight=False)

    last_idx = len(items)
    if extra_option:
        last_idx += 1
        console.print(f"  [green]{last_idx}[/green]. {extra_option}", highlight=False)
    console.print()

    session = PromptSession()
    while True:
        choice = session.prompt(prompt_text).strip()
        if not choice:
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(items):
                return idx
            if extra_option and idx == last_idx:
                return extra_option
        console.print(f"[red]Invalid choice.[/red] Enter a number between 1 and {last_idx}.")


def prompt_system_instruction(console: Console, config: Config) -> str | None:
    """Prompt the user to set or clear the system instruction.

    Returns:
        The new system instruction, or ``None`` if cleared.
    """
    console.print()
    console.print("[bold]System Instruction:[/bold]")
    if config.settings.system_instruction:
        console.print(
            Panel(config.settings.system_instruction, border_style="dim", title="current"),
            highlight=False,
        )
    else:
        console.print("  [dim]No system instruction set.[/dim]", highlight=False)
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
    from lmti.commands import COMMANDS

    cmd_list = "  ".join(f"[dim]/{name}[/dim]" for name in COMMANDS)
    welcome_text = Text.from_markup(
        f"[dim]Model:[/dim]  {config.settings.model}\n"
        f"[dim]Alt+Enter[/dim] for newlines  ·  Commands: {cmd_list}"
    )
    console.print(Panel(welcome_text, border_style="dim", expand=False), highlight=False)
    console.print()
