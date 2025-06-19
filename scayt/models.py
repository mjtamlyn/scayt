from functools import cached_property

from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models

import archeryutils
from archeryutils.classifications import (
    AGB_bowstyles,
    calculate_agb_outdoor_classification,
)
from archerydjango.fields import (
    AgeField,
    BowstyleField,
    GenderField,
    RoundField,
)
from archerydjango.utils import get_age_group


ROUND_FAMILIES = [
    ("bristol", "York/Hereford/Bristols"),
    ("metric", "1440s/Metrics"),
    ("720", "720s"),
    ("720/H2H", "720s/H2H"),
    ("900", "900s"),
    ("s-metric", "Short Metrics"),
    ("windsor", "St George/Albion/Windsors"),
    ("western", "Westerns"),
]

AGE_GROUPS = [
    ("U21", "U21"),
    ("U18", "U18"),
    ("U16", "U16"),
    ("U15", "U15"),
    ("U14", "U14"),
    ("U12", "U12"),
]


class Season(models.Model):
    year = models.PositiveIntegerField(
        validators=[
            validators.MinValueValidator(2000),
            validators.MaxValueValidator(2100),
        ]
    )

    def __str__(self):
        return "%s season" % self.year

    class Meta:
        ordering = ["-year"]


class Venue(models.Model):
    host_club_name = models.CharField(max_length=255)
    post_code = models.CharField(max_length=10)
    website = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ["host_club_name"]

    def __str__(self):
        return self.host_club_name


def default_age_groups():
    return ["U21", "U18", "U16", "U15", "U14", "U12"]


class Event(models.Model):
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    date = models.DateField()
    round_family = models.CharField(max_length=10, choices=ROUND_FAMILIES)
    age_groups = ArrayField(
        models.CharField(max_length=3, choices=AGE_GROUPS),
        size=6,
        default=default_age_groups,
        help_text="""
            Entry a comma separated list of age groups -
            U21,U18,U16,U15,U14,U12
        """,
    )
    entry_link = models.URLField(blank=True, null=True)
    full_results = models.URLField(blank=True, null=True)

    def has_results(self):
        return self.result_set.exists()

    def __str__(self):
        return self.name


class Archer(models.Model):
    agb_number = models.CharField(max_length=12)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    gender = GenderField()
    year = models.PositiveIntegerField(
        "Year of Birth",
        validators=[
            validators.MinValueValidator(2000),
            validators.MaxValueValidator(2100),
        ],
    )
    is_scas_member = models.BooleanField("Is SCAS Member", blank=True)

    @property
    def name(self):
        return "%s %s" % (self.forename, self.surname)

    def __str__(self):
        return self.name


class ArcherSeason(models.Model):
    archer = models.ForeignKey(Archer, on_delete=models.PROTECT)
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    club = models.CharField(max_length=200)
    bowstyle = BowstyleField()
    age_group = AgeField(blank=True, null=True)

    def __str__(self):
        return "%s in %s shooting %s" % (
            self.archer,
            self.season,
            self.bowstyle,
        )

    def save(self, *args, **kwargs):
        if not self.age_group:
            self.age_group = get_age_group(
                self.archer.year,
                self.season.year,
            )
        super().save(*args, **kwargs)

    @cached_property
    def annotated_results(self):
        """Load the results, and then add `weighted_scayt_points`."""
        results = self.result_set.order_by("event__date")
        by_best = sorted(results, key=lambda r: r.scayt_points, reverse=True)
        for result in by_best[:3]:
            result.weighted_scayt_points = result.scayt_points
        for shoot_count, result in enumerate(by_best[3:], 4):
            result.weighted_scayt_points = float(result.scayt_points) / shoot_count
        return results

    @property
    def total_scayt_points(self):
        return sum(map(lambda r: r.weighted_scayt_points, self.annotated_results))


class Result(models.Model):
    archer_season = models.ForeignKey(ArcherSeason, on_delete=models.PROTECT)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    age_group_competed = AgeField(blank=True, null=True)
    shot_round = RoundField(
        archeryutils.load_rounds.WA_outdoor
        | archeryutils.load_rounds.AGB_outdoor_metric
        | archeryutils.load_rounds.AGB_outdoor_imperial
    )
    shot_round_2 = RoundField(
        (
            archeryutils.load_rounds.WA_outdoor
            | archeryutils.load_rounds.AGB_outdoor_metric
            | archeryutils.load_rounds.AGB_outdoor_imperial
        ),
        blank=True,
        null=True,
    )
    pass_1 = models.PositiveIntegerField(blank=True, null=True)
    pass_2 = models.PositiveIntegerField(blank=True, null=True)
    pass_3 = models.PositiveIntegerField(blank=True, null=True)
    pass_4 = models.PositiveIntegerField(blank=True, null=True)
    score = models.PositiveIntegerField()
    hits = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Only for Imperial",
    )
    golds = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Gold for Imperial, 10s for Metric",
    )
    xs = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Only for Metric",
    )
    placing = models.PositiveIntegerField()

    def __str__(self):
        return "{archer} at {event} - Placing {place}".format(
            archer=self.archer_season.archer,
            event=self.event,
            place=self.placing,
        )

    def save(self, *args, **kwargs):
        if not self.age_group_competed:
            self.age_group_competed = self.archer_season.age_group
        super().save(*args, **kwargs)

    @property
    def division(self):
        return "%s %s %s" % (
            self.age_group_competed,
            self.archer_season.bowstyle,
            self.archer_season.archer.gender,
        )

    @property
    def round_name(self):
        if not self.shot_round_2:
            return self.shot_round.name
        if self.shot_round_2 == self.shot_round:
            return "Double %s" % self.shot_round.name
        return "Mixed round - %s & %s" % (self.shot_round.name, self.shot_round_2.name)

    @property
    def n_passes(self):
        if not (self.pass_1 or self.pass_2 or self.pass_3 or self.pass_4):
            return 0
        if self.pass_3 and not self.pass_2:  # Double 720 without splits
            return 2
        if self.shot_round_2:
            return len(self.shot_round.passes) + len(self.shot_round_2.passes)
        return len(self.shot_round.passes)

    @property
    def scayt_points(self):
        if self.placing == 1:
            return 3
        elif self.placing == 2 or self.placing == 3:
            return 2
        return 1

    @property
    def classification(self):
        score = self.score
        if self.shot_round_2:
            if not len(self.shot_round.passes) == 2:
                raise "Unknown double round format"
            score = self.pass_1 + (self.pass_2 or 0)
        return calculate_agb_outdoor_classification(
            score,
            self.shot_round,
            AGB_bowstyles(self.archer_season.bowstyle.value),
            self.archer_season.archer.gender,
            self.archer_season.age_group,
        )

    @property
    def classification_2(self):
        if not self.shot_round_2:
            return None
        if not len(self.shot_round.passes) == 2:
            raise "Unknown double round format"
        return calculate_agb_outdoor_classification(
            self.pass_3 + (self.pass_4 or 0),
            self.shot_round,
            AGB_bowstyles(self.archer_season.bowstyle.value),
            self.archer_season.archer.gender,
            self.archer_season.age_group,
        )
