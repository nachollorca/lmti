# lmsh

Language Models, from the terminal.

## Install

```bash
uv tool install lmsh
```

## Usage

```bash
# Start with the default model (mistral:mistral-small-2603)
lmsh

# Start with a specific model
lmsh -m vertex:gemini-2.5-flash
```

### Commands

| Command  | Shortcut | Description               |
|----------|----------|---------------------------|
| `/exit`  | Ctrl+Q   | Exit the application      |
| `/new`   | Ctrl+N   | Reset the conversation    |
| `/model` | Ctrl+O   | Switch to a different model |
