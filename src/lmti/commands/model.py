"""/model command — switch the active model."""

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console

from lmti import ui
from lmti.config import Config


def _parse_model_choice(choice: str, available_models: list[str]) -> str | None:
    """Parse a model choice string into a model identifier.

    Returns:
        The matched model identifier, or ``None`` if invalid.
    """
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(available_models):
            return available_models[idx - 1]
        return None

    if ":" in choice:
        parts = choice.split(":")
        if len(parts) == 2 and all(parts):
            return choice

    return None


def handle_model(console: Console, config: Config) -> None:
    """Prompt the user to pick a new model, update config, and confirm."""
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
            return  # cancelled

        selected = _parse_model_choice(choice, config.models)
        if selected:
            config.settings.model = selected
            config.save()
            ui.print_panel(console, f"Model switched to [bold]{config.settings.model}[/bold]")
            return

        console.print(
            "[red]Error:[/red] Invalid model format. Use 'provider:model_id' or a number."
        )
