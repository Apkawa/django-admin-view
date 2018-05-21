# coding: utf-8
from __future__ import unicode_literals

import datetime
import pytz
from django.conf import settings

from django.utils import timezone

local_tz = timezone.get_current_timezone()


def local_now(tz=local_tz):
    return datetime.datetime.now(tz)


def to_aware(dt_unaware, tz=local_tz):
    if dt_unaware.tzinfo:
        # maybe aware
        return tz.normalize(dt_unaware)
    return tz.localize(dt_unaware)


def to_unaware(dt_aware):
    return dt_aware.replact(tzinfo=None)


DATE_FORMAT = '%d.%m.%Y'
TIME_FORMAT = '%H:%M'
DATETIME_FORMAT = '%d.%m.%Y %H:%M'


class DisplayDatetime(object):
    def __init__(self, dt,
                 date_format=DATE_FORMAT,
                 datetime_format=DATETIME_FORMAT,
                 time_format=TIME_FORMAT
                 ):
        self._dt = dt
        self._time_format = time_format
        self._date_format = date_format
        self._datetime_format = datetime_format
        self._format = None
        if isinstance(dt, datetime.date):
            self._format = date_format
        elif isinstance(dt, datetime.time):
            self._format = time_format
        elif isinstance(dt, datetime.datetime):
            self._format = datetime_format

    def strftime(self, fmt):
        if self._dt:
            return self._dt.strftime(fmt)
        return ""

    def __format__(self, format_spec):
        if self._dt:
            return self._dt.__format__(format_spec)
        return ""

    def __unicode__(self):
        return unicode(self.__str__())

    def __str__(self):
        return self.strftime(self._format)

    def __repr__(self):
        return self.__str__()


# TODO tests
class DisplayRangeDateTime(object):
    def __init__(self, datetime_from, datetime_end,
                 **kwargs
                 ):
        self.datetime_from = DisplayDatetime(datetime_from, **kwargs)
        self.datetime_to = DisplayDatetime(datetime_end, **kwargs)
        self._format = self.datetime_from._format

    def strftime(self, fmt):
        if self.datetime_from or self.datetime_to:
            return "%s - %s" % (
                self.datetime_from.strftime(fmt),
                self.datetime_to.strftime(fmt),
            )
        return ""

    def __format__(self, format_spec):
        if self.datetime_from or self.datetime_to:
            return "%s - %s" % (
                self.datetime_from.__format__(format_spec),
                self.datetime_to.__format__(format_spec),
            )
        return ""

    def __unicode__(self):
        return unicode(self.__str__())

    def __str__(self):
        return self.strftime(self._format)

    def __repr__(self):
        return self.__str__()
