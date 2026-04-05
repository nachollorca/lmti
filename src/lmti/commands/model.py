"""/model command — switch the active model."""

from prompt_toolkit import PromptSession
from rich.console import Console

from lmti import ui
from lmti.config import Config


def _get_manual_model(console: Console) -> str | None:
    """Prompt for a manual model identifier (provider:model_id)."""
    session = PromptSession()
    while True:
        manual = session.prompt("Enter new model (provider:model_id): ").strip()
        if not manual:
            return None
        if ":" in manual and all(manual.split(":", 1)):
            return manual
        console.print("[red]Error:[/red] Invalid format. Use 'provider:model_id'.")


def handle_model(console: Console, config: Config) -> None:
    """Prompt the user to pick a new model, update config, and confirm."""
    items = [
        f"{m}{' [dim](current)[/dim]' if m == config.settings.model else ''}" for m in config.models
    ]

    selection = ui.prompt_selection(
        console, "Available models:", items, extra_option="Add a manual model identifier"
    )

    if selection is None:
        return

    if isinstance(selection, int):
        config.settings.model = config.models[selection - 1]
    elif selection == "Add a manual model identifier":
        manual = _get_manual_model(console)
        if not manual:
            return
        config.settings.model = manual
    else:
        return

    config.save()
    ui.print_panel(console, f"Model switched to [bold]{config.settings.model}[/bold]")
