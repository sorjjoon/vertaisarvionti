
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)
from datetime import datetime

from werkzeug import secure_filename
from application.domain.assignment import File

def check_user_rights(self, user_id, file_id, to_delete = False):
    sql = select([self.file.c.id]).where(self.file_id == file_id)
    if to_delete:        
        sql = sql.where(self.file.c.owner_id == owner_id)
    else:
        j = self.file.join(self.assignment).join(self.course_student)
        sql = sql.where()

def update_file(self, user_id,files, submit_id=None, assignment_id=None, task_id=None): #TODO validate user has rights
    if submit_id is None and assignment_id is None and task_id is None:
        return

    sql = self.file.delete().where(self.file.c.owner_id == user_id)
    if submit_id:
        sql = sql.where(self.file.c.submit_id == submit_id)
    if assignment_id:
        sql = sql.where(self.file.c.assignment_id == assignment_id)
    if task_id:
        sql = sql.where(self.file.c.task_id == task_id)
        
    with self.engine.connect() as conn:
        conn.execute(sql)
        insert_dics = [{self.file.c.binary_file: file.read(), self.file.c.name: secure_filename(file.filename), self.file.c.submit_id: submit_id, self.file.c.assignment_id: assignment_id, self.file.c.task_id: task_id} for file in files]
        sql = self.file.insert().values(insert_dics)    

def select_file_details(self, assignment_id=None, task_id=None, file_id = None):
    if assignment_id is None and task_id is None and file_id is None: #without this would return everything in case both None
        return None

    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date])
    if assignment_id is not None:
        sql = sql.where(self.file.c.assignment_id == assignment_id)

    if task_id is not None:
        sql = sql.where(self.file.c.task_id == task_id)
    
    if file_id is not None:
        sql = sql.where(self.file.c.id == file_id)

    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        results = []
        for row in rs:
            results.append(File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        rs.close()

    return results

def delete_file(self, file_id, owner_id):
    sql = self.file.delete().where(self.file.c.id == file_id & self.file.c.owner_id == owner_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        count = rs.rowcount
        rs.close()
        return count

def get_file(self, file_id):
    sql = select([self.file.c.binary_file, self.file.c.name]).where(self.file.c.id == file_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        if row is None:
            rs.close()
            return None

        file = row[self.file.c.binary_file]
        name = row[self.file.c.name]
        rs.close()

        
    return file, name