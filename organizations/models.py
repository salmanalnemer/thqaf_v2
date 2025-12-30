from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


phone_validator = RegexValidator(
    regex=r"^\d{10}$",
    message="رقم الجوال يجب أن يكون 10 أرقام فقط.",
)


class OrganizationCategory(models.TextChoices):
    GOVERNMENT = "GOV", "جهة حكومية"
    BUSINESS = "BUS", "قطاع الأعمال"
    ASSOCIATION = "ASSOC", "جمعيات"
    SCHOOLS = "SCHOOLS", "مدارس"
    UNIVERSITIES = "UNIV", "جامعات"


class OrganizationProfile(models.Model):
    """بيانات إضافية لحسابات الجهات."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_profile",
        verbose_name="المستخدم",
    )

    category = models.CharField(
        "تصنيف الجهة",
        max_length=20,
        choices=OrganizationCategory.choices,
        db_index=True,
    )

    # منع تكرار اسم الجهة على مستوى قاعدة البيانات
    org_name = models.CharField("اسم الجهة", max_length=255, unique=True)

    representative_name = models.CharField("اسم ممثل الجهة", max_length=200)
    representative_phone = models.CharField(
        "رقم جوال ممثل الجهة",
        max_length=10,
        validators=[phone_validator],
        help_text="10 أرقام فقط بدون +966",
    )

    # موقع الجهة
    map_url = models.URLField("رابط موقع الجهة عبر الخريطة", blank=True)
    location_description = models.TextField("وصف المعلم/الموقع", blank=True)
    latitude = models.DecimalField(
        "خط العرض", max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        "خط الطول", max_digits=9, decimal_places=6, null=True, blank=True
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)

    class Meta:
        verbose_name = "ملف جهة"
        verbose_name_plural = "ملفات الجهات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["org_name"]),
        ]
        constraints = [
            # شرط: لازم واحد على الأقل من (map_url أو location_description أو (latitude+longitude))
            # (ملاحظة: في إصدار Django عندك نستخدم condition بدل check)
            models.CheckConstraint(
                name="org_location_at_least_one",
                condition=(
                    Q(map_url__gt="")
                    | Q(location_description__gt="")
                    | (Q(latitude__isnull=False) & Q(longitude__isnull=False))
                ),
            )
        ]

    def clean(self):
        """تحقق إضافي ليعمل حتى من لوحة الإدارة."""
        errors = {}

        # تطبيع النصوص
        if self.org_name:
            self.org_name = self.org_name.strip()
        if self.representative_name:
            self.representative_name = self.representative_name.strip()
        if self.map_url is not None:
            self.map_url = (self.map_url or "").strip()
        if self.location_description is not None:
            self.location_description = (self.location_description or "").strip()

        # إلزام معلومة موقع واحدة على الأقل
        has_coords = (self.latitude is not None and self.longitude is not None)
        if not self.map_url and not self.location_description and not has_coords:
            msg = "يرجى إدخال رابط الخريطة أو وصف الموقع أو الإحداثيات."
            errors["map_url"] = msg
            errors["location_description"] = msg

        # إما كلاهما معًا أو فارغين
        if (self.latitude is None) ^ (self.longitude is None):
            msg = "يرجى إدخال خط العرض وخط الطول معًا أو تركهما فارغين."
            errors["latitude"] = msg
            errors["longitude"] = msg

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # تطبيق clean() قبل الحفظ لضمان صحة البيانات من أي مدخل
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.org_name} ({self.user.email})"
