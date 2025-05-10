from django.contrib import admin

from .models import Archer, ArcherSeason, Event, Result, Season, Venue


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["name", "date", "round_family"]
    list_filter = ["season"]


admin.site.register(Archer)
admin.site.register(ArcherSeason)
admin.site.register(Result)
admin.site.register(Season)
admin.site.register(Venue)
