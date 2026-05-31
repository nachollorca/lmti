"""Tests for lmti.errors."""

from lmdk.errors import APIPermissionError, AuthenticationError

from lmti import errors
from lmti.config import Config


def test_handle_error_generic(console):
    errors.handle_error(RuntimeError("boom"), Config(), console)
    assert "boom" in console.export_text()


def test_handle_error_auth_saves_keys(console, monkeypatch, config_paths, fake_prompt):

    class _StubProvider:
        required_env = ("MISTRAL_API_KEY",)

    monkeypatch.setattr(errors, "load_provider", lambda name: _StubProvider)
    fake_prompt(["secret-value"])

    config = Config()
    exc = AuthenticationError(401, "nope", provider="MistralProvider")
    errors.handle_error(exc, config, console)
    assert config.credentials["MISTRAL_API_KEY"] == "secret-value"
    assert "saved" in console.export_text().lower()


def test_handle_error_auth_string_required_env(console, monkeypatch, config_paths, fake_prompt):

    class _StubProvider:
        required_env = "ONE_KEY"

    monkeypatch.setattr(errors, "load_provider", lambda name: _StubProvider)
    fake_prompt([""])  # user skips entering the key

    config = Config()
    exc = APIPermissionError(403, "denied", provider="MistralProvider")
    errors.handle_error(exc, config, console)
    assert "ONE_KEY" not in config.credentials


def test_handle_error_import_error_calls_model(console, monkeypatch):
    called = []

    def spy(cons, cfg):
        called.append((cons, cfg))

    monkeypatch.setattr("lmti.commands.model.handle_model", spy)
    config = Config()
    errors.handle_error(ImportError("No module named 'lmdk.providers.vertex'"), config, console)
    assert called and called[0] == (console, config)
    assert "Vertex" in console.export_text()


def test_handle_error_import_error_unmatched(console, monkeypatch):
    # ImportError that doesn't match the provider regex falls through to generic.
    errors.handle_error(ImportError("something else"), Config(), console)
    assert "something else" in console.export_text()
