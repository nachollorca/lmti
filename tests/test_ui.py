"""Tests for lmti.ui."""

from lmti import ui
from lmti.config import Config


def test_print_panel(console):
    ui.print_panel(console, "hello world")
    assert "hello world" in console.export_text()


def test_print_header_user(console):
    ui.print_header(console, "user")
    assert "You" in console.export_text()


def test_print_header_assistant(console):
    ui.print_header(console, "assistant")
    assert "Assistant" in console.export_text()


def test_print_welcome(console):
    ui.print_welcome(console, Config())
    text = console.export_text()
    assert "/exit" in text
    assert "Alt+Enter" in text


def test_prompt_selection_valid_index(console, fake_prompt):
    fake_prompt(["2"])
    assert ui.prompt_selection(console, "pick", ["a", "b", "c"]) == 2


def test_prompt_selection_cancel(console, fake_prompt):
    fake_prompt([""])
    assert ui.prompt_selection(console, "pick", ["a"]) is None


def test_prompt_selection_extra_option(console, fake_prompt):
    fake_prompt(["3"])
    result = ui.prompt_selection(console, "pick", ["a", "b"], extra_option="other")
    assert result == "other"


def test_prompt_selection_invalid_then_valid(console, fake_prompt):
    fake_prompt(["abc", "99", "1"])
    assert ui.prompt_selection(console, "pick", ["only"]) == 1
    assert "Invalid choice" in console.export_text()


def test_prompt_system_instruction_set(console, fake_prompt):
    fake_prompt(["be brief"])
    assert ui.prompt_system_instruction(console, Config()) == "be brief"


def test_prompt_system_instruction_clear(console, fake_prompt):
    fake_prompt([""])
    config = Config()
    config.settings.system_instruction = "old"
    assert ui.prompt_system_instruction(console, config) is None
    assert "old" in console.export_text()


def test_stream_response_concatenates_tokens(console, monkeypatch):
    def fake_complete(model, prompt, stream, system_instruction):
        assert stream is True
        return iter(["alpha", "-", "beta"])

    monkeypatch.setattr("lmti.ui.complete", fake_complete)
    out = ui.stream_response(console=console, model="x:y", messages=[], render=False)
    assert out == "alpha-beta"


def test_stream_response_with_markdown(console, monkeypatch):
    monkeypatch.setattr("lmti.ui.complete", lambda **kw: iter(["**hi**"]))
    out = ui.stream_response(
        console=console, model="x:y", messages=[], render=True, system_instruction="sys"
    )
    assert out == "**hi**"
