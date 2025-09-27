import io

from django import forms
from django.contrib.admin.helpers import Fieldset


class ImportUploadForm(forms.Form):
    file = forms.FileField(help_text="CSV format")
    _fieldsets = [(None, {"fields": ["file"]})]

    def clean_file(self):
        file = self.cleaned_data["file"]
        decoded_file = file.read().decode("utf-8")
        return io.StringIO(decoded_file)

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


class ImportConfirmForm(forms.Form):
    raw = forms.CharField(widget=forms.HiddenInput())

    def clean_raw(self):
        data = self.cleaned_data["raw"]
        return io.StringIO(data)

    def __init__(self, raw=None, archer_data=None, **kwargs):
        initial = kwargs.get("initial", {})
        initial.update(
            {
                "raw": raw,
            }
        )
        kwargs["initial"] = initial

        self._fieldsets = [(None, {"fields": ["raw"]})]
        for row in archer_data:
            if not row["archer"].pk:
                year_field_name = "%s_year" % row["archer"].agb_number
                scas_field_name = "%s_is_scas_member" % row["archer"].agb_number
                self.base_fields[year_field_name] = forms.IntegerField(
                    label="Year of Birth",
                    min_value=2000,
                    max_value=2100,
                )
                self.base_fields[scas_field_name] = forms.BooleanField(
                    label="Is SCAS Member?",
                    initial=True,
                    required=False,
                )
                row["fieldset"] = Fieldset(
                    form=self,
                    name=row["archer"].name,
                    fields=[year_field_name, scas_field_name],
                )

        self.archer_data = archer_data

        super().__init__(**kwargs)

    def clean(self):
        for row in self.archer_data:
            if not row["archer"].pk:
                archer = row["archer"]
                agb = archer.agb_number
                archer.year = self.cleaned_data["%s_year" % agb]
                archer.is_scas_member = self.cleaned_data["%s_is_scas_member" % agb]

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
