from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin )
import datetime
from werkzeug.utils import secure_filename
from application.domain.assignment import Assignment, Task, Submit, File
from sqlalchemy import func

def count_students(self, teacher_id, course_id=None):
    if course_id:
        sql = select([self.course_student.c.course_id, func.count( self.course_student.c.student_id)]).where(self.course_student.c.course_id == course_id)
    else:    
        j = self.course_student.join(self.course)
        sql = select([self.course_student.c.course_id, func.count( self.course_student.c.student_id)]).select_from(j).group_by(self.course_student.c.course_id).where(self.course.c.teacher_id == teacher_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        
        res = rs.fetchall()
        

        return res

