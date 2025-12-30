from __future__ import annotations

from urllib.parse import urlparse

from django import forms
from django.apps import apps
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import RESTRICTED_SELF_SIGNUP_ROLES, Role, User


def _is_https_url(value: str) -> bool:
    try:
        p = urlparse(value)
        return (p.scheme or "").lower() == "https"
    except Exception:
        return False


def _style_input(
    field: forms.Field,
    *,
    placeholder: str | None = None,
    ltr: bool = False,
    inputmode: str | None = None,
    autocomplete: str | None = None,
):
    style = (
        "width:100%;padding:12px 12px;border:1px solid #e4e7ec;"
        "border-radius:14px;outline:none;background:#fff"
    )
    field.widget.attrs.setdefault("style", style)
    if placeholder:
        field.widget.attrs.setdefault("placeholder", placeholder)
    if ltr:
        field.widget.attrs.setdefault("dir", "ltr")
    if inputmode:
        field.widget.attrs.setdefault("inputmode", inputmode)
    if autocomplete:
        field.widget.attrs.setdefault("autocomplete", autocomplete)


class BaseSignupForm(forms.Form):
    """أساس التسجيل الذاتي:
    - يتحقق من البريد
    - يطابق كلمتي المرور
    - يمنع التسجيل الذاتي للأدوار المقيدة
    """

    email = forms.EmailField(label="البريد الإلكتروني")
    password1 = forms.CharField(label="كلمة المرور", widget=forms.PasswordInput)
    password2 = forms.CharField(label="إعادة كلمة المرور", widget=forms.PasswordInput)

    role: str = Role.IND  # يحدده كل نموذج فرعي

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تنسيق رسمي موحد لكل الحقول بدون CSS خارجي
        for name, field in self.fields.items():
            if getattr(field.widget, "input_type", "") == "password":
                _style_input(field, placeholder="••••••••", ltr=True, autocomplete="new-password")
            else:
                _style_input(field)

        _style_input(self.fields["email"], placeholder="name@example.com", ltr=True, inputmode="email", autocomplete="email")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("هذا البريد مستخدم مسبقًا.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")

        if p1 and p2 and p1 != p2:
            raise ValidationError("كلمتا المرور غير متطابقتين.")
        if p1:
            validate_password(p1)

        if self.role in RESTRICTED_SELF_SIGNUP_ROLES:
            raise ValidationError("لا يمكن إنشاء هذا الدور عبر التسجيل الذاتي. سيتم إنشاؤه من مدير النظام.")
        return cleaned

    def save(self) -> User:
        raise NotImplementedError


class IndividualSignupForm(BaseSignupForm):
    role = Role.IND

    full_name = forms.CharField(label="الإسم كاملاً", max_length=200)
    id_number = forms.CharField(label="الهوية الوطنية / الإقامة", max_length=20)
    phone = forms.CharField(label="رقم الجوال", max_length=10, help_text="10 أرقام بدون +966")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _style_input(self.fields["full_name"], placeholder="الاسم الرباعي")
        _style_input(self.fields["id_number"], placeholder="10-20 رقم", ltr=True, inputmode="numeric", autocomplete="off")
        _style_input(self.fields["phone"], placeholder="05xxxxxxxx", ltr=True, inputmode="numeric", autocomplete="tel")

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("رقم الجوال يجب أن يكون 10 أرقام فقط.")
        # منع تكرار رقم الجوال (مهم للدخول بالجوال لاحقًا)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("رقم الجوال مستخدم مسبقًا.")
        return phone

    def clean_id_number(self):
        val = (self.cleaned_data.get("id_number") or "").strip()
        if not val.isdigit() or not (10 <= len(val) <= 20):
            raise ValidationError("رقم الهوية/الإقامة يجب أن يكون أرقام فقط (10 إلى 20 رقم).")

        IndividualProfile = apps.get_model("individuals", "IndividualProfile")
        if IndividualProfile.objects.filter(id_number=val).exists():
            raise ValidationError("هذه الهوية/الإقامة مسجلة مسبقًا.")
        return val

    def save(self) -> User:
        data = self.cleaned_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password1"],
            full_name=data.get("full_name", "").strip(),
            phone=data.get("phone", "").strip(),
            role=self.role,
            is_active=False,
        )
        IndividualProfile = apps.get_model("individuals", "IndividualProfile")
        IndividualProfile.objects.create(user=user, id_number=data["id_number"].strip())
        return user


