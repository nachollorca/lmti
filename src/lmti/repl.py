"""Main REPL loop for lmti."""

from lmdk.datatypes import AssistantMessage, Message, UserMessage
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown

from lmti import ui
from lmti.commands import (
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

    # ? kb_state is used to collect keybinds? Do we need it to be a dict, tho?
    # ? Is it because we store all the meta about commands in the COMMANDS constant?
    kb_state: dict[str, str | None] = {"action": None}

    kb = build_key_bindings(session_state=kb_state)
    completer = build_completer()
    style = Style.from_dict({"prompt": "ansigreen"})  # TODO: see what other styles are there
    session = PromptSession(key_bindings=kb, completer=completer, style=style)

    ui.print_welcome(console, config)

    while True:
        kb_state["action"] = None

        try:
            # ? Why wouldn't we handle this with `handle_error` too?
            user_input = session.prompt([("class:prompt", "❯ ")])
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()

        command = resolve_command(action=kb_state["action"], text=text)
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
        ui.print_user_header(console)
        # ? Doesn't this console.print of the user message duplicate the user messge?
        # Once for the prompt, another for the markdown render, I mean
        # I like the idea of rendering the user message in case it has markdown, but
        # maybe we have to flush the prompt above? If that becomes difficult, lets just use
        # the prompt input without any rendering for the user message
        console.print(Markdown(text) if config.settings.render_markdown else text)
        ui.print_assistant_header(console)

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
