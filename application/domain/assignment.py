import datetime
import pytz
from dataclasses import dataclass

class Submit():
    def __init__(self, id, date, task_id, files, time_zone = "UTC"):
        self.id = id
        self.task_id = task_id
        self.files = files
        self.date = None
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)


    def __eq__(self, other):
        if isinstance(other, Submit):
            if self.id == other.id and self.task_id == other.task_id:
                return True
        
        return False


    def set_timezones(self, time_zone:str):
        if self.date:
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
    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if isinstance(other, Assignment):
            if self.id == other.id and self.reveal == other.reveal and self.name == other.name and self.deadline == other.deadline:
                return True
        
        return False

    def __hash__(self):
        attr_list = [a for a in dir(self) if not callable(a)]
        return hash(tuple(attr_list))

    def set_timezones(self, time_zone:str):
        if self.reveal is not None:
            self.reveal = self.reveal.astimezone(pytz.timezone(time_zone))
        if self.deadline is not None:
            self.deadline = self.deadline.astimezone(pytz.timezone(time_zone))
        
        for s in self.submits:
            if not s:
                continue
            s.set_timezones(time_zone)

        for file in self.files:
            if not file:
                continue
            file.set_timezones(time_zone)

        for task in self.tasks:
            if not task:
                continue
            task.set_timezones(time_zone)


class Task():
    def __init__(self, id, points, description , files=[], assignment_id=None, time_zone = "UTC", done = False, answer = None):
        self.id = id
        self.description = description
        self.points = points
        self.files = files
        self.answer = answer
        self.assignment_id = assignment_id
        self.done = done

    def __hash__(self):
        attr_list = [a for a in dir(self) if not callable(a) and not a.startswith("__")]
        return hash(tuple(attr_list))

    def set_timezones(self, time_zone:str):
        for file in self.files:
            if not file:
                continue
            file.set_timezones(time_zone)
            if self.answer:
                self.answer.set_timezones(time_zone)
                
    def __eq__(self, other):
        if isinstance(other, Task):
            if self.id == other.id and self.description == other.description and self.points == other.points and self.assignment_id == other.assignment_id:
                return True
        
        return False

    def __str__(self):
        attr_list = [a for a in dir(self) if not callable(a) and not a.startswith("__")]
        return ", ".join(attr_list)

class Answer():
    def __init__(self, id:int, description: str, reveal:datetime.datetime, files:list, time_zone = "UTC"):
        self.id = id
        if reveal is not None:
            self.reveal = pytz.timezone(time_zone).localize(reveal)
        else:
            self.reveal = None
        self.description = description
        self.files = files


    def __hash__(self):
        attr_list = [a for a in dir(self) if not callable(a)]
        return hash(tuple(attr_list))

    def set_timezones(self, time_zone:str):
        for file in self.files:
            if not file:
                continue
            file.set_timezones(time_zone)
        if self.reveal:
            self.reveal = self.reveal.astimezone(pytz.timezone(time_zone))
    


class File():
    def __init__(self, id, name, date:datetime.datetime, time_zone = "UTC"):
        self.id = id
        self.name = name
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)
        else:
            self.date = date

    def set_timezones(self, time_zone:str):
        self.date = self.date.astimezone(pytz.timezone(time_zone))

    def __str__(self):
        return "id: "+str(self.id)+"name: "+self.name
    
    def __hash__(self):
        attr_list = [a for a in dir(self) if not callable(a)]
        return hash(tuple(attr_list))


