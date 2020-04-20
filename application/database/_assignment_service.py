from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin )
import datetime
from werkzeug import secure_filename
from application.domain.assignment import Assignment, Task, Submit, File



def set_submits(self, assignment:Assignment, task_id= None):
    j = self.task.outerjoin(self.submit).outerjoin(self.file)
    sql = select([self.task.c.id,self.submit, self.file.c.id, self.file.c.name, self.file.c.upload_date]).select_from(j).where(self.task.c.assignment_id ==assignment.id).order_by(self.task.c.id)
    if task_id is not None:
        sql = sql.where(self.task.c.id == task_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        a = {}
        b = {}
        for row in rs:
            if row is None or row[self.submit.c.id] is None:
                continue
            b[row[self.task.c.id]] = True
            if a.get(row[self.submit.c.id]) is None:
                a[row[self.submit.c.id]] = Submit(row[self.submit.c.id],row[self.submit.c.last_update], row[self.task.c.id] ,[File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]) ] )
            else:
                a.get(row[self.submit.c.id]).files.append(File(row[self.file.c.id],row[self.file.c.name], row[self.file.c.upload_date]  ))


        if a.values:
            assignment.submits = list(a.values())
        else:
            assignment.submits = []

        rs.close()
    for t in assignment.tasks:
        if b.get(t.id) is not None:
            t.done = True




def select_assignment(self, assignment_id, task_id = None):
    j = self.assignment.join(self.task)
    sql = select([self.assignment, self.task]).select_from(j).where(self.assignment.c.id ==assignment_id)
    if task_id is not None:
        sql = sql.where(self.task.c.id == task_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        assig = None
        for row in rs:
            if assig is None:
                assig = Assignment(row[self.assignment.c.id],row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], [Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id])])
            else:
                assig.tasks.append(Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id]))

        rs.close()
        if assig is None:
            return assig
        sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date]).where((self.file.c.assignment_id == assignment_id) & ((self.file.c.submit_id == None) & (self.file.c.task_id == None) ))
        rs = conn.execute(sql)
        for row in rs:
            if row is None:
                continue
            print("adding to assig file "+str(row[self.file.c.id]))
            assig.files.append( File(row[self.file.c.id],row[self.file.c.name], row[self.file.c.upload_date]) )
        rs.close()
    return assig



def insert_assignment(self, user_id, course_id, name, deadline: datetime, reveal:datetime, files):
    d = None
    if deadline is not None:
        d = deadline.astimezone(datetime.timezone.utc)

    
    if reveal is not None:
        r = reveal.astimezone(datetime.timezone.utc)
    else:
        r = datetime.datetime.utcnow()

    sql = self.assignment.insert().values(deadline=d, reveal=r, course_id=course_id, name=name)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]

        for file in files:
            if file is None:
                continue
            name = secure_filename(file.filename)
            sql = self.file.insert().values(binary_file=file.read(), assignment_id = id ,name=name, task_id=None, owner_id = user_id)
            conn.execute(sql)
        rs.close()
    return id



def insert_task(self, user_id, assignment_id, description, points, files):
    sql = self.task.insert().values(description = description, points = points, assignment_id = assignment_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        for file in files:
            print("insert_task adding files")
            if file is None:
                continue
            name = secure_filename(file.filename)
            sql = self.file.insert().values(binary_file=file.read(), name=name, assignment_id=assignment_id, task_id=id, owner_id = user_id)
            conn.execute(sql)
        rs.close()
    return id


    


