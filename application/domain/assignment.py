import datetime
import pytz
from .base import DomainBase

class Feedback(DomainBase):
    def __init__(self, id:int=None, points=None,modified=None, date:datetime.datetime=None, submit_id:int=None, files=None, owner_id=None, description=None, visible=None, time_zone = "UTC"):
        self.type="feedback"
        self.id = id
        
        self.submit_id = submit_id
        self.points = points
        self.owner_id=owner_id
        self.modified = modified
        if files:
            self.files=files
        else:
            self.files = []
        self.visible=visible
        self.date = None
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)
        if modified is not None:
            self.modified = pytz.timezone(time_zone).localize(modified)
    def set_timezones(self, time_zone):
        if self.date:
            self.date = self.date.astimezone(pytz.timezone(time_zone))
        if self.modified:
            self.modified = self.modified.astimezone(pytz.timezone(time_zone))



class Submit(DomainBase):
    def __init__(self, id:int=None, date:datetime.datetime=None, task_id:int=None, files=[],feedback=None, description:str=None, time_zone = "UTC"):
        self.type="submit"
        self.id = int(id)
        self.task_id = int(task_id)
        self.files = files
        
        self.description = description
        self.date = None
        self.feedback = feedback
        
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

        if self.feedback:
            self.feedback.set_timezones(time_zone)

    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return "id: "+str(self.id)+" task_id: "+str(self.task_id)


class Assignment(DomainBase):
    def __init__(self, id, name, reveal:datetime.datetime, deadline:datetime.datetime, tasks, files = [], time_zone = "UTC", submits = [], task_count = None, submit_count = None, course_id=None, course_abbreviation=None):
        self.type="assignment"
        self.id = id
        self.reveal=reveal
        self.name = name
        self.task_count = task_count
        self.submit_count = submit_count
        self.course_id = course_id
        self.course_abbreviation = course_abbreviation
        if self.reveal is not None:
            self.reveal = pytz.timezone(time_zone).localize(reveal)
        
        self.deadline=deadline
        if self.deadline is not None:
            self.deadline = pytz.timezone(time_zone).localize(deadline)
        self.tasks = tasks
        if files:
            self.files = files
        else:
            self.files = []
        self.submits = submits

        
    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if isinstance(other, Assignment):
            if self.id == other.id and self.reveal == other.reveal and self.name == other.name and self.deadline == other.deadline:
                return True
        
        return False
    def answer_length(self):
        i = 0
        for t in self.tasks:
            
            if t.answer is not None:
                i+=1
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

    def __repr__(self):
        return ", ".join(["id: ", self.id,  "files: ", self.files, "answer: "])

class Task(DomainBase):
    def __init__(self, id, number, points, description , files=[], assignment_id=None, time_zone = "UTC", done:bool = False, answer = None):
        self.type="task"
        if id is not None:
            self.id = int(id)
        else:
            self.id = None
        self.number = number
        self.description = description
        self.points = points
        if files:
            self.files = files
        else:
            self.files = []
        self.answer = answer
        self.assignment_id = assignment_id
        self.done = done

    def __hash__(self):
        attr_list = [a for a in dir(self) if not callable(a) and not a.startswith("__")]
        return hash(tuple(attr_list))

    def set_timezones(self, time_zone:str):
        for file in self.files:
            if not file or not isinstance(file, File):
                continue
            file.set_timezones(time_zone)
            
        if self.answer:
            self.answer.set_timezones(time_zone)
                
    def __eq__(self, other):
        if isinstance(other, Task):
            if self.id == other.id and self.description == other.description and self.points == other.points and self.assignment_id == other.assignment_id and self.number == other.number:
                return True
        
        return False

    def __str__(self):
        attr_list = [a for a in dir(self) if not callable(a) and not a.startswith("__")]
        return ", ".join(attr_list)

    def __repr__(self):
        
        return ", ".join(["id: ", str(self.id),"assig_id: ", str(self.assignment_id) ,"number: ", str(self.number), "descrip: ", str(self.description), "points: ", str(self.points), "files: ", str(self.files), "answer: ", str(self.answer)])
        

class Answer(DomainBase):
    def __init__(self, id:int, description: str, reveal:datetime.datetime, files:list, time_zone = "UTC"):
        self.type="answer"
        self.id = int(id)
        if reveal is not None:
            self.reveal = pytz.timezone(time_zone).localize(reveal)
        else:
            self.reveal = None
        self.description = description
        if files:
            self.files = files
        else:
            self.files = []


    # def __hash__(self):
    #     attr_list = [a for a in dir(self) if not callable(a) and not a.startswith("__")]
    #     return hash(tuple(attr_list))
    def __eq__(self, other):
        if not isinstance(other, Answer):
            return False
        return other.id == self.id and other.description == self.description and self.files == other.files

    def __str__(self):
        file_str = ""
        for f in self.files:
            file_str+=", "+str(f)
        return "id: "+str(self.id)+" desc "+self.description +"\t files: " +file_str
    def set_timezones(self, time_zone:str):
        for file in self.files:
            if not file:
                continue
            file.set_timezones(time_zone)
        if self.reveal:
            self.reveal = self.reveal.astimezone(pytz.timezone(time_zone))
    
    def __repr__(self):
        return str(self)


class File(DomainBase):
    def __init__(self, id:int, name:str, date:datetime.datetime, time_zone = "UTC"):
        self.type="file"
        if id is None:
            raise ValueError("id can't be null")

        self.id = int(id)
        self.name = name
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)
        else:
            self.date = date

    def set_timezones(self, time_zone:str):
        self.date = self.date.astimezone(pytz.timezone(time_zone))

    
    def __repr__(self):
        return "id: "+str(self.id)+" name: "+self.name

    def __str__(self):
        return self.name
    def __eq__(self, other):
        if not isinstance(other, File):
            return False
        return self.name == other.name and self.id == other.id 
    


