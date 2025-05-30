from django.contrib import admin
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.Root.as_view(), name="root"),
    path("calendar/", views.Calendar.as_view(), name="calendar"),
    path(
        "results/<int:pk>/",
        views.EventResults.as_view(),
        name="event-results",
    ),
    path("standings/", views.Standings.as_view(), name="standings"),
    re_path(
        r"^standings/(?P<bow>[RCBL])U(?P<age>\d+)(?P<gender>[MW])/$",
        views.DivisionStandings.as_view(),
        name="division-standings",
    ),
    path(
        "standings/<int:pk>/",
        views.IndividualStandings.as_view(),
        name="individual-standings",
    ),
    path("faq/", views.FAQs.as_view(), name="faqs"),
    path("admin/", admin.site.urls),
]
