from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from pages import views as pages_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # الصفحات العامة (الهيدر)
    path("", pages_views.landing, name="landing"),
    path("courses/", pages_views.public_courses, name="public_courses"),
    path("contact/", pages_views.contact, name="contact"),

    # مسارات الحسابات والتطبيقات
    path("accounts/", include("accounts.urls")),
    path("org/", include("organizations.urls")),
    path("individuals/", include("individuals.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
