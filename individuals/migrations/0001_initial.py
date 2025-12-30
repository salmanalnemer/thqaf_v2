from __future__ import annotations

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0002_emailotp_alter_user_date_joined_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="IndividualProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "id_number",
                    models.CharField(max_length=20, unique=True, verbose_name="الهوية الوطنية / الإقامة"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="individual_profile",
                        to="accounts.user",
                        verbose_name="المستخدم",
                    ),
                ),
            ],
            options={
                "verbose_name": "ملف فرد",
                "verbose_name_plural": "ملفات الأفراد",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="individualprofile",
            index=models.Index(fields=["id_number"], name="individuals_id_number_idx"),
        ),
    ]
