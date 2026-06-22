from django.db import models
from django.contrib.postgres.indexes import GinIndex


class ConversationSession(models.Model):
    """Stores conversation state and handoff tracking."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ESCALATED = "escalated", "Escalated"

    class FlowType(models.TextChoices):
        NONE = "none", "None"
        BOOKING = "booking", "Booking"
        RESCHEDULE = "reschedule", "Reschedule"
        CANCEL = "cancel", "Cancel"
        FAQ = "faq", "FAQ"

    class EscalationReason(models.TextChoices):
        USER_REQUEST = "user_request", "User Requested"
        AI_CONFIDENCE = "ai_confidence", "AI Confidence Low"
        ERROR = "error", "System Error"
        OUT_OF_HOURS = "out_of_hours", "Out of Business Hours"
        COMPLEX_REQUEST = "complex_request", "Complex Request"

    phone = models.CharField(max_length=20, db_index=True)
    session_id = models.CharField(max_length=64, unique=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    active_flow = models.CharField(
        max_length=20,
        choices=FlowType.choices,
        default=FlowType.NONE,
    )
    current_step = models.CharField(max_length=50, blank=True)

    collected_data = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    is_escalated = models.BooleanField(default=False)
    escalation_reason = models.CharField(
        max_length=20,
        choices=EscalationReason.choices,
        blank=True,
    )
    escalation_context = models.JSONField(default=dict, blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone", "status"]),
            models.Index(fields=["expires_at"]),
            GinIndex(fields=["collected_data"], name="collected_data_gin"),
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Session {self.phone} - {self.active_flow}"
