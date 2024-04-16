from django.contrib import admin

from .models import Event, Season, Venue


admin.site.register(Season)
admin.site.register(Venue)
admin.site.register(Event)
