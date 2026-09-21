import datetime

from .fields import DbAges


def get_age_group(year_of_birth, year_of_event=None):
    if year_of_event is None:
        year_of_event = datetime.datetime.now().year
    birthday_this_year = year_of_event - year_of_birth

    if birthday_this_year < 12:
        return DbAges.UNDER_12
    elif birthday_this_year < 14:
        return DbAges.UNDER_14
    elif birthday_this_year < 15:
        return DbAges.UNDER_15
    elif birthday_this_year < 16:
        return DbAges.UNDER_16
    elif birthday_this_year < 18:
        return DbAges.UNDER_18
    elif birthday_this_year < 21:
        return DbAges.UNDER_21
    elif birthday_this_year >= 50:
        return DbAges.OVER_50
    return "Adult"
