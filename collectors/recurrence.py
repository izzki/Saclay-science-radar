"""Expansion RFC 5545 : RRULE, RDATE, EXDATE et exceptions RECURRENCE-ID."""
import os
from datetime import datetime,timedelta,timezone
from icalendar import Calendar
import recurring_ical_events


def expand_calendar(text, reference=None, horizon_days=None):
    calendar=Calendar.from_ical(text)
    reference=reference or datetime.now(timezone.utc)
    horizon_days=horizon_days or int(os.getenv('RADAR_RECURRENCE_HORIZON_DAYS','730'))
    series={str(e.get('uid','')) for e in calendar.walk('VEVENT') if e.get('rrule') or e.get('rdate')}
    for e in calendar.walk('VEVENT'):
        rule=e.get('rrule')
        if rule and str(rule.get('FREQ',[''])[0]).upper() in ('SECONDLY','MINUTELY'):
            raise ValueError('Récurrence à la seconde/minute : fréquence non adaptée au catalogue ; calendrier à contrôler')
    singles=[e for e in calendar.walk('VEVENT') if str(e.get('uid','')) not in series]
    occurrences=[]
    if series:
        occurrences=[e for e in recurring_ical_events.of(calendar).between(reference-timedelta(days=366),reference+timedelta(days=horizon_days)) if str(e.get('uid','')) in series]
    return singles+occurrences,series
