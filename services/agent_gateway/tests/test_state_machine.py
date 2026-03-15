from __future__ import annotations

import unittest

from services.agent_gateway.src.state_machine import (
    ConversationStage,
    ConversationStateMachine,
    InMemorySessionStore,
)


class ConversationStateMachineTests(unittest.TestCase):
    def test_question_flow_transitions_to_answer_stage(self) -> None:
        machine = ConversationStateMachine(InMemorySessionStore())
        session_id = "session-question"

        first = machine.handle_turn(session_id, "Hello there")
        first_stage = first.stage
        second = machine.handle_turn(session_id, "What are your opening hours?")

        self.assertEqual(ConversationStage.INTENT_DETECTION, first_stage)
        self.assertEqual(ConversationStage.ANSWER_QUESTION, second.stage)
        self.assertEqual(2, len(second.history))

    def test_callback_booking_flow_reaches_end_with_captured_details(self) -> None:
        machine = ConversationStateMachine(InMemorySessionStore())
        session_id = "session-booking"

        machine.handle_turn(session_id, "Hi")
        state = machine.handle_turn(session_id, "Can someone call me tomorrow morning?")
        self.assertEqual(ConversationStage.COLLECT_NAME, state.stage)

        state = machine.handle_turn(session_id, "My name is Alice Johnson")
        self.assertEqual(ConversationStage.COLLECT_PHONE, state.stage)
        self.assertEqual("Alice Johnson", state.name)

        state = machine.handle_turn(session_id, "(415) 555-1234")
        self.assertEqual(ConversationStage.COLLECT_TIME, state.stage)
        self.assertEqual("4155551234", state.phone)

        state = machine.handle_turn(session_id, "Tomorrow at 2pm")
        self.assertEqual(ConversationStage.CONFIRM_DETAILS, state.stage)
        self.assertEqual("Tomorrow at 2pm", state.requested_time)

        state = machine.handle_turn(session_id, "Yes, that is correct")
        self.assertEqual(ConversationStage.BOOK_CALLBACK, state.stage)

        state = machine.handle_turn(session_id, "Thanks")
        self.assertEqual(ConversationStage.END, state.stage)

    def test_negative_confirmation_restarts_collection(self) -> None:
        machine = ConversationStateMachine(InMemorySessionStore())
        session_id = "session-negative"

        machine.handle_turn(session_id, "hello")
        machine.handle_turn(session_id, "Please call me back")
        machine.handle_turn(session_id, "My name is Bob")
        machine.handle_turn(session_id, "650-555-0100")
        machine.handle_turn(session_id, "Tomorrow morning")

        state = machine.handle_turn(session_id, "No, that is wrong")
        self.assertEqual(ConversationStage.COLLECT_NAME, state.stage)
        self.assertIsNone(state.name)
        self.assertIsNone(state.phone)
        self.assertIsNone(state.requested_time)


if __name__ == "__main__":
    unittest.main()
