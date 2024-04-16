from django.views.generic import ListView, TemplateView
from django.utils import timezone

from .models import Season


class Root(TemplateView):
    template_name = 'scayt/root.html'
    page_name = 'root'

    def get_context_data(self, **kwargs):
        season = Season.objects.first()
        upcoming_events = season.event_set.order_by('date', 'name').filter(date__gte=timezone.now().date())[:3]
        return super().get_context_data(season=season, page_name=self.page_name, upcoming_events=upcoming_events, **kwargs)


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
        return context


class FAQs(Root):
    template_name = 'scayt/faqs.html'
    page_name = 'faqs'
