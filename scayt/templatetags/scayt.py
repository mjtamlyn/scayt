from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def tag(classification):
    """Converts a classification into a tag"""
    colors = {
        "N/A": "bg-gray-600",
        "UC": "bg-gray-400",
        "A3": "bg-blue-200",
        "A2": "bg-blue-400",
        "A1": "bg-blue-500",
        "B3": "bg-red-200",
        "B2": "bg-red-400",
        "B1": "bg-red-500",
        "MB": "bg-yellow-200",
        "GMB": "bg-yellow-400",
        "EMB": "bg-yellow-500",
    }
    color = colors[classification]
    return mark_safe(
        """<div class="tag {color}">{classification}</div>""".format(
            color=color, classification=classification
        )
    )
