# Refactoring Plan: `src/lmti/tui.py` → modular structure

## Goal

Split the monolithic `tui.py` (~580 lines) into focused modules with clear
responsibilities.  The public entry point (`run(config)`) stays the same; only
the internal organisation changes.

---

## Target file structure

```text
src/lmti/
├── cli.py              # Entry point – update import: tui.run → repl.run
├── config.py           # Unchanged
├── repl.py             # Main REPL loop (formerly tui.py)
├── ui.py               # All Rich / prompt-toolkit rendering helpers
├── errors.py           # Error-recovery handlers
├── commands/
│   ├── __init__.py     # Command registry, dispatch, key-binding builder
│   ├── copy.py         # /copy command implementation
│   └── model.py        # /model command implementation
└── __init__.py
```

---

## Module specifications

### 1. `commands/__init__.py` — Registry & dispatch

#### 1a. `CommandDef` dataclass

```python
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True, slots=True)
class CommandDef:
    description: str
    binding: str          # prompt-toolkit format, e.g. "c-q"
    handler: str | None   # dotted path or None for inline commands
```

#### 1b. `COMMANDS` registry

Single source of truth.  Every command is declared here exactly once.
Derived artefacts (completer word-list, meta-dict, key bindings) are all
built from this dict — no separate `COMMAND_META` / `COMMANDS` lists.

```python
COMMANDS: dict[str, CommandDef] = {
    "exit":   CommandDef("Exit the application",                  "c-q",  None),
    "new":    CommandDef("Start a new conversation",              "c-n",  None),
    "model":  CommandDef("Switch the current model",              "c-m",  "commands.model"),
    "render": CommandDef("Toggle Markdown rendering",             "c-r",  None),
    "system": CommandDef("Set or clear the system instruction",   "c-i",  None),
    "copy":   CommandDef("Copy a message or conversation",        "c-c",  "commands.copy"),
}
```

#### 1c. `build_key_bindings(session_state: dict) -> KeyBindings`

Generate all bindings in a loop over `COMMANDS`:

```python
for name, cmd_def in COMMANDS.items():
    # closure that sets session_state["action"] = name and exits
    ...
```

Also add the `escape+enter → newline` binding here.

#### 1d. `build_completer() -> WordCompleter`

Derive the completer from `COMMANDS` — word list is `["/" + k for k in COMMANDS]`,
meta dict is `{"/" + k: v.description for k, v in COMMANDS.items()}`.

#### 1e. `resolve_command(action: str | None, text: str) -> str | None`

Move from current `tui.py`.  Normalises keybinding actions and `/slash`
input into a canonical command name, or `None` for regular text.

#### 1f. `dispatch(command, config, messages, console) -> LoopSignal`

`LoopSignal` enum moves here too.

The function uses a `match` block.  Trivial commands are handled inline:

- **exit** → return `BREAK`
- **new** → `messages.clear()`, call `ui.print_rule(console, "new conversation")`,
  return `CONTINUE`
- **render** → toggle `config.settings.render_markdown`, `config.save()`,
  call `ui.print_panel(...)`, return `CONTINUE`
- **system** → call `ui.prompt_system_instruction(console, config)`, save,
  print confirmation panel, return `CONTINUE`

Complex commands delegate to their module:

- **model** → `from lmti.commands.model import run as run_model; run_model(console, config)`
- **copy** → `from lmti.commands.copy import run as run_copy; run_copy(console, messages)`

---

### 2. `commands/model.py` — `/model` command

Move these functions here from `tui.py`:
- `_parse_model_choice(choice, available_models) -> str | None`
- `run(console, config) -> None`
  Corresponds to the current `_switch_model` logic **plus** the save-and-confirm
  panel that currently lives in `_handle_command("model")` and is duplicated in
  `_handle_import_error`.

The function should:
1. Call `ui.prompt_selection()` to show the numbered model list and get a choice.
2. Also accept a raw `provider:model_id` string (this is model-specific logic
   that stays here, not in the generic `prompt_selection`).
3. Update `config.settings.model`, call `config.save()`.
4. Call `ui.print_panel()` to confirm.

---

### 3. `commands/copy.py` — `/copy` command

Move these functions here from `tui.py`:
- `_copy_to_clipboard(text) -> bool` (platform clipboard I/O)
- `_message_role(msg) -> str`
- `_format_message_preview(index, msg) -> str`
- `_build_copy_payload(messages, idx) -> tuple[str, str]`
- `run(console, messages) -> None`
  Corresponds to current `_copy_content`.

The function should use `ui.prompt_selection()` for the numbered-list
interaction and `ui.print_panel()` for confirmation/error feedback.

---

### 4. `ui.py` — Rendering helpers

All Rich / prompt-toolkit rendering goes here.  No business logic.

#### 4a. `print_panel(console, content, *, border_style="dim", **panel_kwargs) -> None`

Wraps the recurring pattern:
```python
console.print()
console.print(Panel(content, border_style=border_style, padding=(0, 1), expand=False, **panel_kwargs))
console.print()
```

Every current occurrence of that 3-line sandwich is replaced by a single call.

#### 4b. `print_rule(console, label, *, align="center", style="dim", characters="═") -> None`

