from django import forms
from django.contrib.admin.helpers import Fieldset


class ImportUploadForm(forms.Form):
    file = forms.FileField(help_text="CSV format")
    _fieldsets = [(None, {"fields": ["file"]})]

    @property
    def fieldsets(self):
        return [
            Fieldset(
                form=self,
                name=name,
                fields=field_options.get("fields", ()),
                classes=field_options.get("classes", ()),
                description=field_options.get("description", None),
            )
            for name, field_options in self._fieldsets
        ]
