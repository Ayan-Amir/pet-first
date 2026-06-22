from django.db import models
from pgvector.django import VectorField


class KnowledgeEntry(models.Model):
    """FAQ knowledge base with vector embeddings for RAG."""

    class Category(models.TextChoices):
        GENERAL = "general", "General"
        SERVICES = "services", "Services"
        PRICING = "pricing", "Pricing"
        BOOKING = "booking", "Booking"
        MOBILE_CLINIC = "mobile_clinic", "Mobile Clinic"
        POLICIES = "policies", "Policies"

    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )

    embedding = VectorField(dimensions=1536, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"[{self.category}] {self.question[:50]}..."