Wraps `console.print()` + `Rule(...)` + `console.print()`.
Used for the "new conversation" divider and the "You" / "Assistant" headers.

Overloads or separate helpers for the user/assistant headers are fine:
```python
def print_user_header(console): ...
def print_assistant_header(console): ...
```

#### 4c. `prompt_selection(console, title, items, *, prompt_text="Select an item number (empty to cancel): ") -> int | None`

Generic numbered-list picker.  Shows a title, prints items with 1-based
indices, prompts for a number, validates, returns the 1-based index or
`None` on cancel.

This replaces the ad-hoc loops in `_switch_model` and `_copy_content`.

#### 4d. `stream_response(console, model, messages, *, render=True, system_instruction=None) -> str`

Move from current `_stream_response`.  Handles the `Rich.Live` streaming
rendering.  Returns the full response text.

#### 4e. `print_welcome(console, config) -> None`

The welcome banner currently at the top of `run()`.

---

### 5. `errors.py` — Error recovery

Move these functions here:
- `handle_error(exc, config, messages, console) -> None` (the dispatcher)
- `_handle_auth_error(exc, config, console) -> None`
- `_handle_import_error(exc, config, console) -> None`

Key changes:
- `_handle_import_error` should call `commands.model.run()` instead of
  duplicating the switch-model-and-confirm logic.
- All `Panel(...)` calls become `ui.print_panel(...)`.
- The `messages.pop()` that currently lives inside `_handle_error` should be
  **moved out to `repl.py`** — error handlers should not silently mutate the
  conversation history.  The REPL owns that responsibility.

---

### 6. `repl.py` — Main REPL loop (formerly `tui.py`)

This is the thin orchestrator.  It imports from all other modules and wires
them together.

```python
from lmti.commands import build_key_bindings, build_completer, dispatch, resolve_command, LoopSignal
from lmti.errors import handle_error
from lmti import ui
```

#### `run(config: Config) -> None`

Pseudocode:

```python
def run(config):
    console = Console(force_terminal=True)
    messages = []

    kb_state = {"action": None}
    kb = build_key_bindings(kb_state)
    completer = build_completer()
    style = Style.from_dict({"prompt": "ansigreen"})
    session = PromptSession(key_bindings=kb, completer=completer, style=style)

    ui.print_welcome(console, config)

    while True:
        kb_state["action"] = None

        try:
            user_input = session.prompt([("class:prompt", "❯ ")])
        except (EOFError, KeyboardInterrupt):
            break

        text = user_input.strip()
        command = resolve_command(kb_state["action"], text)

        if command:
            signal = dispatch(command, config, messages, console)
            if signal is LoopSignal.BREAK:
                break
            if signal is LoopSignal.CONTINUE:
                continue

        if not text:
            continue

        # Send message
        messages.append(UserMessage(content=text))
        ui.print_user_header(console)
        console.print(Markdown(text) if config.settings.render_markdown else text)
        ui.print_assistant_header(console)

        try:
            response = ui.stream_response(
                console, config.settings.model, messages,
                render=config.settings.render_markdown,
                system_instruction=config.settings.system_instruction,
            )
            messages.append(AssistantMessage(content=response))
            console.print()
        except Exception as exc:
            messages.pop()  # remove the failed user message
            handle_error(exc, config, console)
```

---

### 7. `cli.py` — Update import

```python
# Before
from lmti.tui import run

# After
from lmti.repl import run
```

---

## Migration checklist

Implement in this order to keep things working at each step:

- [x] **Step 1 — Create `ui.py`**
  - Move/create: `print_panel`, `print_rule`, `print_user_header`,
    `print_assistant_header`, `prompt_selection`, `stream_response`,
    `print_welcome`.
  - Do NOT update callers yet.  Just create the module and make sure it's
    importable.

- [x] **Step 2 — Create `errors.py`**
  - Move `_handle_auth_error`, `_handle_import_error`, `_handle_error`.
  - Replace internal `Panel(...)` calls with `ui.print_panel()`.
  - Remove the `messages.pop()` from `handle_error` (caller will handle it).

- [x] **Step 3 — Create `commands/` package**
  - Create `commands/__init__.py` with `CommandDef`, `COMMANDS`, `LoopSignal`,
    `build_key_bindings`, `build_completer`, `resolve_command`, `dispatch`.
  - Create `commands/copy.py` — move clipboard + copy logic.
  - Create `commands/model.py` — move model-switch logic.
  - Wire `dispatch()` to call `commands.copy.run` / `commands.model.run` and
    handle trivial commands inline.

- [x] **Step 4 — Create `repl.py`**
  - Write the slim REPL loop that imports from `commands`, `ui`, `errors`.
  - The `_send_message` function is absorbed into the loop body (it's only
    called once and is straightforward).

- [x] **Step 5 — Update `cli.py`**
  - Change `from lmti.tui import run` → `from lmti.repl import run`.

- [x] **Step 6 — Delete `tui.py`**
  - Remove the old file.

- [x] **Step 7 — Verify**
  - Run `just format` and `just check-types`.
  - Manual smoke test: start the app, send a message, try each command and
    keybinding, test error paths (wrong API key, missing provider).
