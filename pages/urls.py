from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("courses/", views.public_courses, name="public_courses"),
    path("contact/", views.contact, name="contact"),
]
