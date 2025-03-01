from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models


ROUND_FAMILIES = [
    ('bristol', 'York/Hereford/Bristols'),
    ('metric', '1440s/Metrics'),
    ('720', '720s'),
    ('720/H2H', '720s/H2H'),
    ('s-metric', 'Short Metrics'),
    ('windsor', 'St George/Albion/Windsors'),
    ('western', 'Westerns'),
]

AGE_GROUPS = [
    ('U21', 'U21'),
    ('U18', 'U18'),
    ('U16', 'U16'),
    ('U15', 'U15'),
    ('U14', 'U14'),
    ('U12', 'U12'),
]


class Season(models.Model):
    year = models.PositiveIntegerField(validators=[
        validators.MinValueValidator(2000),
        validators.MaxValueValidator(2100),
    ])

    def __str__(self):
        return '%s season' % self.year

    class Meta:
        ordering = ['-year']


class Venue(models.Model):
    host_club_name = models.CharField(max_length=255)
    post_code = models.CharField(max_length=10)
    website = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['host_club_name']

    def __str__(self):
        return self.host_club_name


def default_age_groups():
    return ['U21', 'U18', 'U16', 'U15', 'U14', 'U12']


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
        help_text='''
            Entry a comma separated list of age groups -
            U21,U18,U16,U15,U14,U12
        ''',
    )
    entry_link = models.URLField(blank=True, null=True)
    # TODO show_results

    def __str__(self):
        return self.name
