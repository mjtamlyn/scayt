import functools

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from django_object_actions import DjangoObjectActions

from .forms import ImportUploadForm
from .models import Archer, ArcherSeason, Event, Result, Season, Venue


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

    def get_form_class(self):
        return ImportUploadForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["event"] = self.get_object()
        context["opts"] = Event._meta
        context.update(**self.admin_site.each_context(self.request))
        return context


admin.site.register(Archer)
admin.site.register(ArcherSeason)
admin.site.register(Result)
admin.site.register(Season)
admin.site.register(Venue)
