import datetime
import pytz
class Course():
    def __init__(self, name, description, end_date:datetime.datetime, code=None, id=None, assignments = [], min=None, time_zone = "UTC", teacher_id = None, student_count = 0):
        self.name=name
        self.description=description
        self.end_date=end_date
        self.code = code
        self.id = id
        self.assignments = assignments
        self.set_timezones(time_zone)
        self.teacher_id =teacher_id
        self.min = min
        self.student_count = student_count


    def __str__(self):
        return str(id)

    def set_timezones(self, time_zone:str):
        for a in self.assignments:
            a.set_timezones(time_zone)
    
