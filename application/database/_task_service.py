from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)
import datetime
from werkzeug.utils import secure_filename
from application.domain.assignment import Assignment, Task, Submit, File
from sqlalchemy import func



def set_task_answer(task: Task, for_student = True):
    j = self.answer.outerjoin(self.file)
    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date]).select_from(j).where(self.answer.c.task_id ==task.id)
    if for_student:
        sql = sql.where(self.answer.c.reveal > func.now())
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        files = []
        for row in rs:
            files.append(File(row[self.file.c.id], row[self.file.c.upload_date]))
    task.answers = files



def update_answer(user_id, task_id, files, description, reveal= func.now()):
    sql = select(self.answer.c.id).where(self.answer.c.task_id == task_id)
    with self.engine.connect as conn:
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            sql = self.answer.insert().values(reveal=reveal, task_id=task_id, description = description)
            rs = conn.execute(sql)
            id = rs.inserted_primary_key[0]
        else:
            id = row[self.answer.c.id]
            sql = update(self.answer).values(reveal=reveal, task_id=task_id, description = description)
        
        self.update_file(user_id, files, answer_id = id)
    return id
