import datetime
import pytz
class Submit():
    def __init__(self, id, date, task_id, files, time_zone = "UTC"):
        self.id = id
        self.task_id = task_id
        self.files = files
        self.date = None
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)

    def set_timezones(self, time_zone:str):
        self.date = self.date.astimezone(pytz.timezone(time_zone))

class Assignment():
    def __init__(self, id, name, reveal:datetime.datetime, deadline:datetime.datetime, tasks, files = [], time_zone = "UTC", submits = []):
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


    def get_deadline_string(self):
        if self.deadline is None:
            return ""
        now = datetime.datetime.now(pytz.utc)
        deadline_adjusted = self.deadline.astimezone(pytz.utc)
        diff = deadline_adjusted - now
        hours = diff.seconds // 3600
        
        minutes = (diff.seconds - 3600*hours)//60
        seconds = (diff.seconds -3600*hours - 60*minutes)
        if diff.days > 1:
            first = str(diff.days)+" päivää ja "

            if hours > 1:
                second = str(hours) + " tuntia"
            elif minutes > 1:
                second = str(minutes)+" minuuttia "
            elif seconds > 1:
                second = str(seconds) +" sekuntia"
        if hours > 1:
            first = str(hours) + " tuntia ja "
            if minutes > 1:
                second = str(minutes)+" minuuttia "
            elif seconds > 1:
                second = str(seconds) +" sekuntia"
        else:
            first = str(minutes)+" minuuttia ja "
            second = str(seconds) +" sekuntia"

        if now > deadline_adjusted:
            after = " sitten"
        else:
            after = " jäljellä"
        return first + second+after

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
        


