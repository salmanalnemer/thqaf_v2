from __future__ import annotations

from django.test import TestCase
from django.contrib.auth.models import Group
from django.core.management import call_command

from .models import User, Role, UserType
from .forms import IndividualSignupForm


class RoleAndSignupTests(TestCase):
    def test_individual_signup_creates_inactive_user_with_role(self):
        form = IndividualSignupForm(
            data={
                "email": "test@example.com",
                "full_name": "Test User",
                "phone": "0500000000",
                "password1": "Str0ngPass!234",
                "password2": "Str0ngPass!234",
            }
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.role, Role.IND)
        self.assertEqual(user.user_type, UserType.IND)
        self.assertFalse(user.is_active)

    def test_role_sync_sets_user_type_and_is_staff(self):
        u = User.objects.create_user(
            email="m@example.com",
            password="Str0ngPass!234",
            role=Role.DEPT_MANAGER,
            is_active=True,
        )
        u.refresh_from_db()
        self.assertEqual(u.user_type, UserType.STAFF)
        self.assertFalse(u.is_staff)

        s = User.objects.create_user(
            email="a@example.com",
            password="Str0ngPass!234",
            role=Role.SYSTEM_ADMIN,
            is_active=True,
        )
        s.refresh_from_db()
        self.assertEqual(s.user_type, UserType.STAFF)
        self.assertTrue(s.is_staff)

    def test_bootstrap_roles_creates_groups(self):
        call_command("bootstrap_roles")
        for role in Role.values:
            self.assertTrue(Group.objects.filter(name=role).exists())
