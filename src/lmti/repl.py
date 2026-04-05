"""Main REPL loop for lmti."""

from lmdk.datatypes import AssistantMessage, Message, UserMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console

from lmti import ui
from lmti.commands import (
    KeyBindingState,
    LoopSignal,
    build_completer,
    build_key_bindings,
    dispatch,
    resolve_command,
)
from lmti.config import Config
from lmti.errors import handle_error


def run(config: Config) -> None:
    """Run the interactive REPL.

    Args:
        config: The application configuration (single source of truth).
    """
    console = Console(force_terminal=True)  # Why force_terminal?
    messages: list[Message] = []

    # KeyBindingState is a side-channel between key-binding handlers and this
    # loop — see its docstring for details on why this is necessary.
    kb_state = KeyBindingState()

    kb = build_key_bindings(state=kb_state)
    completer = build_completer()
    style = Style.from_dict(
        {
            "prompt": "ansigreen bold",
        }
    )
    session = PromptSession(key_bindings=kb, completer=completer, style=style)

    ui.print_welcome(console, config)

    while True:
        kb_state.action = None

        try:
            ui.print_header(console, "user")
            user_input = session.prompt([("class:prompt", "❯ ")])
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()

        command = resolve_command(keybinding_action=kb_state.action, text=text)
        if command:
            signal = dispatch(command=command, config=config, messages=messages, console=console)
            if signal is LoopSignal.BREAK:
                break
            if signal is LoopSignal.CONTINUE:
                continue

        # empty messagage -> do nothing
        if not text:
            continue

        # Send message
        messages.append(UserMessage(text))
        ui.print_header(console, "assistant")

        try:
            response = ui.stream_response(
                console=console,
                model=config.settings.model,
                messages=messages,
                render=config.settings.render_markdown,
                system_instruction=config.settings.system_instruction,
            )
            messages.append(AssistantMessage(response))
            console.print()
        except Exception as exc:
            messages.pop()  # remove the failed user message
            handle_error(exc, config, console)
