from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = "الحسابات"

    def ready(self):
        # ربط الإشارات (auto-assign groups based on role)
        from . import signals  # noqa: F401