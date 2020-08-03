import datetime

import pytz


class DomainBase():
    def set_timezones(self, time_zone: str):
        for x in self:
            a = getattr(self, x)
            if isinstance(a, datetime.datetime):
                setattr(self, x, a.astimezone(pytz.timezone(time_zone)))
                
    def __iter__(self):
        atrributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self, a))]
        return atrributes.__iter__()
    