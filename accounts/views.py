from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

from .forms import (
    IndividualSignupForm,
    OrganizationSignupForm,
    OTPVerifyForm,
    EmailLoginForm,
)
from .models import User, EmailOTP

logger = logging.getLogger(__name__)


PENDING_USER_SESSION_KEY = "pending_activation_user_id"


def register_choice(request):
    """صفحة اختيار نوع التسجيل (فرد/جهة).

    ملاحظة: الأدوار المقيدة (مدرب/مدير إدارة/مشرف/منسق دورات) لا تظهر هنا
    لأنها تُنشأ من قِبل مدير النظام فقط.
    """
    return render(request, "accounts/register_choice.html")


def register_individual(request):
    if request.method == "POST":
        form = IndividualSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_activation_otp(request, user)
            request.session[PENDING_USER_SESSION_KEY] = user.id
            messages.success(request, "تم إنشاء الحساب ✅ أرسلنا رمز التحقق إلى بريدك.")
            return redirect("accounts:verify_otp")
        messages.error(request, "تحقق من البيانات المدخلة.")
    else:
        form = IndividualSignupForm()
    return render(request, "accounts/register_form.html", {"form": form, "title": "تسجيل فرد"})


def register_organization(request):
    if request.method == "POST":
        form = OrganizationSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_activation_otp(request, user)
            request.session[PENDING_USER_SESSION_KEY] = user.id
            messages.success(request, "تم إنشاء حساب الجهة ✅ أرسلنا رمز التحقق إلى بريدك.")
            return redirect("accounts:verify_otp")
        messages.error(request, "تحقق من البيانات المدخلة.")
    else:
        form = OrganizationSignupForm()
    return render(request, "accounts/register_form.html", {"form": form, "title": "تسجيل جهة"})


def verify_otp(request):
    user_id = request.session.get(PENDING_USER_SESSION_KEY)
    if not user_id:
        messages.info(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop(PENDING_USER_SESSION_KEY, None)
        messages.error(request, "لم نتمكن من العثور على الحساب.")
        return redirect("accounts:login")

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = (
                EmailOTP.objects.filter(user=user, is_used=False)
                .order_by("-created_at")
                .first()
            )
            if not otp:
                messages.error(request, "لا يوجد رمز تحقق صالح. اطلب إعادة إرسال الرمز.")
                return redirect("accounts:verify_otp")

            if otp.is_expired():
                messages.error(request, "انتهت صلاحية الرمز. اضغط إعادة إرسال للحصول على رمز جديد.")
                return redirect("accounts:verify_otp")

            if otp.attempts >= 5:
                messages.error(request, "تجاوزت عدد المحاولات. اضغط إعادة إرسال للحصول على رمز جديد.")
                return redirect("accounts:verify_otp")

            if otp.code != code:
                otp.attempts += 1
                otp.save(update_fields=["attempts"])
                messages.error(request, "رمز غير صحيح.")
                return redirect("accounts:verify_otp")

            otp.is_used = True
            otp.save(update_fields=["is_used"])

            user.is_active = True
            user.save(update_fields=["is_active", "user_type", "is_staff", "role"])

            request.session.pop(PENDING_USER_SESSION_KEY, None)
            login(request, user)
            messages.success(request, "تم تفعيل الحساب بنجاح 🎉")
            return redirect("landing")
        messages.error(request, "تحقق من رمز التفعيل.")
    else:
        form = OTPVerifyForm()

    return render(request, "accounts/verify_otp.html", {"form": form, "user": user})


def resend_otp(request):
    """إعادة إرسال رمز التفعيل للحساب المعلق في الجلسة.

    حِماية بسيطة: حد أدنى 60 ثانية بين كل إرسال.
    """
    user_id = request.session.get(PENDING_USER_SESSION_KEY)
    if not user_id:
        messages.info(request, "لا يوجد حساب بانتظار التفعيل.")
        return redirect("accounts:login")

    cooldown_key = "otp_resend_last"
    now_ts = int(timezone.now().timestamp())
    last_ts = int(request.session.get(cooldown_key, 0))
    if now_ts - last_ts < 60:
        messages.warning(request, "يرجى الانتظار قليلًا قبل إعادة الإرسال.")
        return redirect("accounts:verify_otp")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.pop(PENDING_USER_SESSION_KEY, None)
        messages.error(request, "لم نتمكن من العثور على الحساب.")
        return redirect("accounts:login")

    _send_activation_otp(request, user)
    request.session[cooldown_key] = now_ts
    messages.success(request, "تم إرسال رمز جديد إلى بريدك.")
    return redirect("accounts:verify_otp")


def login_view(request):
    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            login(request, user)
            messages.success(request, "تم تسجيل الدخول ✅")
            return redirect("landing")
        messages.error(request, "تحقق من بيانات الدخول.")
    else:
        form = EmailLoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "تم تسجيل الخروج.")
    return redirect("landing")


def _send_activation_otp(request, user: User):
    """إرسال OTP التفعيل عبر البريد مع تسجيل الأخطاء."""
    try:
        otp = EmailOTP.create_for_user(user)
        ctx = {
            "user": user,
            "code": otp.code,
            "ttl_minutes": 10,
            "year": timezone.now().year,
        }
        subject = "رمز تفعيل حسابك | بوابة ثقف"
        text_body = render_to_string("accounts/emails/otp.txt", ctx)
        html_body = render_to_string("accounts/emails/otp.html", ctx)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=False)
    except Exception:
        logger.exception("Failed to send activation OTP")
        messages.warning(request, "تم إنشاء الحساب ✅ لكن تعذر إرسال رمز التفعيل حاليًا.")
