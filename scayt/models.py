from django.core import validators
from django.db import models


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

    def __str__(self):
        return self.host_club_name


class Event(models.Model):
    season = models.ForeignKey(Season, on_delete=models.PROTECT)
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    # TODO round_family
    # TODO age_groups
    entry_link = models.URLField(blank=True, null=True)
    # TODO show_results

    def __str__(self):
        return self.name
