import datetime
import pytz
class Submit():
    def __init__(self, id, date, task_id, file_ids, time_zone = "UTC"):
        self.id = id
        self.task_id = task_id
        self.file_ids = file_ids
        self.date = None
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)

    def set_timezones(self, time_zone:str):
        self.date = self.date.astimezone(pytz.timezone(time_zone))

class Assignment():
    def __init__(self, id, name, reveal, deadline, tasks, files = [], time_zone = "UTC", submits = []):
        self.id = id
        self.reveal=reveal
        self.name = name
        if self.reveal is not None:
            self.reveal = pytz.timezone(time_zone).localize(reveal)
        self.deadline=deadline
        if self.deadline is not None:
            self.deadline = pytz.timezone(time_zone).localize(deadline)
        self.tasks = tasks
        self.files = files
        self.submits = submits

    def set_timezones(self, time_zone:str):
        if self.reveal is not None:
            self.reveal = self.reveal.astimezone(pytz.timezone(time_zone))
        if self.deadline is not None:
            self.deadline = self.deadline.astimezone(pytz.timezone(time_zone))
        
        for s in self.submits:
            s.set_timezones()

        for file in self.files:
            file.set_timezones(time_zone)

        for task in self.tasks:
            task.set_timezones(time_zone)


class Task():
    def __init__(self, id, points, description , files=[], assignment_id=None, time_zone = pytz.timezone("UTC"), done = False):
        self.id = id
        self.description = description
        self.points = points
        self.files = files
        self.assignment_id = assignment_id
        self.done = done

    def set_timezones(self, time_zone:str):
        for file in self.files:
            file.set_timezones(time_zone)



class File():
    def __init__(self, id, name, date:datetime.datetime, time_zone = "UTC"):
        self.id = id
        self.name = name
        self.date = pytz.timezone(time_zone).localize(date)

    def set_timezones(self, time_zone:str):
        self.date = self.date.astimezone(pytz.timezone(time_zone))
        


