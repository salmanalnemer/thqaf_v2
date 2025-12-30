from __future__ import annotations

from django.contrib import admin

from .models import IndividualProfile


@admin.register(IndividualProfile)
class IndividualProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "id_number", "created_at")
    search_fields = ("user__email", "user__full_name", "id_number")
    list_select_related = ("user",)
