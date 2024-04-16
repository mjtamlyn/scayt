from django.views.generic import TemplateView

from .models import Season


class Root(TemplateView):
    template_name = 'scayt/root.html'
    page_name = 'root'

    def get_context_data(self, **kwargs):
        season = Season.objects.first()
        return super().get_context_data(season=season, page_name=self.page_name, **kwargs)


class FAQs(Root):
    template_name = 'scayt/faqs.html'
    page_name = 'faqs'
