from django.db import models

from archeryutils.classifications import AGB_ages, AGB_bowstyles, AGB_genders
from archeryutils.classifications.agb_outdoor_classifications import (
    outdoor_bowstyles,
)
from archeryutils.rounds import Round
from django_enumfield.enum import Enum as DbEnum
from django_enumfield.db.fields import EnumField


class RoundField(models.CharField):
    description = "Choose from a set of archery rounds"

    def __init__(self, rounds, **kwargs):
        self.rounds = rounds
        self._round_dict = (
            rounds  # TODO: allow more complex round structures to be passed
        )

        # Handle if the passed rounds are just codenames from a migration.
        if isinstance(rounds, list):
            self._round_dict = {r: r for r in rounds}

        kwargs.setdefault("max_length", 64)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # For deconstruction, use an explicit list of round codenames
        kwargs["rounds"] = list(self._round_dict.keys())
        return name, path, args, kwargs

    @property
    def non_db_attrs(self):
        return super().non_db_attrs + ("rounds",)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self._round_dict[value]

    def to_python(self, value):
        print(value)
        if isinstance(value, Round):
            return value.codename

        if value is None:
            return value

        if value in self.rounds:
            return self._round_dict[value]

        raise ValueError("Round unknown")

    def get_prep_value(self, value):
        if isinstance(value, Round):
            return value.codename
        return value

    def formfield(self, **kwargs):
        from . import forms

        return forms.RoundField(rounds=self.rounds, required=not self.blank)


DbBowstyles = DbEnum(
    "DbBowstyles",
    [(item.name, item.value) for item in AGB_bowstyles if item in outdoor_bowstyles],
)
DbBowstyles.__labels__ = {
    DbBowstyles.RECURVE: "Recurve",
    DbBowstyles.COMPOUND: "Compound",
    DbBowstyles.BAREBOW: "Barebow",
    DbBowstyles.LONGBOW: "Longbow",
}


class BowstyleField(EnumField):
    def __init__(self, enum=DbBowstyles, *args, **kwargs):
        super().__init__(enum, *args, **kwargs)


DbAges = DbEnum(
    "DbAges",
    [(item.name, item.value) for item in AGB_ages],
)
DbAges.__labels__ = {
    DbAges.AGE_50_PLUS: "50+",
    DbAges.AGE_ADULT: "Adult",
    DbAges.AGE_UNDER_21: "U21",
    DbAges.AGE_UNDER_18: "U18",
    DbAges.AGE_UNDER_16: "U16",
    DbAges.AGE_UNDER_15: "U15",
    DbAges.AGE_UNDER_14: "U14",
    DbAges.AGE_UNDER_12: "U12",
}


class AgeField(EnumField):
    def __init__(self, enum=DbAges, *args, **kwargs):
        super().__init__(enum, *args, **kwargs)


DbGender = DbEnum(
    "DbGender",
    [(item.name, item.value) for item in AGB_genders],
)
DbGender.__labels__ = {
    DbGender.MALE: "Men",
    DbGender.FEMALE: "Women",
}


class GenderField(EnumField):
    def __init__(self, enum=DbGender, *args, **kwargs):
        super().__init__(enum, *args, **kwargs)
