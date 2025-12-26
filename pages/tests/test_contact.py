from django.test import TestCase
from django.urls import reverse
from django.core import mail

from pages.models import ContactMessage


class ContactTests(TestCase):
    def test_contact_success_saves_and_sends(self):
        url = reverse("contact")
        payload = {
            "org_name": "جهة تجريبية",
            "org_rep": "سلمان",
            "phone": "0500000000",
            "email": "test@example.com",
            "message": "هذه رسالة اختبار طويلة بما يكفي.",
        }

        # في بيئة الاختبار Django يستخدم locmem email backend تلقائياً غالباً
        res = self.client.post(url, payload, follow=True)
        self.assertEqual(res.status_code, 200)

        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertGreaterEqual(len(mail.outbox), 1)