class OrganizationSignupForm(BaseSignupForm):
    role = Role.ORG

    category = forms.ChoiceField(
        label="تصنيف الجهة",
        choices=(
            ("GOV", "جهة حكومية"),
            ("BUS", "قطاع الأعمال"),
            ("ASSOC", "جمعيات"),
            ("SCHOOLS", "مدارس"),
            ("UNIV", "جامعات"),
        ),
    )
    org_name = forms.CharField(label="إسم الجهة", max_length=255)
    representative_name = forms.CharField(label="إسم ممثل الجهة", max_length=200)
    representative_phone = forms.CharField(
        label="رقم الجوال ممثل الجهة",
        max_length=10,
        help_text="10 أرقام بدون +966",
    )
    map_url = forms.URLField(label="موقع الجهة عبر الخريطة", required=False)
    location_description = forms.CharField(
        label="وصف معلم أو الموقع",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    latitude = forms.DecimalField(label="خط العرض", required=False, max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(label="خط الطول", required=False, max_digits=9, decimal_places=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تحسينات عرض للحقول
        _style_input(self.fields["org_name"], placeholder="مثال: شركة / إدارة / جامعة ...")
        _style_input(self.fields["representative_name"], placeholder="اسم ممثل الجهة")
        _style_input(self.fields["representative_phone"], placeholder="05xxxxxxxx", ltr=True, inputmode="numeric", autocomplete="tel")
        _style_input(self.fields["map_url"], placeholder="https://maps.google.com/...", ltr=True, autocomplete="url")
        _style_input(self.fields["latitude"], placeholder="مثال: 27.511234", ltr=True, inputmode="decimal", autocomplete="off")
        _style_input(self.fields["longitude"], placeholder="مثال: 41.720123", ltr=True, inputmode="decimal", autocomplete="off")

        # select
        self.fields["category"].widget.attrs.setdefault(
            "style",
            "width:100%;padding:12px 12px;border:1px solid #e4e7ec;border-radius:14px;outline:none;background:#fff",
        )

        # textarea
        self.fields["location_description"].widget.attrs.setdefault(
            "style",
            "width:100%;padding:12px 12px;border:1px solid #e4e7ec;border-radius:14px;outline:none;background:#fff",
        )

    def clean_representative_phone(self):
        phone = (self.cleaned_data.get("representative_phone") or "").strip()
        if not phone.isdigit() or len(phone) != 10:
            raise ValidationError("رقم الجوال يجب أن يكون 10 أرقام فقط.")
        # نخزن جوال ممثل الجهة في User.phone → لازم يكون فريد
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("رقم الجوال مستخدم مسبقًا.")
        return phone

    def clean_map_url(self):
        url = (self.cleaned_data.get("map_url") or "").strip()
        if url and not _is_https_url(url):
            raise ValidationError("يرجى إدخال رابط خريطة يبدأ بـ https://")
        return url

    def clean(self):
        cleaned = super().clean()

        lat = cleaned.get("latitude")
        lng = cleaned.get("longitude")
        map_url = (cleaned.get("map_url") or "").strip()
        desc = (cleaned.get("location_description") or "").strip()

        # إما كلاهما معًا أو فارغين
        if (lat is None) ^ (lng is None):
            raise ValidationError("يرجى إدخال خط العرض وخط الطول معًا أو تركهما فارغين.")

        # إلزام معلومة موقع واحدة على الأقل (حسب متطلبك)
        has_coords = (lat is not None and lng is not None)
        if not map_url and not desc and not has_coords:
            raise ValidationError("يرجى إدخال رابط الخريطة أو وصف الموقع أو الإحداثيات.")

        # منع تكرار اسم الجهة (حسّاس للحالة)
        OrganizationProfile = apps.get_model("organizations", "OrganizationProfile")
        org_name = (cleaned.get("org_name") or "").strip()
        if org_name and OrganizationProfile.objects.filter(org_name__iexact=org_name).exists():
            raise ValidationError("اسم الجهة مسجل مسبقًا.")

        return cleaned

    def save(self) -> User:
        data = self.cleaned_data

        # نخزن phone في User كجوال ممثل الجهة لتسهيل التواصل/الدخول لاحقًا
        user = User.objects.create_user(
            email=data["email"],
            password=data["password1"],
            full_name=data.get("representative_name", "").strip(),
            phone=data.get("representative_phone", "").strip(),
            role=self.role,
            is_active=False,
        )

        OrganizationProfile = apps.get_model("organizations", "OrganizationProfile")
        OrganizationProfile.objects.create(
            user=user,
            category=data["category"],
            org_name=data.get("org_name", "").strip(),
            representative_name=data.get("representative_name", "").strip(),
            representative_phone=data.get("representative_phone", "").strip(),
            map_url=(data.get("map_url") or "").strip(),
            location_description=(data.get("location_description") or "").strip(),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
        return user


class OTPVerifyForm(forms.Form):
    code = forms.CharField(label="رمز التحقق", max_length=6)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_input(self.fields["code"], placeholder="000000", ltr=True, inputmode="numeric", autocomplete="one-time-code")

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("رمز التحقق يجب أن يكون 6 أرقام.")
        return code


class EmailLoginForm(forms.Form):
    """
    ✅ تسجيل دخول رسمي:
    - حقل واحد: رقم الجوال أو البريد الإلكتروني (identifier)
    - كلمة مرور
    ملاحظة: أبقينا اسم الكلاس EmailLoginForm حتى لا نغير views.py
    """

    identifier = forms.CharField(label="رقم الجوال أو البريد الإلكتروني", max_length=255)
    password = forms.CharField(label="الرقم السري", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _style_input(
            self.fields["identifier"],
            placeholder="05xxxxxxxx أو name@example.com",
            ltr=True,
            inputmode="email",
            autocomplete="username",
        )
        _style_input(
            self.fields["password"],
            placeholder="••••••••",
            ltr=True,
            autocomplete="current-password",
        )

    def clean(self):
        cleaned = super().clean()
        identifier = (cleaned.get("identifier") or "").strip().lower()
        password = cleaned.get("password")

        if not identifier or not password:
            raise ValidationError("يرجى إدخال بيانات الدخول.")

        # بريد إلكتروني
        if "@" in identifier:
            user = authenticate(email=identifier, password=password)
            if user is None:
                raise ValidationError("بيانات الدخول غير صحيحة.")
            if not user.is_active:
                raise ValidationError("الحساب غير مفعل. يرجى تفعيل الحساب عبر رمز التحقق.")
            cleaned["user"] = user
            return cleaned

        # رقم جوال
        if not identifier.isdigit() or len(identifier) != 10:
            raise ValidationError("أدخل بريدًا صحيحًا أو رقم جوال من 10 أرقام.")

        user = User.objects.filter(phone=identifier).first()
        if not user:
            raise ValidationError("بيانات الدخول غير صحيحة.")
        if not user.check_password(password):
            raise ValidationError("بيانات الدخول غير صحيحة.")
        if not user.is_active:
            raise ValidationError("الحساب غير مفعل. يرجى تفعيل الحساب عبر رمز التحقق.")

        cleaned["user"] = user
        return cleaned
