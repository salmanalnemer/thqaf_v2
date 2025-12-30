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
            name="OrganizationProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "category",
                    models.CharField(choices=[
                        ("GOV", "جهة حكومية"),
                        ("BUS", "قطاع الأعمال"),
                        ("ASSOC", "جمعيات"),
                        ("SCHOOLS", "مدارس"),
                        ("UNIV", "جامعات"),
                    ], db_index=True, max_length=20, verbose_name="تصنيف الجهة"),
                ),
                ("org_name", models.CharField(max_length=255, verbose_name="اسم الجهة")),
                ("representative_name", models.CharField(max_length=200, verbose_name="اسم ممثل الجهة")),
                (
                    "representative_phone",
                    models.CharField(help_text="10 أرقام فقط بدون +966", max_length=10, verbose_name="رقم جوال ممثل الجهة"),
                ),
                ("map_url", models.URLField(blank=True, verbose_name="رابط موقع الجهة عبر الخريطة")),
                ("location_description", models.TextField(blank=True, verbose_name="وصف المعلم/الموقع")),
                ("latitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="خط العرض")),
                ("longitude", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="خط الطول")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organization_profile",
                        to="accounts.user",
                        verbose_name="المستخدم",
                    ),
                ),
            ],
            options={
                "verbose_name": "ملف جهة",
                "verbose_name_plural": "ملفات الجهات",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="organizationprofile",
            index=models.Index(fields=["category"], name="org_category_idx"),
        ),
        migrations.AddIndex(
            model_name="organizationprofile",
            index=models.Index(fields=["org_name"], name="org_name_idx"),
        ),
    ]
