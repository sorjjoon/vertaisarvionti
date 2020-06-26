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
        j).where(self.task.c.assignment_id == assignment.id).order_by(self.task.c.number)
    sql = sql.where(self.submit.c.owner_id == user_id)
    
    if task_id is not None:
        self.logger.info("Setting submits for assignment %s (task: %s) for user %s ",assignment.id,task_id, user_id)
        sql = sql.where(self.task.c.id == task_id)
    else:
        self.logger.info("Setting submits for assignment %s (task: all) for user %s ",assignment.id, user_id)
    with self.engine.connect() as conn:
        
        rs = conn.execute(sql)
        a = {}
        b = {}
        for row in rs:
            
            if row is None or row[self.submit.c.id] is None:
                continue
            
            b[row[self.task.c.id]] = True
            if a.get(row[self.submit.c.id]) is None:
                if row[self.file.c.id]:
                    files = [File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date])]
                else:
                    files = []
                
                a[row[self.submit.c.id]] = Submit(id=row[self.submit.c.id], date=row[self.submit.c.last_update], task_id=row[self.task.c.id],files=files, description=row[self.submit.c.description])
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

def select_assignment(self, assignment_id:int, task_id:int=None, for_student:bool=False, set_task_files:bool=False) -> Assignment:
    """Select assignment given it's id only assignment where reveal date is past will be added
    if task id is given, only this task will be set. Sets assignment files, but not task files

    Note: submit data is no set in this function

    Arguments:
        assignment_id {int} -- [assingment id]

    Keyword Arguments:
        task_id {int} -- [task id, ignored if not defined (or set to null)] (default: {None})
        for_student {bool} -- [show non revealed] (default: {None})
        for_student {bool} -- [set task files]
    Returns:
        [Assignment] -- [returns all information in the Assignment object]
    """
    j = self.assignment.join(self.task)
    
    self.logger.info("Selecting  assignment %s (task: %s) - (for_student %s)",assignment_id,(task_id or "all") , for_student)
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
            self.logger.debug(str(row))
            if assig is None:
                task = Task(row[self.task.c.id], row[self.task.c.number], row[self.task.c.points], row[self.task.c.description], files=[], assignment_id=row[self.assignment.c.id])
                assig = Assignment(row[self.assignment.c.id], row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], 
                [task], files=[])
                
            else:
                assig.tasks.append(Task(row[self.task.c.id], row[self.task.c.number], row[self.task.c.points],
                                        row[self.task.c.description], assignment_id=row[self.assignment.c.id]))

        rs.close()
        if assig is None:
            return assig
        assig.files=self.select_file_details(assignment_id=assig.id)
        for t in assig.tasks:
            t.files = self.select_file_details(task_id=t.id)
    return assig

def delete_assignment(self, assignment_id):
    """Delete given assignment (delete cascades)
    DOESN'T CHECK USER RIGHTS
    
    Args:
        assignment_id ([type]): [description]
    """
    self.logger.info("Deleting assignment %s ", assignment_id)
    sql = self.assignment.delete().where(self.assignemnt.c.id == assignment_id)
    with self.engine.connect() as conn:
        conn.execute(sql)
        self.logger.info("Deletion success!")

def delete_task(self, task_id):
    """Delete given task (delete cascades)
    DOESN'T CHECK USER RIGHTS

    Args:
        task_id ([type]): [description]
    """
    self.logger.info("Deleting task %s ", task_id)
    sql = self.task.delete().where(self.task.c.id == task_id)
    with self.engine.connect() as conn:
        conn.execute(sql)
        self.logger.info("Deletion success!")

def update_assignment(self, assignment_id:int, name:str=None, deadline: datetime=None, reveal: datetime=None):
    """Update non file parts of an assignment
    Doesn't check user rights

    Args:
        assignment_id (int): [description]
        name (str, optional): [description]. Defaults to None.
        deadline (datetime, optional): [description]. Defaults to None.
        reveal (datetime, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating assignment %s params name: %s, deadline: %s, reveal: %s", assignment_id, deadline, reveal)
    if name==deadline==reveal==None:
        self.logger.info("All params null")    
    sql = self.assignment.update().where(self.assignemnt.c.id == assignment_id)        
    if name:
        sql= sql.values(name=name)
    if deadline:
        sql= sql.values(deadline=deadline)
    if reveal:
        sql= sql.values(deadline=deadline)
    with self.engine.connect() as conn:
        conn.execute(sql)
        self.logger.info("Update success!")
    
def update_task(self, task_id, description:str=None, points:int=None):
    """Update all non files parts of a task
    Doesn't check user rights
    Args:
        task_id ([type]): [description]
        description (str, optional): [description]. Defaults to None.
        points (int, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating task %s params description: %s, points: %s", task_id, description, points)
    if description==points==None:
        self.logger.info("All params null")
    sql = self.task.update().where(self.task.c.id == task_id)        
    if description is not None:
        sql= sql.values(description=description)

    if points is not None:
        sql= sql.values(points=points)

    with self.engine.connect() as conn:
        conn.execute(sql)
        self.logger.info("Update success!")



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
        self.logger.info("Inserting  assignment for user %s (course %s) ", user_id, course_id)
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        self.logger.info("Insert success! assignment id: %s",id)
        self.insert_files(user_id, files, assignment_id=id, task_id=None)
       
        rs.close()
    return id


def insert_task(self, user_id:int, number:int, assignment_id:int, description:str, points:int, files:list) -> int:
    """
    insert the given info to the database
        The files given need to be able to read with.read, and need the filename property. seek(0) is called before reading
    All given dates are converted to UTC before insert (so they shouldn't be naive)
    Arguments:
        user_id {int} -- [user id]
        number {int} -- [task number]
        assignment_id {int} -- [assignment if]
        description {str} -- [description]
        points {int} -- [points]
        files {list} -- [files]

    Returns:
        int -- [task id]
    """
    sql = self.task.insert().values(description=description, number=number,
                                    points=points, assignment_id=assignment_id)
    with self.engine.connect() as conn:
        self.logger.info("Inserting task for assignment %s for user %s  ",assignment_id, user_id)
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        self.logger.info("Insert success! task id: %s",id)

        self.insert_files(user_id,  files, assignment_id=assignment_id, task_id=id)
        
            
        rs.close()
    return id

