from apps.orchestrator.services.flow_engine import infer_flow_hint
from apps.conversations.models import ConversationSession


def test_infer_flow_booking():
    assert infer_flow_hint("I want to book grooming") == ConversationSession.FlowType.BOOKING


def test_infer_flow_faq():
    assert infer_flow_hint("What are your prices?") == ConversationSession.FlowType.FAQ
