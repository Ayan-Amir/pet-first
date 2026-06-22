import json

from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta

from .models import ConversationSession


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = [
        "session_id",
        "phone",
        "status",
        "active_flow",
        "current_step",
        "is_escalated",
        "expires_at",
        "last_activity_display",
    ]
    list_filter = [
        "status",
        "active_flow",
        "is_escalated",
        "created_at",
        "escalation_reason",
    ]
    search_fields = ["phone", "session_id"]
    readonly_fields = [
        "session_id",
        "created_at",
        "updated_at",
        "collected_data_display",
    ]

    fieldsets = (
        ("Session Info", {"fields": ("session_id", "phone")}),
        ("Flow State", {"fields": ("status", "active_flow", "current_step")}),
        (
            "Collected Data",
            {"fields": ("collected_data_display",), "classes": ("collapse",)},
        ),
        (
            "Escalation",
            {
                "fields": (
                    "is_escalated",
                    "escalation_reason",
                    "escalation_context",
                    "escalated_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "expires_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Collected Data")
    def collected_data_display(self, obj: ConversationSession) -> str:
        return format_html(
            "<pre>{}</pre>", json.dumps(obj.collected_data or {}, indent=2)
        )

    @admin.display(description="Last Activity")
    def last_activity_display(self, obj: ConversationSession) -> str:
        ago = timezone.now() - obj.updated_at
        if ago < timedelta(minutes=1):
            return "Just now"
        if ago < timedelta(hours=1):
            return f"{ago.seconds // 60}m ago"
        if ago < timedelta(days=1):
            return f"{ago.seconds // 3600}h ago"
        return f"{ago.days}d ago"

    actions = ["mark_escalated", "mark_completed", "extend_session"]

    @admin.action(description="Mark selected sessions as escalated")
    def mark_escalated(self, request, queryset):
        queryset.update(
            is_escalated=True,
            status=ConversationSession.Status.ESCALATED,
            escalation_reason=ConversationSession.EscalationReason.USER_REQUEST,
            escalated_at=timezone.now(),
        )

    @admin.action(description="Mark selected sessions as completed")
    def mark_completed(self, request, queryset):
        queryset.update(status=ConversationSession.Status.COMPLETED)

    @admin.action(description="Extend session by 30 minutes")
    def extend_session(self, request, queryset):
        queryset.update(expires_at=timezone.now() + timedelta(minutes=30))
