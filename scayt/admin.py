import csv
import functools
import io

from django.db import transaction
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from archerydjango.fields import DbAges, DbBowstyles, DbGender
from django_object_actions import DjangoObjectActions

from .forms import ImportConfirmForm, ImportUploadForm
from .models import Archer, ArcherSeason, Event, Result, Season, Venue, rounds


@admin.register(Event)
class EventAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = ["name", "date", "round_family"]
    list_filter = ["season"]
    change_actions = ["import_results"]

    def get_urls(self):
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return functools.update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        urls.insert(
            0,
            path(
                "<pk>/import/",
                wrap(ImportResultsView.as_view(admin_site=self.admin_site)),
                name="%s_%s_import" % info,
            ),
        )
        return urls

    def import_results(self, request, instance):
        url = reverse(
            "admin:%s_%s_import"
            % (self.model._meta.app_label, self.model._meta.model_name),
            kwargs={"pk": instance.pk},
        )
        return HttpResponseRedirect(url)

    import_results.short_description = "Import Results"
    import_results.label = "Import Results"


class ImportResultsView(SingleObjectMixin, FormView):
    template_name = "admin/scayt/event/import_results.html"
    model = Event
    object = None
    admin_site = None
    data = []

    def get_success_url(self):
        event = self.get_object()
        url = reverse(
            "admin:%s_%s_change"
            % (self.model._meta.app_label, self.model._meta.model_name),
            kwargs={"object_id": event.pk},
        )
        return url

    def get_form_class(self):
        if self.data or "raw" in self.request.POST:
            return ImportConfirmForm
        return ImportUploadForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not self.data:
            if "raw" in self.request.POST:
                self.data = self.translate_data(
                    self.get_object(), io.StringIO(self.request.POST["raw"])
                )
                kwargs["archer_data"] = self.data
            return kwargs
        else:
            kwargs["raw"] = self.raw
            kwargs["archer_data"] = self.data
            kwargs.pop("data")
            kwargs.pop("files")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.get_object()
        context["opts"] = Event._meta
        context["data"] = self.data
        context["data_has_errors"] = sum(len(row["errors"]) for row in self.data)
        context.update(**self.admin_site.each_context(self.request))
        return context

    def form_valid(self, form):
        event = self.get_object()

        save = False
        if self.data or "raw" in self.request.POST:
            file = form.cleaned_data["raw"]
            save = True
        else:
            file = form.cleaned_data["file"]
            self.raw = file.read()
            file.seek(0)

        if not self.data:
            self.data = self.translate_data(event, file)

        if save:
            self.save(self.data)
            messages.success(
                self.request,
                "%s results processed for %s"
                % (
                    len(self.data),
                    event,
                ),
            )
            return super().form_valid(form)
        return self.render_to_response(self.get_context_data())

    def translate_data(self, event, file):
        reader = csv.DictReader(file)
        data = []
        for row in reader:
            archer = self.find_archer(row)
            season = self.find_season(row, archer["instance"], event)
            result = self.find_result(row, season["instance"], event)
            all_messages = archer["messages"] + season["messages"] + result["messages"]
            data.append(
                {
                    "errors": [
                        message["message"]
                        for message in all_messages
                        if message["level"] == "error"
                    ],
                    "messages": all_messages,
                    "archer": archer["instance"],
                    "season": season["instance"],
                    "result": result["instance"],
                }
            )
        return data

    def find_archer(self, row):
        messages = []
        try:
            archer = Archer.objects.get(agb_number=row["AGB Number"])
            messages.append(
                {
                    "message": "Found archer",
                    "level": "success",
                }
            )
        except Archer.DoesNotExist:
            archer = Archer(
                agb_number=row["AGB Number"],
                forename=row["Name"].split(" ", 1)[0],
                surname=row["Name"].split(" ", 1)[1],
                gender=DbGender.__lookup__[row["Gender"]],
            )
            messages.append(
                {
                    "message": "Creating new archer",
                    "level": "warning",
                }
            )
        return {"instance": archer, "messages": messages}

    def find_season(self, row, archer, event):
        bowstyle = DbBowstyles.__lookup__[row["BowStyle"]]
        messages = []
        try:
            if not archer.pk:
                raise ArcherSeason.DoesNotExist
            season = ArcherSeason.objects.get(
                archer=archer,
                season=event.season,
                bowstyle=bowstyle,
            )
            messages.append(
                {
                    "message": "Found season",
                    "level": "success",
                }
            )
        except ArcherSeason.DoesNotExist:
            season = ArcherSeason(
                archer=archer,
                season=event.season,
                bowstyle=bowstyle,
                club=row["Club"],
            )
            messages.append(
                {
                    "message": "Creating new archer season",
                    "level": "warning",
                }
            )
        return {"instance": season, "messages": messages}

    def find_result(self, row, season, event):
        messages = []
        try:
            if not season.pk:
                raise Result.DoesNotExist
            result = Result.objects.get(
                archer_season=season,
                event=event,
            )
            messages.append(
                {
                    "message": "Result already exists!",
                    "level": "error",
                }
            )
        except Result.DoesNotExist:
            shot_round = shot_round_2 = None
            round_name = row["Round"]
            if round_name.startswith("Double "):
                shot_round = self.round_finder(round_name[7:])
                shot_round_2 = shot_round
            else:
                shot_round = self.round_finder(round_name)
            if not shot_round:
                messages.append(
                    {
                        "message": "Round not found for %s" % round_name,
                        "level": "error",
                    }
                )
            result = Result(
                archer_season=season,
                event=event,
                placing=row["Placing"],
                age_group_competed=DbAges.__lookup__[row["Age Group"]],
                shot_round=shot_round,
                shot_round_2=shot_round_2,
                score=row["Score"],
                golds=row.get("10+X", row.get("Golds")),
                hits=row.get("Hits"),
                xs=row.get("X"),
                pass_1=row.get("1st Distance"),
                pass_2=row.get("2nd Distance"),
                pass_3=row.get("3rd Distance"),
                pass_4=row.get("4th Distance"),
            )
            if not messages:
                messages.append(
                    {
                        "message": "Creating new result",
                        "level": "success",
                    }
                )
        return {"instance": result, "messages": messages}

    def round_finder(self, name):
        round_ident = {
            "WA 70m": "wa720_70",
            "WA 60m": "wa720_60",
            "WA 50m Compound": "wa720_50_c",
            "WA 50m Barebow": "wa720_50_b",
            "Metric 122-50": "metric_122_50",
            "Metric 122-40": "metric_122_40",
            "Metric 122-30": "metric_122_30",
            "Metric 80-40": "metric_80_40",
            "Metric 80-30": "metric_80_30",
            "WA 1440 70m": "wa1440_70",
            "WA 1440 60m": "wa1440_60",
            "Metric II": "metric_ii",
            "Metric III": "metric_iii",
            "Metric IV": "metric_iv",
            "Metric V": "metric_v",
            "Short Metric I": "short_metric_i",
            "Short Metric II": "short_metric_ii",
            "Short Metric III": "short_metric_iii",
            "Short Metric IV": "short_metric_iv",
            "Short Metric V": "short_metric_v",
            "WA900": "wa900",
            "900-50": "agb900_50",
            "900-40": "agb900_40",
            "900-30": "agb900_30",
            "York": "york",
            "Hereford": "hereford",
            "Bristol I": "bristol_i",
            "Bristol II": "bristol_ii",
            "Bristol III": "bristol_iii",
            "Bristol IV": "bristol_iv",
            "Bristol V": "bristol_v",
            "Western": "western",
            "Western 50": "western_50",
            "Western 40": "western_40",
            "Western 30": "western_30",
            "Western 20": "western_20",
            "Albion": "albion",
            "Windsor": "windsor",
            "Windsor 50": "windsor_50",
            "Windsor 40": "windsor_40",
            "Windsor 30": "windsor_30",
        }.get(name)
        try:
            return rounds[round_ident or name]
        except KeyError:
            return None

    def save(self, data):
        with transaction.atomic():
            for row in data:
                if not row["archer"].pk:
                    row["archer"].save()
                if not row["season"].pk:
                    row["season"].save()
                row["result"].save()


admin.site.register(Archer)
admin.site.register(ArcherSeason)
admin.site.register(Result)
admin.site.register(Season)
admin.site.register(Venue)
