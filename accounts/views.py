from django.http import HttpResponse

def landing(request):
    return HttpResponse("THQAF landing - OK")

from django.shortcuts import render


def landing(request):
    stats = {
        "courses": 0,
        "beneficiaries": 0,
        "certificates": 0,
    }
    return render(request, "pages/landing.html", {"stats": stats})


def public_courses(request):
    return render(request, "pages/public_courses.html")


def contact(request):
    # Placeholder الآن (سنعمل form + model لاحقًا)
    return render(request, "pages/contact.html")
