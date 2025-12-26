from django.contrib import admin
from .models import ContactMessage, SiteSetting


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("org_name", "org_representative", "email", "phone", "is_sent", "created_at")
    search_fields = ("org_name", "org_representative", "email", "phone")
    list_filter = ("is_sent", "created_at")
    readonly_fields = ("created_at", "is_sent", "send_error")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("contact_inbox_email", "updated_at")

    def has_add_permission(self, request):
        # يمنع إضافة أكثر من سجل (Singleton)
        return not SiteSetting.objects.exists()
