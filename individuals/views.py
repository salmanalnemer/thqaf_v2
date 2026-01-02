from __future__ import annotations

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from accounts.models import Role


def _count_user_rows(app_label: str, model_name: str, user_field: str, user_id: int) -> int:
    """
    يعدّ سجلات مرتبطة بالمستخدم بشكل آمن.
    إذا الموديل غير موجود أو الحقل غير صحيح يرجّع 0 بدل ما يكسر الصفحة.
    """
    try:
        Model = apps.get_model(app_label, model_name)
        if Model is None:
            return 0
        return Model.objects.filter(**{user_field: user_id}).count()
    except Exception:
        return 0


@login_required
def individual_dashboard(request):
    # ✅ السماح للأفراد فقط
    if getattr(request.user, "role", None) != Role.IND:
        messages.error(request, "هذه الصفحة مخصصة للأفراد فقط.")
        return redirect("landing")

    uid = request.user.id

    # ✅ عدّ الدورات: جرّب أشهر أسماء موديلات/حقول بدون كسر
    # عدّل هذه الأسماء لاحقاً لتطابق نظامك إذا رغبت (سأقول لك كيف بأسفل).
    courses_count = (
        _count_user_rows("courses", "Enrollment", "user_id", uid)
        or _count_user_rows("courses", "Registration", "user_id", uid)
        or _count_user_rows("courses", "CourseRegistration", "user_id", uid)
        or _count_user_rows("courses", "Participant", "user_id", uid)
    )

    # ✅ عدّ الشهادات: جرّب أشهر أسماء
    certificates_count = (
        _count_user_rows("certificates", "Certificate", "user_id", uid)
        or _count_user_rows("certificates", "UserCertificate", "user_id", uid)
        or _count_user_rows("certificates", "IssuedCertificate", "user_id", uid)
    )

    return render(
        request,
        "individuals/individual_dashboard.html",
        {
            "courses_count": courses_count,
            "certificates_count": certificates_count,
        },
    )
