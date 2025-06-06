# Generated by Django 5.2.1 on 2025-05-21 15:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matcher", "0002_matchsession_matchedjob"),
    ]

    operations = [
        migrations.CreateModel(
            name="SavedJob",
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
                ("user_session_key", models.CharField(db_index=True, max_length=40)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("not_applied", "Not Applied"),
                            ("interested", "Interested/Saved"),
                            ("applied", "Applied"),
                            ("interviewing", "Interviewing"),
                            ("offer_received", "Offer Received"),
                            ("rejected", "Rejected"),
                            ("accepted", "Accepted"),
                        ],
                        default="interested",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "job_listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saved_instances",
                        to="matcher.joblisting",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
                "unique_together": {("job_listing", "user_session_key")},
            },
        ),
    ]
