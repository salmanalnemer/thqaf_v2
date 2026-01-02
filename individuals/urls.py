from django.urls import path
from . import views

app_name = "individuals"

urlpatterns = [
    path("dashboard/", views.individual_dashboard, name="dashboard"),
]
