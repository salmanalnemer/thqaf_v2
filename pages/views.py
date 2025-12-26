from django.shortcuts import render

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
    return render(request, "pages/contact.html")
