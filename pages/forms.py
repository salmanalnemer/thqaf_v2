from django import forms
from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["org_name", "org_representative", "phone", "email", "message"]
        widgets = {
            "org_name": forms.TextInput(attrs={"placeholder": "مثال: جامعة حائل"}),
            "org_representative": forms.TextInput(attrs={"placeholder": "مثال: أحمد محمد"}),
            "phone": forms.TextInput(attrs={"placeholder": "05xxxxxxxx"}),
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"}),
            "message": forms.Textarea(attrs={"placeholder": "اكتب رسالتك هنا..."}),
        }
