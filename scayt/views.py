import itertools

from django.db.models import Count
from django.views.generic import DetailView, ListView, RedirectView, TemplateView
from django.urls import reverse
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
        previous_seasons = Season.objects.exclude(pk=season.pk).order_by("-year")
        return super().get_context_data(
            current_season=season,
            season=season,
            page_name="root",
            upcoming_events=upcoming_events,
            previous_seasons=previous_seasons,
            **kwargs
        )


class SeasonMixin:
    def get_season(self):
        if "year" in self.kwargs:
            season = Season.objects.get(year=self.kwargs["year"])
        else:
            season = Season.objects.first()
        return season

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_season"] = Season.objects.first()
        return context


class YearRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("calendar", kwargs=self.kwargs)


class Calendar(SeasonMixin, ListView):
    template_name = "scayt/calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        self.season = self.get_season()
        return self.season.event_set.order_by("date", "name").select_related("venue")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.season
        context["page_name"] = "calendar" if self.season.is_current else ""
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


class Standings(SeasonMixin, Root):
    template_name = "scayt/standings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = self.get_season()
        return context


class FinalStandings(SeasonMixin, TemplateView):
    template_name = "scayt/final_standings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = self.get_season()
        context["season"] = season

        categories = itertools.product(
            DbBowstyles,
            (a for a in DbAges if str(a).startswith("U")),
            DbGender,
        )
        all_placings = []
        for bowstyle, age, gender in categories:
            division = "{bow} {age} {gender}".format(
                bow=bowstyle,
                age=age,
                gender=gender,
            )
            archers = (
                ArcherSeason.objects.filter(season=season)
                .annotate(
                    event_count=Count("result"),
                )
                .filter(
                    event_count__gte=3,
                    age_group=age,
                    archer__gender=gender,
                    bowstyle=bowstyle,
                    archer__is_scas_member=True,
                )
                .prefetch_related("result_set")
                .select_related("season")
            )

            placings = sorted(archers, key=lambda a: a.total_scayt_points, reverse=True)

            placing = 0
            current_total = None
            placing_counter = 1
            for archer in placings:
                if archer.total_scayt_points == current_total:
                    placing_counter += 1
                else:
                    current_total = archer.total_scayt_points
                    placing += placing_counter
                    placing_counter = 1
                archer.placing = placing

            if len(archers):
                all_placings.append((division, placings))
        context["all_placings"] = all_placings
        return context


class DivisionStandings(SeasonMixin, TemplateView):
    template_name = "scayt/division_standings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = self.get_season()
        context["season"] = season
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
            season=season,
            age_group=age,
            archer__gender=gender,
            bowstyle=bowstyle,
        ).prefetch_related("result_set").select_related("season")
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
        context["current_season"] = Season.objects.first()
        context["season"] = self.object.season
        context["results"] = self.object.annotated_results
        return context
