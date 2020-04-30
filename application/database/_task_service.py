from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)
import datetime
from werkzeug.utils import secure_filename
from application.domain.assignment import Assignment, Task, Submit, File, Answer
from sqlalchemy import func
import pytz


def set_task_answer(self, task: Task, for_student = True) -> None:
    """Set the given task objects answer to match the database
    For a task with no answer, answer set to null

    Arguments:
        task {Task} -- [task must have set id]

    Keyword Arguments:
        for_student {bool} -- [If the answer is fetched for a teacher or student, students can't see answers before their reveal date] (default: {True})

    """
    j = self.answer.outerjoin(self.file)
    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date]).select_from(j).where(self.answer.c.task_id ==task.id)
    if for_student:
        sql = sql.where(self.answer.c.reveal > func.now())
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        files = []
        for row in rs:
            files.append(File(row[self.file.c.id], self.file.c.name, row[self.file.c.upload_date]))
        sql = select([self.answer]).where(self.answer.c.task_id == task.id)
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            return None
        id = row[self.answer.c.id]
        desc = row[self.answer.c.description]
        reveal = row[self.answer.c.reveal]
        task.answer = Answer(id, desc, reveal, files)



def update_answer(self, user_id, task_id, files, description, reveal= datetime.datetime.utcnow()):
    sql = select([self.answer.c.id]).where(self.answer.c.task_id == task_id)
    print("updating answer for user "+str(user_id))
    reveal = reveal.astimezone(pytz.utc)
    with self.engine.connect() as conn:
        print("checking for old answer")
        rs = conn.execute(sql)
        row = rs.first()

        if row is None:
            print("no old answer found, creating new entry")
            sql = self.answer.insert().values(reveal=reveal, task_id=task_id, description = description)
            rs = conn.execute(sql)
            id = rs.inserted_primary_key[0]
        else:

            id = row[self.answer.c.id]
            print("old answer with id "+str(id)+" found, updating values")
            sql = update(self.answer).values(reveal=reveal, task_id=task_id, description = description).where(self.answer.c.id == id)
            conn.execute(sql)
        
        self.update_file(user_id, files, answer_id = id)
    return id
