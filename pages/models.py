from django.db import models


class ContactMessage(models.Model):
    org_name = models.CharField("اسم الجهة", max_length=255)
    org_representative = models.CharField("ممثل الجهة", max_length=255, default="")  # يساعد بالترحيل لو فيه بيانات قديمة
    phone = models.CharField("رقم التواصل", max_length=30)
    email = models.EmailField("البريد الإلكتروني")
    message = models.TextField("نص الرسالة")

    is_sent = models.BooleanField("تم الإرسال؟", default=False)
    send_error = models.TextField("خطأ الإرسال", blank=True, default="")

    created_at = models.DateTimeField("تاريخ الإرسال", auto_now_add=True)

    class Meta:
        verbose_name = "رسالة تواصل"
        verbose_name_plural = "رسائل التواصل"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.org_name} - {self.email}"


class SiteSetting(models.Model):
    """
    إعدادات عامة (Singleton)
    - contact_inbox_email: الإيميل الذي يستقبل رسائل "تواصل معنا"
    """

    contact_inbox_email = models.EmailField(
        "إيميل استقبال رسائل تواصل معنا",
        default="support@thqaf.com",
    )
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"

    def __str__(self) -> str:
        return f"إيميل الاستقبال: {self.contact_inbox_email}"

    @classmethod
    def get_solo(cls) -> "SiteSetting":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
