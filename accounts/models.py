from __future__ import annotations

import secrets
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.core.validators import RegexValidator
from django.utils import timezone


class UserType(models.TextChoices):
    ORG = "ORG", "جهة"
    IND = "IND", "فرد"
    TRAINER = "TRAINER", "مدرب"
    STAFF = "STAFF", "موظف"


phone_validator = RegexValidator(
    regex=r"^\d{10}$",
    message="رقم الجوال يجب أن يكون 10 أرقام فقط.",
)


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("البريد الإلكتروني مطلوب.")
        email = self.normalize_email(email).lower().strip()

        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        # افتراضيًا: غير مفعل حتى يتم التحقق عبر OTP (إلا إذا تم تمرير is_active=True صراحةً)
        user.is_active = bool(extra_fields.get("is_active", False))

        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("user_type", UserType.STAFF)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("يجب أن يكون Superuser بقيمة is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("يجب أن يكون Superuser بقيمة is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("البريد الإلكتروني", unique=True)
    full_name = models.CharField("الاسم الكامل", max_length=200, blank=True)

    phone = models.CharField(
        "رقم الجوال",
        max_length=10,
        blank=True,
        validators=[phone_validator],
        help_text="10 أرقام فقط بدون +966",
    )

    user_type = models.CharField(
        "نوع المستخدم",
        max_length=20,
        choices=UserType.choices,
        default=UserType.IND,
        db_index=True,
    )

    is_active = models.BooleanField("مفعل", default=False)
    is_staff = models.BooleanField("موظف إداري", default=False)

    date_joined = models.DateTimeField("تاريخ الانضمام", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["user_type"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self) -> str:
        return self.email


class EmailOTP(models.Model):
    """
    رمز تحقق عبر البريد (OTP)
    - 6 أرقام
    - صلاحية افتراضية 10 دقائق
    - تتبع المحاولات
    """
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="email_otps",
        verbose_name="المستخدم",
    )
    code = models.CharField("رمز التحقق", max_length=6)
    created_at = models.DateTimeField("تاريخ الإنشاء", default=timezone.now)
    expires_at = models.DateTimeField("ينتهي في")
    attempts = models.PositiveSmallIntegerField("عدد المحاولات", default=0)
    is_used = models.BooleanField("تم استخدامه؟", default=False)

    class Meta:
        verbose_name = "رمز تحقق بريد"
        verbose_name_plural = "رموز تحقق البريد"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    @staticmethod
    def generate_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"  # 6 digits

    @classmethod
    def create_for_user(cls, user: "User", ttl_minutes: int = 10) -> "EmailOTP":
        now = timezone.now()
        return cls.objects.create(
            user=user,
            code=cls.generate_code(),
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    def __str__(self) -> str:
        return f"OTP({self.user_id}) used={self.is_used}"
