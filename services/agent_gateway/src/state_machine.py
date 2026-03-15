from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ConversationStage(str, Enum):
    GREETING = "GREETING"
    INTENT_DETECTION = "INTENT_DETECTION"
    ANSWER_QUESTION = "ANSWER_QUESTION"
    COLLECT_NAME = "COLLECT_NAME"
    COLLECT_PHONE = "COLLECT_PHONE"
    COLLECT_TIME = "COLLECT_TIME"
    CONFIRM_DETAILS = "CONFIRM_DETAILS"
    BOOK_CALLBACK = "BOOK_CALLBACK"
    END = "END"


@dataclass
class SessionState:
    session_id: str
    stage: ConversationStage = ConversationStage.GREETING
    name: str | None = None
    phone: str | None = None
    requested_time: str | None = None
    history: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "name": self.name,
            "phone": self.phone,
            "requested_time": self.requested_time,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SessionState:
        raw_history = payload.get("history")
        history: list[dict[str, str]]
        if isinstance(raw_history, list):
            history = [item for item in raw_history if isinstance(item, dict)]
        else:
            history = []

        stage_value = payload.get("stage")
        stage = ConversationStage.GREETING
        if isinstance(stage_value, str):
            try:
                stage = ConversationStage(stage_value)
            except ValueError:
                stage = ConversationStage.GREETING

        return cls(
            session_id=str(payload.get("session_id", "")),
            stage=stage,
            name=payload.get("name") if isinstance(payload.get("name"), str) else None,
            phone=payload.get("phone") if isinstance(payload.get("phone"), str) else None,
            requested_time=(
                payload.get("requested_time")
                if isinstance(payload.get("requested_time"), str)
                else None
            ),
            history=history,
        )


class SessionStore(Protocol):
    def load(self, session_id: str) -> SessionState | None: ...

    def save(self, state: SessionState) -> None: ...

    def get_or_create(self, session_id: str) -> SessionState: ...


class RedisSessionStore:
    def __init__(
        self,
        redis_url: str,
        key_prefix: str = "agent_gateway:session:",
        ttl_seconds: int = 60 * 60 * 12,
    ) -> None:
        try:
            from redis import Redis
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "redis package is required for RedisSessionStore. Install dependencies from "
                "services/agent_gateway/requirements.txt."
            ) from exc
        self._client: Any = Redis.from_url(redis_url, decode_responses=True)
        self._prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def ping(self) -> bool:
        return bool(self._client.ping())

    def _key(self, session_id: str) -> str:
        return f"{self._prefix}{session_id}"

    def load(self, session_id: str) -> SessionState | None:
        payload = self._client.get(self._key(session_id))
        if payload is None:
            return None
        return SessionState.from_dict(json.loads(payload))

    def save(self, state: SessionState) -> None:
        self._client.setex(
            self._key(state.session_id),
            self._ttl_seconds,
            json.dumps(state.to_dict()),
        )

    def get_or_create(self, session_id: str) -> SessionState:
        existing = self.load(session_id)
        if existing is not None:
            return existing
        created = SessionState(session_id=session_id)
        self.save(created)
        return created


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def load(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def save(self, state: SessionState) -> None:
        self._sessions[state.session_id] = state

    def get_or_create(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.strip().split())


def _extract_name(text: str) -> str | None:
    normalized = _normalize_whitespace(text)
    if not normalized:
        return None
    match = re.search(r"\bmy name is ([A-Za-z][A-Za-z' -]{1,60})", normalized, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip(" .,!?:;")
    # Fallback: use the full utterance when no explicit marker is present.
    return normalized.strip(" .,!?:;")


def _extract_phone(text: str) -> str | None:
    digits = re.sub(r"\D", "", text)
    if len(digits) < 10:
        return None
    return digits[-10:]


def _extract_time(text: str) -> str | None:
    normalized = _normalize_whitespace(text)
    if not normalized:
        return None
    if re.search(r"\b(today|tomorrow|morning|afternoon|evening)\b", normalized, flags=re.IGNORECASE):
        return normalized
    if re.search(r"\b\d{1,2}(:\d{2})?\s?(am|pm)\b", normalized, flags=re.IGNORECASE):
        return normalized
    return None


def _wants_callback(text: str) -> bool:
    lowered = text.lower()
    phrases = (
        "call me",
        "call back",
        "callback",
        "book",
        "schedule",
        "appointment",
    )
    return any(phrase in lowered for phrase in phrases)


def _is_affirmative(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("yes", "correct", "sounds good", "confirm"))


def _is_negative(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("no", "incorrect", "change", "wrong"))


def _wants_to_end(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("bye", "goodbye", "that's all", "nothing else"))


class ConversationStateMachine:
    def __init__(self, store: SessionStore) -> None:
        self._store = store

    def handle_turn(self, session_id: str, user_text: str) -> SessionState:
        state = self._store.get_or_create(session_id)
        updated = self.advance_state(state, user_text)
        self._store.save(updated)
        return updated

    def advance_state(self, state: SessionState, user_text: str) -> SessionState:
        text = _normalize_whitespace(user_text)
        state.history.append({"role": "user", "content": text})

        if state.stage == ConversationStage.END:
            return state

        if _wants_to_end(text):
            state.stage = ConversationStage.END
            return state

        if state.stage == ConversationStage.GREETING:
            state.stage = ConversationStage.INTENT_DETECTION
            return state

        if state.stage == ConversationStage.INTENT_DETECTION:
            if _wants_callback(text):
                state.stage = ConversationStage.COLLECT_NAME
            else:
                state.stage = ConversationStage.ANSWER_QUESTION
            return state

        if state.stage == ConversationStage.ANSWER_QUESTION:
            if _wants_callback(text):
                state.stage = ConversationStage.COLLECT_NAME
            return state

        if state.stage == ConversationStage.COLLECT_NAME:
            extracted = _extract_name(text)
            if extracted:
                state.name = extracted
                state.stage = ConversationStage.COLLECT_PHONE
            return state

        if state.stage == ConversationStage.COLLECT_PHONE:
            extracted = _extract_phone(text)
            if extracted:
                state.phone = extracted
                state.stage = ConversationStage.COLLECT_TIME
            return state

        if state.stage == ConversationStage.COLLECT_TIME:
            extracted = _extract_time(text)
            if extracted:
                state.requested_time = extracted
                state.stage = ConversationStage.CONFIRM_DETAILS
            return state

        if state.stage == ConversationStage.CONFIRM_DETAILS:
            if _is_affirmative(text):
                state.stage = ConversationStage.BOOK_CALLBACK
            elif _is_negative(text):
                state.name = None
                state.phone = None
                state.requested_time = None
                state.stage = ConversationStage.COLLECT_NAME
            return state

        if state.stage == ConversationStage.BOOK_CALLBACK:
            state.stage = ConversationStage.END
            return state

        return state
