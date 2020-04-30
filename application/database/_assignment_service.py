from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)
import datetime
import pytz
from sqlalchemy import func
from werkzeug.utils import secure_filename
from application.domain.assignment import Assignment, Task, Submit, File

def set_answers(self, assignment: Assignment, for_student=False) -> None:
    """useless?

    Arguments:
        assignment {Assignment} -- [description]

    Keyword Arguments:
        for_student {bool} -- [description] (default: {False})
    """
    for t in assignment.tasks:
        self.set_answer(t, for_student = for_student)

def set_submits(self, assignment: Assignment, user_id:int, task_id:int=None) -> None:
    """Set submit fields in the given assignment (submits will contain files as well)
    if tasks are set, set task done status as well

    Arguments:
        assignment {Assignment} -- [assignemnt to modify]
        user_id {int} -- [user id]

    Keyword Arguments:
        task_id {int} -- [if provided, will only fetch submit data for the given task] (default: {None})
    """
    j = self.task.outerjoin(self.submit).outerjoin(self.file)
    sql = select([self.task.c.id, self.submit, self.file.c.id, self.file.c.name, self.file.c.upload_date]).select_from(
        j).where(self.task.c.assignment_id == assignment.id).order_by(self.task.c.id)
    sql = sql.where(self.submit.c.owner_id == user_id)
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
                a[row[self.submit.c.id]] = Submit(row[self.submit.c.id], row[self.submit.c.last_update], row[self.task.c.id], [
                                                  File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date])])
            else:
                a.get(row[self.submit.c.id]).files.append(
                    File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))

        if a.values:
            assignment.submits = list(a.values())
        else:
            assignment.submits = []

        rs.close()
    for t in assignment.tasks:
        if b.get(t.id) is not None:
            t.done = True

def select_assignment(self, assignment_id:int, task_id:int=None, for_student:bool=False) -> Assignment:
    """Select assignment given it's id only assignment where reveal date is past will be added
    if task id is given, only this task will be set
    Note: submit data is no set in this function

    Arguments:
        assignment_id {int} -- [assingment id]

    Keyword Arguments:
        task_id {int} -- [task id, ignored if not defined (or set to null)] (default: {None})
        task_id {bool} -- [show non revealed] (default: {None})
    Returns:
        [Assignment] -- [returns all information in the Assignment object]
    """
    j = self.assignment.join(self.task)
    
    sql = select([self.assignment, self.task]).select_from(
        j).where(self.assignment.c.id == assignment_id)
    if task_id is not None:
        sql = sql.where(self.task.c.id == task_id)
    if for_student:
        sql = sql.where(func.now() > self.assignment.c.reveal)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        assig = None
        for row in rs:
            if assig is None:
                
                assig = Assignment(row[self.assignment.c.id], row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], [
                                   Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], files=[], assignment_id=row[self.assignment.c.id])], files=[])
                
            else:
                assig.tasks.append(Task(row[self.task.c.id], row[self.task.c.points],
                                        row[self.task.c.description], assignment_id=row[self.assignment.c.id]))

        rs.close()
        if assig is None:
            return assig
        sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date]).where(
            (self.file.c.assignment_id == assignment_id) & ((self.file.c.submit_id == None) & (self.file.c.task_id == None)))
        rs = conn.execute(sql)
        for row in rs:
            if row is None:
                continue
            assig.files.append(
                File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        rs.close()
    return assig



def insert_assignment(self, user_id:int, course_id:int, name:str, deadline: datetime, reveal: datetime, files:list) -> int:
    """Inserted the given fields to the database. If Reveal is null, current time is used
    The files given need to be able to read with.read, and need the filename property. seek(0) is called before reading
    All given dates are converted to UTC before insert (so they shouldn't be naive)

    Arguments:
        user_id {int} -- [user id]
        course_id {int} -- [course id]
        name {str} -- [name]
        deadline {datetime} -- [deadline]
        reveal {datetime} -- [reveal]
        files {list} -- [description]

    Returns:
        [id] -- [pk of the inserted assignment]
    """
    d = None
    if deadline is not None:
        d = deadline.astimezone(datetime.timezone.utc)

    if reveal is not None:
        r = reveal.astimezone(datetime.timezone.utc)
    else:
        r = datetime.datetime.utcnow()

    sql = self.assignment.insert().values(
        deadline=d, reveal=r, course_id=course_id, name=name)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]

        for file in files:
            if file is None:
                continue
            name = secure_filename(file.filename)
            file.seek(0)
            sql = self.file.insert().values(binary_file=file.read(), assignment_id=id,
                                            name=name, task_id=None, owner_id=user_id)
            conn.execute(sql)
        rs.close()
    return id


def insert_task(self, user_id:int, assignment_id:int, description:str, points:int, files:list) -> int:
    """
    insert the given info to the database
        The files given need to be able to read with.read, and need the filename property. seek(0) is called before reading
    All given dates are converted to UTC before insert (so they shouldn't be naive)
    Arguments:
        user_id {int} -- [user id]
        assignment_id {int} -- [assignment if]
        description {str} -- [descpriotoin]
        points {int} -- [points]
        files {list} -- [files]

    Returns:
        int -- [task id]
    """
    sql = self.task.insert().values(description=description,
                                    points=points, assignment_id=assignment_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        for file in files:
            print("insert_task adding files")
            if file is None:
                continue
            name = secure_filename(file.filename)
            file.seek(0)
            sql = self.file.insert().values(binary_file=file.read(), name=name,
                                            assignment_id=assignment_id, task_id=id, owner_id=user_id)
            conn.execute(sql)
        rs.close()
    return id

