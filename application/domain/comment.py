import datetime
import json
import pytz
class CommentJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)


class Comment():
    def __init__(self, id:int, owner_id:int, text:str, visible:bool,  date:datetime.datetime, modified:datetime.datetime, time_zone = "UTC", owner_str:str=""):
        self.id = int(id)
        self.owner_id=int(owner_id)
        self.text = text
        self.visible = visible
        self.date = None
        self.owner_str=owner_str
        if date is not None:
            self.date = pytz.timezone(time_zone).localize(date)
        self.modified = None
        if modified is not None:
            self.modified = pytz.timezone(time_zone).localize(date)


    def __repr__(self):
        return "id: "+str(self.id)+" owner_id "+str(self.owner_id)+" text "+self.text+" visible: "+str(self.visible)
    def __str__(self):
        return self.text

    def set_timezones(self, time_zone:str):
        if self.date:
            self.date = self.date.astimezone(pytz.timezone(time_zone))
        if self.modified:
            self.modified = self.modified.astimezone(pytz.timezone(time_zone))