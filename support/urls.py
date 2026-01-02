# support/urls.py
from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("new/", views.new_ticket, name="new"),
    path("my/", views.my_tickets, name="my"),
]
