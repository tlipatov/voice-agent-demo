"""Redis-backed conversation state machine persistence tests."""

from __future__ import annotations

import os
import unittest

try:
    from redis import Redis
    from redis.exceptions import RedisError
except ModuleNotFoundError:  # pragma: no cover - environment-dependent
    Redis = None  # type: ignore[assignment]

    class RedisError(Exception):
        pass

from services.agent_gateway.src.state_machine import (
    ConversationStage,
    ConversationStateMachine,
    RedisSessionStore,
)


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _redis_available(url: str) -> bool:
    if Redis is None:
        return False
    try:
        client = Redis.from_url(url, decode_responses=True)
        return bool(client.ping())
    except RedisError:
        return False


class ConversationStateMachineRedisE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        if Redis is None:
            self.skipTest("redis package is not installed in this environment")
        if not _redis_available(REDIS_URL):
            self.skipTest(f"Redis is not reachable at {REDIS_URL}")
        self.store = RedisSessionStore(REDIS_URL, key_prefix="agent_gateway:test:session:", ttl_seconds=600)
        self.machine = ConversationStateMachine(self.store)
        self.client = Redis.from_url(REDIS_URL, decode_responses=True)

    def tearDown(self) -> None:
        for key in self.client.scan_iter(match="agent_gateway:test:session:*"):
            self.client.delete(key)

    def test_session_state_persists_between_service_requests(self) -> None:
        session_id = "persisted-session"

        state_1 = self.machine.handle_turn(session_id, "Hello")
        self.assertEqual(ConversationStage.INTENT_DETECTION, state_1.stage)

        # Simulate a new request handler process by creating a new machine+store.
        machine_2 = ConversationStateMachine(
            RedisSessionStore(REDIS_URL, key_prefix="agent_gateway:test:session:", ttl_seconds=600)
        )
        state_2 = machine_2.handle_turn(session_id, "Can I get a callback tomorrow?")
        self.assertEqual(ConversationStage.COLLECT_NAME, state_2.stage)
        self.assertEqual(2, len(state_2.history))

        # Ensure persisted payload is visible directly in Redis-backed loading path.
        reloaded = self.store.load(session_id)
        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(ConversationStage.COLLECT_NAME, reloaded.stage)
        self.assertEqual("Can I get a callback tomorrow?", reloaded.history[-1]["content"])


if __name__ == "__main__":
    unittest.main()
