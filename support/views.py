# support/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.models import Role

def _require_individual(user) -> bool:
    return getattr(user, "role", None) == Role.IND

@login_required
def new_ticket(request):
    if not _require_individual(request.user):
        messages.error(request, "هذه الخدمة مخصصة للأفراد فقط.")
        return redirect("landing")

    # صفحة مؤقتة (تقدر تربطها بنموذج تذكرة لاحقاً)
    return render(request, "support/new_ticket.html")

@login_required
def my_tickets(request):
    if not _require_individual(request.user):
        messages.error(request, "هذه الخدمة مخصصة للأفراد فقط.")
        return redirect("landing")

    return render(request, "support/my_tickets.html")
