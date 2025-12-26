from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives

from .forms import ContactMessageForm
from .models import ContactMessage, SiteSetting


def landing(request):
    context = {
        "stats": {"courses": 0, "beneficiaries": 0, "certificates": 0},
        "audiences": [
            {"icon": "ti ti-users", "title": "الأفراد", "desc": "مستفيدون من الدورات"},
            {"icon": "ti ti-building-community", "title": "جهات حكومية", "desc": "طلب واعتماد الدورات"},
            {"icon": "ti ti-briefcase", "title": "قطاع خاص", "desc": "برامج تدريبية ومبادرات"},
            {"icon": "ti ti-school", "title": "تعليم", "desc": "مدارس وجامعات"},
        ],
        "faqs": [
            {"q": "كيف أسجل كجهة؟", "a": "من بوابة الجهات: سجل البيانات ثم فعّل البريد عبر رمز التحقق."},
            {"q": "كيف يسجل الفرد بالدورات؟", "a": "يسجل حسابه ثم يمكنه التسجيل في الدورات المفتوحة."},
            {"q": "هل يمكن طباعة الشهادات؟", "a": "نعم، بعد إصدار الشهادة يمكن عرضها وطباعتها."},
        ],
    }
    return render(request, "pages/landing.html", context)


def public_courses(request):
    return render(request, "pages/public_courses.html")


def contact(request):
    if request.method == "POST":
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            obj: ContactMessage = form.save()

            # ✅ الإيميل المستلم من لوحة التحكم (مع fallback للإعداد)
            settings_obj = SiteSetting.get_solo()
            inbox_email = (settings_obj.contact_inbox_email or "").strip() or getattr(settings, "CONTACT_TO_EMAIL", None)

            try:
                if not inbox_email:
                    raise ValueError("لا يوجد بريد مستلم مضبوط في SiteSetting أو CONTACT_TO_EMAIL")

                subject = f"رسالة تواصل جديدة | {obj.org_name}"

                # رقم بلاغ مرتب
                ref = f"THQAF-{obj.id:06d}"

                # سياق القالب
                ctx = {
                    "obj": obj,
                    "ref": ref,
                    "created_at": timezone.localtime(obj.created_at).strftime("%Y-%m-%d %I:%M %p"),
                    "year": timezone.now().year,
                    # لو عندك شعار برابط مطلق (أفضل للإيميل):
                    # "logo_url": "https://thqaf.com/static/assets/img/logo.png",
                }

                # ✅ محتوى نصي احتياطي + HTML
                text_body = render_to_string("pages/emails/contact_message.txt", ctx)
                html_body = render_to_string("pages/emails/contact_message.html", ctx)

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[inbox_email],
                    reply_to=[obj.email],
                )
                email.attach_alternative(html_body, "text/html")
                email.send(fail_silently=False)

                obj.is_sent = True
                obj.send_error = ""
                obj.save(update_fields=["is_sent", "send_error"])

            except Exception as e:
                obj.is_sent = False
                obj.send_error = str(e)
                obj.save(update_fields=["is_sent", "send_error"])

            # ✅ UX: نبلغ المستخدم حسب نجاح الإرسال
            if obj.is_sent:
                messages.success(request, "تم استلام رسالتك بنجاح ✅ وسيتم التواصل معكم من قبل المختصين.")
            else:
                messages.warning(request, "تم استلام رسالتك ✅ لكن تعذّر إرسالها للبريد حالياً، وسيتم معالجتها قريباً.")
            return redirect("contact")

        messages.error(request, "تأكد من تعبئة الحقول بشكل صحيح.")
    else:
        form = ContactMessageForm()

    return render(request, "pages/contact.html", {"form": form})
