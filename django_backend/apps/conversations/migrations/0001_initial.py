from django.db import migrations, models
import django.contrib.postgres.indexes


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ConversationSession",
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
                ("phone", models.CharField(db_index=True, max_length=20)),
                ("session_id", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("completed", "Completed"),
                            ("escalated", "Escalated"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "active_flow",
                    models.CharField(
                        choices=[
                            ("none", "None"),
                            ("booking", "Booking"),
                            ("reschedule", "Reschedule"),
                            ("cancel", "Cancel"),
                            ("faq", "FAQ"),
                        ],
                        default="none",
                        max_length=20,
                    ),
                ),
                ("current_step", models.CharField(blank=True, max_length=50)),
                ("collected_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField()),
                ("is_escalated", models.BooleanField(default=False)),
                (
                    "escalation_reason",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("user_request", "User Requested"),
                            ("ai_confidence", "AI Confidence Low"),
                            ("error", "System Error"),
                            ("out_of_hours", "Out of Business Hours"),
                            ("complex_request", "Complex Request"),
                        ],
                        max_length=20,
                    ),
                ),
                ("escalation_context", models.JSONField(blank=True, default=dict)),
                ("escalated_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddIndex(
            model_name="conversationsession",
            index=models.Index(fields=["phone", "status"], name="conversatio_phone_8a0b0d_idx"),
        ),
        migrations.AddIndex(
            model_name="conversationsession",
            index=models.Index(fields=["expires_at"], name="conversatio_expires_6d8c8a_idx"),
        ),
        migrations.AddIndex(
            model_name="conversationsession",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["collected_data"], name="collected_data_gin"
            ),
        ),
    ]
