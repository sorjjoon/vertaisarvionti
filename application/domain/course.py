import datetime
import pytz
class Course():
    def __init__(self, name, description, code=None, id=None, assignments = [], min=None, time_zone = "UTC", teacher_id = None, student_count = 0, teacher_name = "", abbreviation=None):
        self.name=name
        self.description=description
        
        self.code = code
        self.id = id
        self.assignments = assignments
        self.set_timezones(time_zone)
        self.teacher_id =teacher_id
        self.min = min
        self.student_count = student_count
        self.teacher_name = teacher_name
        self.abbreviation = abbreviation

    def __eq__(self, other):
        if isinstance(other, Course):
            if self.name == other.name:
                if self.description == other.description:
                    if self.id == other.id:
                        if self.abbreviation == other.abbreviation:
                            if self.teacher_name == other.teacher_name:
                                return True
        return False

    def __repr__(self):
        return str(self)
        
    def __str__(self):
        return "id: "+str(self.id)+" name: "+str(self.name)+ " description "+str(self.description)+" code, "+str(self.code)+", teacher id: "+str(self.teacher_id)+", abbreviation: "+str(self.abbreviation)+", teacher_name "+str(self.teacher_name)

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
    
