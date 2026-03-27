# Language Model Terminal Interface

Oftentimes I just want to talk to LMs, without the agentic clutter: I dont want it to read my stuff, access my files or consume through a gazillion tokens of tools, skills, MCPs and what not. I just want a recipe for tika masala, c'mon :(

For that I normally have to log into the webapps from the provider (i.e. Mistral LeChat, Gemini, ChatGPT). But I live on the terminal. So I made a thin wrapper bc it is 2026 and programming is easy

FAQ:
- **Can I talk with LMs from different providers from the terminal?** Yes :)
- **Does the app have access to my files?** No
- **Can the app run terminal commands?** Nope
- Can the app execute code? Nein
- Does the app have any sort of agentic loop? Negative
- Can I connect the app to MCPs or other tools? Also no

## Install
`uv tool install lmti`

## Usage
```bash
# Start with the default model
lmti

# Start with a specific model
lmti -m vertex:gemini-2.5-flash
```

<details>
<summary>Configuration</summary>

Config is stored at `~/.config/lmti/config.yaml`. It handles your credentials and default settings:

```yaml
credentials:
  MISTRAL_API_KEY: your-key-here
settings:
  render_markdown: true
  model: mistral:mistral-small-2603
models:
- mistral:mistral-small-2603
- vertex:gemini-2.5-flash
```
</details>

## Development

### Structure
```text
src/lmti/
├── cli.py      # Argument parsing and entry point
├── config.py   # Configuration loading and persistence
├── tui.py      # Terminal UI implementation (prompt-toolkit)
└── __init__.py
```

### Tooling
We use `just` for development tasks. Use:
- `just sync`: Updates lockfile and syncs environment.
- `just format`: Lints and formats with `ruff`.
- `just check-types`: Static analysis with `ty`.
- `just analyze-complexity`: Cyclomatic complexity checks with `complexipy`.
- `just test`: Runs pytest with 90% coverage threshold.

### Contribute
1. **Hooks**: Install pre-commit hooks via `just install-hooks`.
2. **Issues**: Open an issue first using the default template.
3. **PRs**: Link your PR to the relevant issue.

## License
MIT
