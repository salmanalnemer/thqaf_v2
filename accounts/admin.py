from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, EmailOTP


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "role", "user_type", "is_active", "is_staff")
    list_filter = ("role", "user_type", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("البيانات", {"fields": ("full_name", "phone", "role", "user_type")}),
        ("الصلاحيات", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تواريخ", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "phone", "role", "user_type", "password1", "password2", "is_active", "is_staff"),
        }),
    )


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("user__email", "user__phone", "code")
