
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)

from werkzeug.utils import secure_filename
from sqlalchemy import func
from application.domain.assignment import Assignment, Task, Submit
    
def select_task(self, task_id):
    j = self.task.outerjoin(self.submit).outerjoin(self.file).outerjoin(self.file.c.task_id, self.file.id)
    sql = select([self.task.c.id,self.submit, self.file.c.id]).select_from(j).where(self.task.c.id == task_id)

    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        task = None
        for row in rs:
            if task is None:
                task = Task(row[self.task.c.id],row[self.task.c.points], row[self.task.c.description], )


def update_submit(self,user_id, task_id, assignment_id, files):
    sql = select([self.submit.c.id]).where((self.submit.c.task_id == task_id) & (self.submit.c.owner_id==user_id))
    with self.engine.connect() as conn:
        row = conn.execute(sql).first()
        if row is None:
            sql = self.submit.insert().values(owner_id = user_id, task_id = task_id)
            submit_id = conn.execute(sql).inserted_primary_key[0]
        else:
            
            submit_id = row[self.submit.c.id]
            sql = update(self.submit).values(last_update = func.now())
            
            conn.execute(sql)
        
        self.update_file(user_id, files, submit_id=submit_id, assignment_id = assignment_id)
