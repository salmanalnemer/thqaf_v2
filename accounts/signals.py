from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group

from .models import User, Role

logger = logging.getLogger(__name__)


ROLE_GROUP_NAMES = {r.value for r in Role}


@receiver(post_save, sender=User)
def sync_role_group(sender, instance: User, created: bool, **kwargs):
    """مزامنة مجموعة (Group) الدور مع حقل role.

    - نضيف المستخدم إلى مجموعة تحمل اسم role (مثل: SYSTEM_ADMIN)
    - نزيله من مجموعات الأدوار الأخرى فقط (ولا نمس المجموعات المخصصة الأخرى)

    هذا يسمح لاحقًا لمدير النظام بضبط صلاحيات كل مجموعة من لوحة Django Admin
    (أو أي واجهة إدارة نضيفها لاحقًا).
    """
    try:
        role_name = instance.role
        if not role_name:
            return

        # Ensure role group exists (safe in concurrent creates)
        role_group, _ = Group.objects.get_or_create(name=role_name)

        # Remove from other role groups
        other_role_groups = Group.objects.filter(name__in=(ROLE_GROUP_NAMES - {role_name}))
        instance.groups.remove(*other_role_groups)

        # Add to the correct role group
        instance.groups.add(role_group)

    except Exception:
        # لا نكسر عملية الحفظ بسبب خطأ في مزامنة المجموعات
        logger.exception("Failed to sync role group for user_id=%s", instance.pk)
