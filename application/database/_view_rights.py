
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from datetime import datetime
from sqlalchemy import func

from werkzeug.utils import secure_filename
from application.domain.assignment import File
from typing import List, Tuple


def check_access_rights(self, user_id:int, role:str, course_id, assignment_id = None, task_id = None) -> bool:
    """Checks if the given user has rights to view selected elements. If multiple are given, checks for all
    currently task_id doesn't check for anything (can be expanded later, if needed)



    Arguments:
        self {data} -- [description]
        user_id {int} -- [description]
        role {str} -- [description]

    Keyword Arguments:
        course_id {[type]} -- [description] (default: {None})
        assignment_id {[type]} -- [description] (default: {None})
        task_id {[type]} -- [description] (default: {None})

    Returns:
        bool -- [description]
    """
    self.logger.info("Checking if %s has rights to course [%s], assignment [%s], task [%s]", user_id, course_id, assignment_id, task_id)
    if course_id==assignment_id==task_id == None:
        self.logger.info("SUCCESS, all params null")
        return True
    with self.engine.connect() as conn: 
        if course_id is not None:       
            sql = select([self.course.c.id]).where(self.course.c.id == course_id)
            if role=="TEACHER":
                sql = sql.where(self.course.c.teacher_id == user_id)
            else:
                j = self.course.join(self.course_student)
                sql = sql.select_from(j).where(self.course_student.c.student_id == user_id)
            row = conn.execute(sql).first()
            if row is None:
                self.logger.warning("FAILURE, student is not signed up, or teacher doesn't own the course")
                return False


        if task_id is not None:
            sql = select([self.task.c.assignment_id]).where(self.task.c.id==task_id)
            row = conn.execute(sql).first()
            if row is None:
                self.logger.warning("FAILURE, task id is invalid")
                return False
            if assignment_id is None:
                assignment_id=row[self.task.c.assignment_id]

            if row[self.task.c.assignment_id] != assignment_id:
                self.logger.warning("FAILURE, Doesn't belong to this assignment")
                return False
            

        if assignment_id is not None and role=="USER": #if role is teacher, we have checked the teacher owns this course
            sql = select([self.assignment.c.id]).where((self.assignment.c.id == assignment_id) & (self.assignment.c.reveal <= func.now()) )
            row = conn.execute(sql).first()
            if row is None:
                self.logger.warning("FAILURE, assignment id is invalid, or the assignment is not revealed")
                return False
    self.logger.info("SUCCESS")
    return True
