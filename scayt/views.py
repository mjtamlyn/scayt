from django.views.generic import DetailView, ListView, TemplateView
from django.utils import timezone

from archerydjango.fields import DbAges, DbBowstyles, DbGender

from .models import ArcherSeason, Event, Season


class Root(TemplateView):
    template_name = "scayt/root.html"

    def get_context_data(self, **kwargs):
        season = Season.objects.first()
        upcoming_events = season.event_set.order_by("date", "name").filter(
            date__gte=timezone.now().date()
        )[:3]
        return super().get_context_data(
            season=season, page_name="root", upcoming_events=upcoming_events, **kwargs
        )


class Calendar(ListView):
    template_name = "scayt/calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        self.season = Season.objects.first()
        return self.season.event_set.order_by("date", "name").select_related("venue")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.season
        context["page_name"] = "calendar"
        context["page_title"] = "%s Calendar" % self.season.year
        return context


class FAQs(Root):
    template_name = "scayt/faqs.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "FAQs"
        context["page_name"] = "faqs"
        return context


class EventResults(DetailView):
    model = Event
    template_name = "scayt/event_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["results"] = self.object.result_set.order_by(
            "archer_season__bowstyle",
            "age_group_competed",
            "archer_season__archer__gender",
            "placing",
        ).select_related("archer_season", "archer_season__archer")
        return context


class Standings(Root):
    template_name = "scayt/standings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = Season.objects.first()
        return context


class DivisionStandings(TemplateView):
    template_name = "scayt/division_standings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = Season.objects.first()
        bowstyle = {
            "R": DbBowstyles.RECURVE,
            "C": DbBowstyles.COMPOUND,
            "B": DbBowstyles.BAREBOW,
            "L": DbBowstyles.LONGBOW,
        }[self.kwargs["bow"]]
        gender = {
            "M": DbGender.MALE,
            "W": DbGender.FEMALE,
        }[self.kwargs["gender"]]
        age = DbAges["AGE_UNDER_%s" % self.kwargs["age"]]
        context["division"] = "{bow} {age} {gender}".format(
            bow=bowstyle,
            age=age,
            gender=gender,
        )
        archers = ArcherSeason.objects.filter(
            age_group=age,
            archer__gender=gender,
            bowstyle=bowstyle,
        ).prefetch_related("result_set")
        context["placings"] = sorted(
            archers, key=lambda a: a.total_scayt_points, reverse=True
        )

        placing = 0
        current_total = None
        placing_counter = 1
        for archer in context["placings"]:
            if archer.total_scayt_points == current_total:
                placing_counter += 1
            else:
                current_total = archer.total_scayt_points
                placing += placing_counter
                placing_counter = 1
            archer.placing = placing

        return context


class IndividualStandings(DetailView):
    template_name = "scayt/individual_standings.html"
    model = ArcherSeason

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = Season.objects.first()
        context["results"] = self.object.annotated_results
        return context
