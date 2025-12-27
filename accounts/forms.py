from __future__ import annotations

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User, Role, RESTRICTED_SELF_SIGNUP_ROLES


class BaseSignupForm(forms.Form):
    email = forms.EmailField(label="البريد الإلكتروني")
    full_name = forms.CharField(label="الاسم الكامل", max_length=200)
    phone = forms.CharField(label="رقم الجوال", max_length=10, required=False, help_text="10 أرقام بدون +966")
    password1 = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="تأكيد كلمة المرور", widget=forms.PasswordInput)

    role: str = Role.IND  # يحدده كل نموذج فرعي

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد مستخدم مسبقًا.")
        return email

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if phone and (not phone.isdigit() or len(phone) != 10):
            raise ValidationError("رقم الجوال يجب أن يكون 10 أرقام فقط.")
        return phone

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("كلمتا المرور غير متطابقتين.")
        if p1:
            validate_password(p1)
        # منع التسجيل الذاتي للأدوار المقيدة
        if self.role in RESTRICTED_SELF_SIGNUP_ROLES:
            raise ValidationError("لا يمكن إنشاء هذا الدور عبر التسجيل الذاتي. سيتم إنشاؤه من مدير النظام.")
        return cleaned

    def save(self) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password1"],
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            role=self.role,
            is_active=False,
        )
        return user


class IndividualSignupForm(BaseSignupForm):
    role = Role.IND


class OrganizationSignupForm(BaseSignupForm):
    role = Role.ORG


class OTPVerifyForm(forms.Form):
    code = forms.CharField(label="رمز التحقق", max_length=6)

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("رمز التحقق يجب أن يكون 6 أرقام.")
        return code


class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="البريد الإلكتروني")
    password = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get("email") or "").strip().lower()
        password = cleaned.get("password")
        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise ValidationError("بيانات الدخول غير صحيحة.")
            if not user.is_active:
                raise ValidationError("الحساب غير مفعل. يرجى تفعيل الحساب عبر رمز التحقق.")
            cleaned["user"] = user
        return cleaned
