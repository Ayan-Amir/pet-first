from django.contrib import admin

from apps.knowledge.models import KnowledgeEntry
from apps.knowledge.services.rag_service import generate_embedding


@admin.register(KnowledgeEntry)
class KnowledgeEntryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "question_short",
        "category",
        "is_active",
        "created_at",
        "updated_at",
    ]
    list_filter = ["category", "is_active", "created_at"]
    search_fields = ["question", "answer"]
    readonly_fields = ["created_at", "updated_at", "embedding_preview"]
    actions = ["activate_entries", "deactivate_entries"]

    fieldsets = (
        ("Content", {"fields": ("question", "answer", "category")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Vector Embedding",
            {"fields": ("embedding_preview",), "classes": ("collapse",)},
        ),
        (
            "Metadata",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    @admin.display(description="Question")
    def question_short(self, obj: KnowledgeEntry) -> str:
        if len(obj.question) > 50:
            return obj.question[:50] + "..."
        return obj.question

    @admin.display(description="Embedding")
    def embedding_preview(self, obj: KnowledgeEntry) -> str:
        if obj.embedding is not None:
            return f"Vector of {len(obj.embedding)} dimensions (auto-generated)"
        return "Not generated yet"

    def save_model(self, request, obj, form, change):
        if not obj.embedding or (form and "question" in form.changed_data):
            obj.embedding = generate_embedding(obj.question)
        super().save_model(request, obj, form, change)

    @admin.action(description="Activate selected entries")
    def activate_entries(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Deactivate selected entries")
    def deactivate_entries(self, request, queryset):
        queryset.update(is_active=False)
