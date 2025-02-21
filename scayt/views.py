from django.views.generic import ListView, TemplateView
from django.utils import timezone

from .models import Season


class Root(TemplateView):
    template_name = 'scayt/root.html'

    def get_context_data(self, **kwargs):
        season = Season.objects.first()
        upcoming_events = season.event_set.order_by('date', 'name').filter(date__gte=timezone.now().date())[:3]
        return super().get_context_data(season=season, page_name='root', upcoming_events=upcoming_events, **kwargs)


class Calendar(ListView):
    template_name = 'scayt/calendar.html'
    context_object_name = 'events'

    def get_queryset(self):
        self.season = Season.objects.first()
        return self.season.event_set.order_by('date', 'name').select_related('venue')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = self.season
        context['page_name'] = 'calendar'
        context['page_title'] = '%s Calendar' % self.season.year
        return context


class FAQs(Root):
    template_name = 'scayt/faqs.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'FAQs'
        context['page_name'] = 'faqs'
        return context


class Standings(Root):
    template_name = 'scayt/standings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['season'] = Season.objects.first()
        return context
