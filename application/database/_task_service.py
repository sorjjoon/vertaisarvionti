import datetime
from typing import List

import pytz
from sqlalchemy import func
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from werkzeug.utils import secure_filename

from application.domain.assignment import (Answer, Assignment, File, Submit,
                                           Task)


def set_task_answer(self, task: Task, for_student=True) -> None:
    """Set the given task objects answer to match the database
    For a task with no answer, answer set to null

    Arguments:
        task {Task} -- [task must have set id]

    Keyword Arguments:
        for_student {bool} -- [If the answer is fetched for a teacher or student, students can't see answers before their reveal date] (default: {True})

    """
    self.logger.info("Setting answer for task %s (for_student - %s)", task.id, for_student)
    j = self.answer.outerjoin(self.file)
    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date, self.answer]
                 ).select_from(j).where(self.answer.c.task_id == task.id)
    if for_student:
        sql = sql.where(self.answer.c.reveal < func.now())
    #First row gives answer details, other give extra files   
    task.answer = None
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        
        
        for row in rs:
            
            if row is None:
                self.logger.info("No answer found (or not revealed)")
                continue
            
            if task.answer is None:
                id = row[self.answer.c.id]
                self.logger.info("Answer found id: %s",id)
                desc = row[self.answer.c.description]
                reveal = row[self.answer.c.reveal]
                task.answer = Answer(id, desc, reveal, [])
            if row[self.file.c.id] is not None:
                task.answer.files.append(
                    File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        if task.answer:  
            self.logger.info("Found %s files for answer %s", len(task.answer.files), task.answer.id)
        else:
            self.logger.info("No answer found (or not revealed)")
        
        
        

def update_answer(self, user_id: int, task_id: int, files: List[File], description: str, files_to_delete=None, reveal: datetime.datetime = pytz.utc.localize(datetime.datetime.utcnow())) -> int:
    """Update the database answer to match. If no answer was submitted, a new one is created. If one is found, it is replaced
        Doesn't check if the user has rights to update the answer
    Arguments:
        user_id {int} -- [description]
        task_id {int} -- [description]
        files {List[File]} -- [description]
        description {str} -- [description]

    Keyword Arguments:
        reveal {datetime.datetime} -- [if this arguments is None, set reveal to be the assignment deadline] (default: {datetime.datetime.utcnow()}) 

    Returns:
        int -- [inserted (or exsisting answer id)]
    """
    
    self.logger.info("Updating answer for task %s for user %s",task_id,str(user_id))
    

    with self.engine.connect() as conn:
        if reveal:
            reveal = reveal.astimezone(pytz.utc)
        else:
            
            j = self.task.join(self.assignment)
            sql = select([self.assignment.c.deadline]).select_from(j).where(self.task.c.id == task_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                self.logger.error("Invalid task id! %s", task_id)
                raise ValueError("Invalid task id!")    
            reveal = row[self.assignment.c.deadline]
            self.logger.info("Setting answer reveal same as assignment deadline %s", reveal)

        sql = select([self.answer.c.id]).where(self.answer.c.task_id == task_id)
        rs = conn.execute(sql)
        row = rs.first()

        if row is None:
            new_answer = True
            self.logger.info("no old answer found, creating new entry")
            sql = self.answer.insert().values(
                reveal=reveal, task_id=task_id, description=description)
            rs = conn.execute(sql)
            id = rs.inserted_primary_key[0]
            self.logger.info("Insert success! id: %s",id)
        else:
            new_answer = False
            id = row[self.answer.c.id]
            self.logger.info("old answer with id "+str(id)+" found, updating values")
            sql = update(self.answer).values(reveal=reveal, task_id=task_id,
                                             description=description).where(self.answer.c.id == id)
            conn.execute(sql)
            self.logger.info("Update success!")
        
        if new_answer:
            self.update_file(user_id, files, answer_id=id)
        else:
            self.update_file(user_id, files, answer_id=id, files_to_delete=files_to_delete)
    return id
