import asyncio
from pathlib import Path

import pytest

from nanobot.agent.loop import AgentLoop
from nanobot.bus.queue import MessageBus


class _DummyProvider:
    def get_default_model(self) -> str:
        return "openai/gpt-4o-mini"

    async def chat(self, **kwargs):  # pragma: no cover - not used in this test
        raise AssertionError("chat should not be called in this test")


@pytest.mark.asyncio
async def test_consolidation_is_single_flight_per_session(monkeypatch, tmp_path: Path) -> None:
    bus = MessageBus()
    agent = AgentLoop(
        bus=bus,
        provider=_DummyProvider(),  # type: ignore[arg-type]
        workspace=tmp_path,
        memory_window=10,
    )

    session = agent.sessions.get_or_create("cli:test")
    for i in range(20):
        session.add_message("user", f"msg-{i}")

    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def fake_consolidate(_session, archive_all: bool = False) -> None:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()

    monkeypatch.setattr(agent, "_consolidate_memory", fake_consolidate)
    monkeypatch.setattr(agent.sessions, "save", lambda _session: None)

    agent._schedule_consolidation(session)
    await asyncio.wait_for(started.wait(), timeout=1.0)

    # Must not create a second in-flight task for the same session.
    agent._schedule_consolidation(session)
    await asyncio.sleep(0)
    assert calls == 1

    release.set()
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert session.key not in agent._consolidation_tasks

