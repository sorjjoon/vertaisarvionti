
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
from application.domain.assignment import File

def check_user_delete_rights(self, user_id, file_id, is_teacher=False):
    
    sql = select([self.file.c.id]).where(self.file_id == file_id)        
    sql = sql.where(self.file.c.owner_id == user_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            return False
        
        return True

def check_user_view_rights(self, user_id, file_id, is_teacher=False):
    sql = select([self.file.c.owner_id,self.file.c.assignment_id, self.file.c.submit_id, self.file.c.task_id, self.file.c.answer_id]).where(self.file.c.id == file_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            return False

        if row[self.file.c.owner_id] == user_id:
            return True
        assig_id = row[self.file.c.assignment_id]
        submit_id = row[self.file.c.submit_id]
        task_id = row[self.file.c.task_id]
        answer_id = row[self.file.c.answer_id]

        if answer_id is not None:
            if is_teacher: #shouldn't happen (teacher owns the answer to his own course)
                return False
                # j = self.course.join(self.assignment)
                # sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id)
                # rs = conn.execute(sql)
                # row = rs.first()

                # if row is None:
                #     return False
                
                # return True

            sql = select([self.answer.c.id]).where((self.answer.c.id == answer_id) & (self.answer.c.reveal < func.now()) ) 
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False

            j = self.course.outerjoin(self.assignment).outerjoin(self.course_student)
            sql = select([self.course_student.c.id]).select_from(j).where(self.course_student.c.id == user_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True

        elif submit_id is not None:
            if is_teacher:
                j = self.course.outerjoin(self.assignment)
                sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id & self.course.c.teacher_id == user_id)
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    return False
                return True
            
            sql = select([self.peer.c.id]).where((self.peer.c.submit_id == submit_id) & (self.peer.c.reviewer_id == user_id) )
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True

        else:
            if is_teacher:
                j = self.course.outerjoin(self.assignment)
                sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id & self.course.c.teacher_id == user_id)
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    return False
                return True
            
            
            j = self.course.outerjoin(self.assignment).outerjoin(self.course_student)
            sql = select([self.assignment.c.id]).select_from(j).where(self.assignment.c.id == assig_id & self.course_student.student_id == user_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True
        




def update_file(self, user_id,files, submit_id=None, assignment_id=None, task_id=None, answer_id=None, files_to_delete = []): 
    if submit_id is None and assignment_id is None and task_id is None and answer_id is None:
        return

    sql = self.file.delete().where(self.file.c.owner_id == user_id)
    if submit_id is not None:
        sql = sql.where(self.file.c.submit_id == submit_id)
    if assignment_id is not None:
        sql = sql.where(self.file.c.assignment_id == assignment_id)
    if task_id is not None:
        sql = sql.where(self.file.c.task_id == task_id)
    if answer_id is not None:
        sql = sql.where(self.file.c.answer_id == answer_id)
    if files_to_delete:
        sql = sql.where(self.file.c.id.in_(files_to_delete))

    with self.engine.connect() as conn:
        conn.execute(sql)
        
        insert_dics = [{self.file.c.binary_file: file.read(), self.file.c.owner_id: user_id, self.file.c.name: secure_filename(file.filename), self.file.c.submit_id: submit_id, self.file.c.assignment_id: assignment_id, self.file.c.task_id: task_id} for file in files]
        sql = self.file.insert().values(insert_dics)
        conn.execute(sql)    

def select_file_details(self, assignment_id=None, task_id=None, file_id = None, answer_id=None):
    if assignment_id is None and task_id is None and file_id is None: #without this would return everything in case both None
        return None

    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date])
    if assignment_id is not None:
        sql = sql.where(self.file.c.assignment_id == assignment_id)

    if task_id is not None:
        sql = sql.where(self.file.c.task_id == task_id)
    
    if file_id is not None:
        sql = sql.where(self.file.c.id == file_id)
    if answer_id:
        sql = sql.where(self.file.c.answer_id == answer_id)

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
            return None, None

        file = row[self.file.c.binary_file]
        name = row[self.file.c.name]
        rs.close()

        
    return file, name