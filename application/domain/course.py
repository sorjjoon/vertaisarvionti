import datetime
import pytz
class Course():
    def __init__(self, name, description, end_date:datetime.datetime, code=None, id=None, assignments = [], time_zone = "UTC"):
        self.name=name
        self.description=description
        self.end_date=end_date
        self.code = code
        self.id = id
        self.assignments = assignments
        self.set_timezones(time_zone)

    def __str__(self):
        return str(id)

    def set_timezones(self, time_zone:str):
        for a in self.assignments:
            a.set_timezones(time_zone)
    
