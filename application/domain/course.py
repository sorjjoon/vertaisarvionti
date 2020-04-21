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

    def divide_assignment(self):
        self.past = []
        self.future = []
        now = datetime.datetime.now(pytz.utc)
        for a in self.assignments:
            if a.deadline is None:
                self.future.append(a)
                continue
            deadline_adjusted = a.deadline.astimezone(pytz.utc)
            if deadline_adjusted > now:
                self.future.append(a)
            else:
                self.past.append(a)

    def set_timezones(self, time_zone:str):
        for a in self.assignments:
            a.set_timezones(time_zone)
    
