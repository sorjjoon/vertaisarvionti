import datetime

import pytz
from .assignment import File
from .base import DomainBase



class Comment(DomainBase):
    def __init__(self, id: int, owner_id: int, text: str, reveal: datetime.datetime,  date: datetime.datetime, modified: datetime.datetime, owner_str: str = "", date_str=None, files=None, time_zone="UTC"):
        self.type="comment"
        self.id = int(id)
        self.owner_id = int(owner_id)
        self.text = text
        self.reveal = pytz.timezone(time_zone).localize(reveal)
        self.date = None
        self.owner_str = owner_str
        
        if files:
            self.files = files
        else:
            self.files = []
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)
        self.modified = None
        if modified is not None:
            self.modified = pytz.timezone(time_zone).localize(modified)
        self._set_date_str()
    
    # def __iter__(self):
    #     return iter(["id", "owner_id", "owner_str", "files", "date_str", "text"])

    def __repr__(self):
        return "id: "+str(self.id)+" owner_id "+str(self.owner_id)+" text "+self.text+" visible: "+str(self.reveal)

    def __str__(self):
        return self.text

    def _set_date_str(self):
        self.date_str = str(self.date.strftime("%d.%m, klo %H:%M"))
        if self.modified:
            self.date_str += " (muokattu " + \
                self.modified.strftime("%d.%m, klo %H:%M")+")"

    def set_timezones(self, time_zone: str):
        """set timezone for this object and all it's children (if they have datetime)

        Args:
            time_zone (str): [description]
        """
        self.reveal.astimezone(pytz.timezone(time_zone))
        if self.date:
            self.date = self.date.astimezone(pytz.timezone(time_zone))
        if self.modified:
            self.modified = self.modified.astimezone(pytz.timezone(time_zone))
        
        self._set_date_str()
        for f in self.files:
            f.set_timezones(time_zone)
     
    def __eq__(self, other):
        if not isinstance(other, Comment):
            return False
        if self.id != other.id or self.owner_id != other.owner_id or self.text != other.text or self.reveal != other.reveal or self.date != other.date or self.modified != other.modified or self.owner_str != other.owner_str or self.files != other.files:
            return False
        return True
