# /undo command implementation

## Summary
Add an `/undo` command that lets the user select a previous **user** message
from the current conversation to go back to. Everything from that message
onward is deleted, and the normal prompt appears so the user can type a
replacement. Selecting the first user message clears the conversation entirely
(same effect as `/new`).

## Steps

### 1. Register the command
In `src/lmti/commands/__init__.py`:
- [x] Add `"undo"` to the `COMMANDS` dict with binding `"escape u"` and handler `"commands.undo"`.
- [x] Add a `"undo"` case in `dispatch()` that calls `handle_undo(console, state)` and returns `LoopSignal.CONTINUE`.

### 2. Create `src/lmti/commands/undo.py`
- [x] Show only **user** messages from `state.messages` as a numbered selection list using `ui.prompt_selection`.
- [x] Format each item as a preview (role + truncated content, same pattern as `/copy`).
- [x] On selection, truncate `state.messages` to everything **before** the selected user message.
- [x] If the result is an empty list (selected the first user message), set `state.conversation_path = None` (behaves like `/new`).
- [x] Otherwise, call `save_conversation(state.messages, state.conversation_path)` to persist the truncated history.
- [x] Print a confirmation panel.

### 3. Verify
- [x] `just format`
- [x] `just check-types`
