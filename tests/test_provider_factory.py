import pytest
import typer

from nanobot.cli.commands import _make_provider
from nanobot.config.schema import Config
from nanobot.providers.codex_cli_provider import CodexCLIProvider
from nanobot.providers.openai_codex_provider import OpenAICodexProvider


def test_make_provider_uses_codex_cli_when_enabled() -> None:
    config = Config()
    config.agents.defaults.model = "openai/gpt-5.3-codex"
    config.providers.openai.use_codex_cli = True
    config.providers.openai.api_key = ""

    provider = _make_provider(config)

    assert isinstance(provider, CodexCLIProvider)


def test_make_provider_requires_api_key_without_codex_cli() -> None:
    config = Config()
    config.agents.defaults.model = "openai/gpt-5.3-codex"
    config.providers.openai.use_codex_cli = False
    config.providers.openai.api_key = ""

    with pytest.raises(typer.Exit):
        _make_provider(config)


def test_make_provider_uses_openai_codex_provider_for_oauth_model() -> None:
    config = Config()
    config.agents.defaults.model = "openai-codex/gpt-5.1-codex"
    config.providers.openai.use_codex_cli = False
    config.providers.openai.api_key = ""

    provider = _make_provider(config)

    assert isinstance(provider, OpenAICodexProvider)
