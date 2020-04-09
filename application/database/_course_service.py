from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from string import ascii_uppercase
from random import choice
from application.domain.course import Course
from application.domain.assignment import Assignment, Task
from datetime import datetime
def random_string(length: int):
    chars = ascii_uppercase
    result = ""
    for i in range(length):
        result+= choice(chars)
    return result

def set_assignments(self, course: Course, for_student = True):
    if course is None:
        return
    j = self.assignment.join(self.task)
    sql = select([self.assignment, self.task]).select_from(j).where(self.assignment.c.course_id == course.id).order_by(self.assignment.c.deadline, self.task.c.id) #todo nulls last
    if for_student:
        sql = sql.where(self.assignment.c.reveal < func.now())
        
    with self.engine.connect() as conn:
        
        rs = conn.execute(sql)
        
        a = {}
        for row in rs:
            if row is None:
                continue
            assig_id = row[self.assignment.c.id]
            if a.get(assig_id) is None:
                assig = Assignment(row[self.assignment.c.id],row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], [Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id])])
                a[assig_id] = assig
            else:
                a[assig_id].tasks.append(Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id]))
    
    course.assignments = list(a.values())
        



def select_course_details(self, course_id, student_id, is_student = True):
    j = self.course.join(self.course_student)
    if is_student:
        sql = select([self.course]).select_from(j).where( (self.course_student.c.student_id == student_id) & (self.course.c.id == course_id))
    else:
        sql = select([self.course]).where( (self.course.c.teacher_id == student_id) & (self.course.c.id == course_id))

    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        if row is None:
            rs.close()
            return None     
        c = Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], id=row[self.course.c.id])
        rs.close()


    return c



def insert_course(self, course, teacher_id):
    code = random_string(8)
    sql = select([self.course.c.code]).where(self.course.c.code==code)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        while row is not None:
            rs.close()
            print("duplicate code")
            code = random_string(8)
            rs = conn.execute(sql)
            row = rs.fetchone()
        rs.close()
        sql =self.course.insert().values(teacher_id=teacher_id, name=course.name, description=course.description, code=code, end_date = course.end_date)
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        rs.close()
        return id, code

def select_courses_teacher(self, teacher_id):
    sql = select([self.course]).where(self.course.c.teacher_id== teacher_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        courses = []
        for row in rs:
            courses.append(Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], code=row[self.course.c.code], id = row[self.course.c.id]))
        rs.close()
    return courses


def select_courses_student(self, student_id):
    j = self.course.join(self.course_student)
    sql = select([self.course]).select_from(j).where(self.course_student.c.student_id == student_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        courses = []
        for row in rs:
            courses.append(Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], id=row[self.course.c.id]))
        rs.close()
    return courses

def enlist_student(self, code:str , student_id):
    sql = select([self.course.c.id]).where(self.course.c.code == code)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        rs.close()
        if row is None:
            raise ValueError("invalid code")
        course_id = row[self.course.c.id]
        
        sql = self.course_student.insert().values(student_id=student_id, course_id=course_id)
        conn.execute(sql)

def select_students(self, course_id, teacher_id):
    j = self.course.join(self.course_student).join(self.account)
    sql = select([self.course.c.teacher_id, self.account.c.first_name, self.account.c.last_name]).select_from(j).where(self.course.c.id == course_id)
    with self.engine.connect() as conn:
        results = []
        rs = conn.execute(sql)
        for row in rs:
            if row[self.course.c.teacher_id] != teacher_id:
                raise ValueError("Unauthorized access")
            results.append((row[self.account.c.last_name]+", "+row[self.account.c.first_name], 0 , 0))
        rs.close()

    return results




