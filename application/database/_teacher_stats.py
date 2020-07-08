import datetime

from sqlalchemy import func
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from werkzeug.utils import secure_filename
from sqlalchemy.engine import Connection
from application.domain.assignment import Assignment, File, Submit, Task


def count_students(self, conn: Connection,  teacher_id:int, course_id:int=None) -> tuple:
    """placeholder for student counts, currenylu returns tuples

    Arguments:
        teacher_id {int} -- [description]

    Keyword Arguments:
        course_id {int} -- [description] (default: {None})

    Returns:
        [type] -- [description]
    """
    self.logger.info("Fetching student counts for course: %s for user %s", (course_id or "all"), teacher_id)
    if course_id:
        sql = select([self.course_student.c.course_id, func.count( self.course_student.c.student_id)]).where(self.course_student.c.course_id == course_id)
    else:    
        j = self.course_student.join(self.course)
        sql = select([self.course_student.c.course_id, func.count( self.course_student.c.student_id)]).select_from(j).group_by(self.course_student.c.course_id).where(self.course.c.teacher_id == teacher_id)
    with conn.begin():
        rs = conn.execute(sql)
        
        res = rs.fetchall()
        

        return res
