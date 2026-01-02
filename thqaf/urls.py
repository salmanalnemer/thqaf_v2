from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = " لوحة تحكم بوابة ثقف إدارة النظام "
admin.site.site_title = "THQAF Admin"
admin.site.index_title = "إدارة النظام"

urlpatterns = [
    path("admin/", admin.site.urls),

    # الصفحات العامة (Landing / Courses / Contact) من pages/urls.py
    path("", include("pages.urls")),

    # مسارات الحسابات والتطبيقات
    path("accounts/", include("accounts.urls")),
    path("individuals/", include("individuals.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
