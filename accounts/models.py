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


class Role(models.TextChoices):
    """الأدوار التشغيلية داخل المنصة.

    ملاحظة:
    - role هو المرجع الأساسي للصلاحيات.
    - user_type يبقى لتجميع الأنواع (جهة/فرد/مدرب/موظف) وللتوافق الخلفي.
    """

    SYSTEM_ADMIN = "SYSTEM_ADMIN", "مدير النظام"
    DEPT_MANAGER = "DEPT_MANAGER", "مدير الإدارة"
    SUPERVISOR = "SUPERVISOR", "مشرف"
    COURSE_COORDINATOR = "COURSE_COORDINATOR", "منسق الدورات"
    TRAINER = "TRAINER", "مدرب"
    ORG = "ORG", "جهة"
    IND = "IND", "فرد"


ROLE_TO_USER_TYPE = {
    Role.SYSTEM_ADMIN: UserType.STAFF,
    Role.DEPT_MANAGER: UserType.STAFF,
    Role.SUPERVISOR: UserType.STAFF,
    Role.COURSE_COORDINATOR: UserType.STAFF,
    Role.TRAINER: UserType.TRAINER,
    Role.ORG: UserType.ORG,
    Role.IND: UserType.IND,
}


RESTRICTED_SELF_SIGNUP_ROLES = {
    Role.TRAINER,
    Role.DEPT_MANAGER,
    Role.SUPERVISOR,
    Role.COURSE_COORDINATOR,
    Role.SYSTEM_ADMIN,
}


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
        extra_fields.setdefault("role", Role.SYSTEM_ADMIN)
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

    role = models.CharField(
        "الدور",
        max_length=30,
        choices=Role.choices,
        default=Role.IND,
        db_index=True,
        help_text=(
            "يحدد صلاحيات المستخدم داخل النظام. "
            "تنبيه: أدوار (مدرب/مدير إدارة/مشرف/منسق دورات) يتم إنشاؤها من مدير النظام فقط."
        ),
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

        permissions = [
            ("manage_users", "إدارة المستخدمين بالكامل"),
            ("view_all_data", "مشاهدة جميع البيانات في النظام"),
            ("manage_courses", "إدارة الدورات"),
            ("approve_courses", "اعتماد الدورات"),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        """مزامنة user_type و is_staff مع الدور."""
        if self.role:
            self.user_type = ROLE_TO_USER_TYPE.get(self.role, self.user_type)
        # الوصول إلى Django Admin: مقصور على مدير النظام
        if self.role == Role.SYSTEM_ADMIN:
            self.is_staff = True
        elif self.is_superuser:
            # إن وُجدت حالات ترحيل قديمة
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

    # ====== Helpers for role checks ======
    @property
    def is_system_admin(self) -> bool:
        return self.is_superuser or self.role == Role.SYSTEM_ADMIN

    @property
    def is_dept_manager(self) -> bool:
        return self.role == Role.DEPT_MANAGER

    @property
    def is_supervisor(self) -> bool:
        return self.role == Role.SUPERVISOR

    @property
    def is_course_coordinator(self) -> bool:
        return self.role == Role.COURSE_COORDINATOR

    @property
    def is_trainer(self) -> bool:
        return self.role == Role.TRAINER

    @property
    def is_organization(self) -> bool:
        return self.role == Role.ORG

    @property
    def is_individual(self) -> bool:
        return self.role == Role.IND

    # ====== Permission gates (role-first, then Django perms) ======
    def can_manage_users(self) -> bool:
        return self.is_system_admin or self.has_perm("accounts.manage_users")

    def can_view_all_data(self) -> bool:
        if self.is_system_admin:
            return True
        if self.role in {Role.DEPT_MANAGER, Role.SUPERVISOR}:
            return True
        return self.has_perm("accounts.view_all_data")

    def can_manage_courses(self) -> bool:
        if self.is_system_admin:
            return True
        if self.role in {Role.DEPT_MANAGER, Role.SUPERVISOR, Role.COURSE_COORDINATOR}:
            return True
        return self.has_perm("accounts.manage_courses")

    def can_approve_courses(self) -> bool:
        if self.is_system_admin:
            return True
        if self.role in {Role.DEPT_MANAGER, Role.SUPERVISOR}:
            return True
        return self.has_perm("accounts.approve_courses")


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
