from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("", views.Root.as_view(), name="root"),
    path("calendar/", views.Calendar.as_view(), name="calendar"),
    path("standings/", views.Standings.as_view(), name="standings"),
    path("faq/", views.FAQs.as_view(), name="faqs"),
    path("admin/", admin.site.urls),
]
