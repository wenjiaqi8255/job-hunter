# Generated by Django 5.2.1 on 2025-05-23 12:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matcher", "0003_savedjob"),
    ]

    operations = [
        migrations.CreateModel(
            name="CoverLetter",
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
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "saved_job",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cover_letter",
                        to="matcher.savedjob",
                    ),
                ),
            ],
        ),
    ]
