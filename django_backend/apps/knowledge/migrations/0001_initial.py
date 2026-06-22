from django.db import migrations, models
import pgvector.django.vector


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KnowledgeEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("question", models.TextField()),
                ("answer", models.TextField()),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("general", "General"),
                            ("services", "Services"),
                            ("pricing", "Pricing"),
                            ("booking", "Booking"),
                            ("mobile_clinic", "Mobile Clinic"),
                            ("policies", "Policies"),
                        ],
                        default="general",
                        max_length=20,
                    ),
                ),
                (
                    "embedding",
                    pgvector.django.vector.VectorField(
                        blank=True, dimensions=1536, null=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="knowledgeentry",
            index=models.Index(
                fields=["category", "is_active"], name="knowledge_k_categor_8f3b2a_idx"
            ),
        ),
    ]
