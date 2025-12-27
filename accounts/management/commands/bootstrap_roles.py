from __future__ import annotations

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

from accounts.models import Role


# الصلاحيات الافتراضية لكل دور.
# يمكن لمدير النظام تعديلها لاحقًا من Django Admin (Groups/Permissions).
ROLE_DEFAULT_PERMS: dict[str, set[str]] = {
    Role.SYSTEM_ADMIN: {
        "accounts.manage_users",
        "accounts.view_all_data",
        "accounts.manage_courses",
        "accounts.approve_courses",
    },
    Role.DEPT_MANAGER: {
        "accounts.view_all_data",
        "accounts.manage_courses",
        "accounts.approve_courses",
    },
    Role.SUPERVISOR: {
        "accounts.view_all_data",
        "accounts.manage_courses",
        "accounts.approve_courses",
    },
    Role.COURSE_COORDINATOR: {
        "accounts.manage_courses",
    },
    Role.TRAINER: set(),
    Role.ORG: set(),
    Role.IND: set(),
}


def _get_permission(perm_str: str) -> Permission:
    """Resolve a permission string in the format 'app_label.codename'."""
    app_label, codename = perm_str.split(".", 1)
    return Permission.objects.select_related("content_type").get(
        content_type__app_label=app_label,
        codename=codename,
    )


class Command(BaseCommand):
    help = "إنشاء مجموعات الأدوار الافتراضية وإسناد الصلاحيات الأساسية لها."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="إعادة ضبط صلاحيات مجموعات الأدوار إلى القيم الافتراضية.",
        )

    def handle(self, *args, **options):
        reset = bool(options.get("reset"))

        created_groups = 0
        for role in Role.values:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                created_groups += 1

            desired_perms = ROLE_DEFAULT_PERMS.get(role, set())
            perms = []
            for perm_str in desired_perms:
                try:
                    perms.append(_get_permission(perm_str))
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ لم يتم العثور على الصلاحية {perm_str}. تأكد من تشغيل migrations أولًا."
                        )
                    )

            if reset:
                group.permissions.set(perms)
            else:
                group.permissions.add(*perms)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ تم تجهيز مجموعات الأدوار. Groups created: {created_groups}. (reset={reset})"
            )
        )
