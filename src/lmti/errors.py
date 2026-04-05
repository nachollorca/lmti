"""Error-recovery handlers."""

from lmdk.errors import APIPermissionError, AuthenticationError
from lmdk.provider import load_provider
from prompt_toolkit import PromptSession
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lmti import ui
from lmti.config import Config


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
    ui.print_panel(console, error_text, border_style="red")

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

    from lmti.commands.model import handle_model as run_model

    match = re.search(r"lmdk\.providers\.(\w+)", str(exc))
    provider = match.group(1).capitalize() if match else "Unknown"

    ui.print_panel(
        console,
        f"[bold]{provider}[/bold] provider is not supported or missing dependencies.",
        border_style="red",
    )

    run_model(console, config)


def handle_error(exc: Exception, config: Config, console: Console) -> None:
    """Handle errors during response generation.

    Note: the caller is responsible for removing the failed user message
    from the conversation history.
    """
    if isinstance(exc, (AuthenticationError, APIPermissionError)):
        _handle_auth_error(exc, config, console)
    elif isinstance(exc, ImportError) and "lmdk.providers." in str(exc):
        _handle_import_error(exc, config, console)
    else:
        ui.print_panel(
            console,
            str(exc),
            border_style="red",
            title="[bold red]error[/bold red]",
        )
