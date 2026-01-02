from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q


id_number_validator = RegexValidator(
    regex=r"^\d{10,20}$",
    message="رقم الهوية/الإقامة يجب أن يكون أرقام فقط (10 إلى 20 رقم).",
)


class IndividualProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="individual_profile",
        verbose_name="المستخدم",
    )

    id_number = models.CharField(
        "الهوية الوطنية / الإقامة",
        max_length=20,
        unique=True,
        validators=[id_number_validator],
    )

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)

    class Meta:
        verbose_name = "ملف فرد"
        verbose_name_plural = "ملفات الأفراد"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["id_number"])]
        constraints = [
            # منع القيم الفارغة (احتياطي قوي على مستوى DB)
            # (ملاحظة: في إصدار Django عندك نستخدم condition بدل check)
            models.CheckConstraint(
                name="individual_id_number_not_blank",
                condition=~Q(id_number=""),
            )
        ]

    def clean(self):
        # تطبيع
        if self.id_number is not None:
            self.id_number = (self.id_number or "").strip()

        # حماية إضافية ضد المسافات فقط
        if not self.id_number:
            raise ValidationError({"id_number": "رقم الهوية/الإقامة مطلوب."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.user.email} ({self.id_number})"
