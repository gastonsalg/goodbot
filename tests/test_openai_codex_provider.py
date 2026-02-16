from types import SimpleNamespace

import pytest

from nanobot.providers.openai_codex_provider import OpenAICodexProvider


@pytest.mark.asyncio
async def test_openai_codex_provider_does_not_retry_with_verify_false(monkeypatch) -> None:
    provider = OpenAICodexProvider()
    calls: list[bool] = []

    async def fake_to_thread(fn, *args, **kwargs):
        return SimpleNamespace(account_id="acct-1", access="token-1")

    async def fake_request_codex(url, headers, body, verify):
        calls.append(verify)
        raise RuntimeError("CERTIFICATE_VERIFY_FAILED")

    monkeypatch.setattr("nanobot.providers.openai_codex_provider.asyncio.to_thread", fake_to_thread)
    monkeypatch.setattr("nanobot.providers.openai_codex_provider._request_codex", fake_request_codex)

    result = await provider.chat([{"role": "user", "content": "hi"}])

    assert calls == [True]
    assert result.finish_reason == "error"
    assert result.content is not None
    assert "CERTIFICATE_VERIFY_FAILED" in result.content

