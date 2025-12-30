from __future__ import annotations

from django.contrib import admin

from .models import OrganizationProfile


@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = (
        "org_name",
        "category",
        "representative_name",
        "representative_phone",
        "user",
        "created_at",
    )
    search_fields = (
        "org_name",
        "user__email",
        "representative_name",
        "representative_phone",
    )
    list_filter = ("category",)
    list_select_related = ("user",)