from __future__ import annotations
from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from string import ascii_uppercase
from random import choice
from application.domain.course import Course
from application.domain.account import Account
from application.domain.assignment import Assignment, Task
from datetime import datetime
from typing import List, TYPE_CHECKING
from .data import utcnow
if TYPE_CHECKING:
    from .data import data


def random_string(length: int) -> str:
    """returns random string length n of uppercase ascii characters

    Arguments:
        length {int} -- [string length]

    Returns:
        str -- [random string]
    """
    chars = ascii_uppercase
    result = ""
    for _ in range(length):
        result+= choice(chars)
    return result

def set_assignments(self:data, conn: Connection,  course: Course, for_student = True, set_files=False):
    """Set Assignment fields for the given course. If for_student is provided, only assignment where reveal date is past will be added
        Doesn't set file info
    Arguments:
        course {Course} -- [course object to modify. Needs to have id field set]

    Keyword Arguments:
        for_student {bool} -- [wheather query is for student or teacher, students can't see assignment before their reveal date] (default: {True})
    """
    
    if course is None:
        self.logger.warning("Null course?")
        return
    self.logger.info("Seting assignments for course: %s (for student %s)",str(course.id), for_student)
    j = self.assignment.join(self.task)
    sql = select([self.assignment, self.task]).select_from(j).where(self.assignment.c.course_id == course.id).order_by(self.assignment.c.deadline, self.task.c.number) 
    if for_student:
        sql = sql.where(self.assignment.c.reveal < utcnow())
        
    with conn.begin():
        rs = conn.execute(sql)
        a = {}
        for row in rs:
            if row is None:
                self.logger.info("found no assignments matching parameters")
                continue
            assig_id = row[self.assignment.c.id]
            if a.get(assig_id) is None:
                assig = Assignment(row[self.assignment.c.id],row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], [], files=[])
                a[assig_id] = assig
                if set_files:
                    assig.files=self.select_file_details(conn, assignment_id=assig.id)

            t = Task(row[self.task.c.id],row[self.task.c.number], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id], files=[])
            if set_files:
                t.files=self.select_file_details(conn, task_id=t.id)

            a[assig_id].tasks.append(t)
    
    course.assignments = list(a.values())
        

def update_course(self:data, conn: Connection, user_id:int, course_id:int, values:dict) -> None:
    sql = self.course.update().values(values).where((self.course.c.teacher_id == user_id) & (self.course.c.id==course_id))
    self.logger.info("user %s attempting update on course %s, with values %s", user_id, course_id, values)
    with conn.begin():
        rs = conn.execute(sql)
        if rs.rowcount ==1:
            self.logger.info("Update success")
        else:
            self.logger.warning("Update failure, %s rows changed", rs.rowcount)

def select_course_details(self:data, conn: Connection,  course_id:int, user_id:int) -> Course:
    """Return the course object for the given id. For student doesn't matter, but is here cause I'm lazy (used to check if student has rights)

    Arguments:
        course_id {int} -- [description]
        user_id {int} -- [description]

    Keyword Arguments:
        is_student {bool} -- [doesn't matter] (default: {True})

    Returns:
        Course -- [course object with all simple fields set, including teacher id Assignments not set]
    """
    j = self.course.join(self.account)
    sql = select([self.course, self.account.c.first_name, self.account.c.last_name]).select_from(j).where( self.course.c.id == course_id)

    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Fetching course %s for user %s", course_id, user_id)
        row = rs.fetchone()
        if row is None or row[self.course.c.id]==None:
            rs.close()
            self.logger.warning("found no course matching parameters")
            return None   
        teacher_name = row[self.account.c.last_name]+", "+row[self.account.c.first_name]
        c = Course(row[self.course.c.name], row[self.course.c.description], id=row[self.course.c.id], code = row[self.course.c.code], teacher_id = row[self.course.c.teacher_id], teacher_name = teacher_name )
        rs.close()
    return c



def insert_course(self:data, conn: Connection,  course:Course, teacher_id:int) -> tuple:
    """Insert the given course object to the database. Inserted course needs name, desc and abbreviation (rest are ignored)
        returns generated pk, code
    Arguments:
        course {Course} -- [description]
        teacher_id {int} -- [description]

    Returns:
        tuple -- [id, code]
    """
    code = random_string(5)
    sql = select([self.course.c.code]).where(self.course.c.code==code)
    with conn.begin():
        rs = conn.execute(sql)
        row = rs.first()
        self.logger.info("Inserting new course for user %s", teacher_id)
        while row is not None:
            
            self.logger.info("duplicate code")
            code = random_string(5)
            sql = select([self.course.c.code]).where(self.course.c.code==code) #I'm not sure if this is needed
            rs = conn.execute(sql)
            row = rs.first()
        
        sql =self.course.insert().values(teacher_id=teacher_id, name=course.name, description=course.description, code=code, abbreviation = course.abbreviation)
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        self.logger.info("Insertion success! course id: %s code: %s", id, code)
        rs.close()
        return id, code

def select_courses_teacher(self:data, conn: Connection,  teacher_id:int) -> list:
    """Returns a list of course objects for the given id (meaning courses the teacher owns), only simple details are added

    Arguments:
        teacher_id {int} -- [description]

    Returns:
        list -- [list of Course objects]
    """
    self.logger.info("Fetching all courses for user (teacher) %s", teacher_id)
    j = self.course.join(self.account, self.account.c.id==self.course.c.teacher_id)
    sql = select([self.course, self.account.c.last_name, self.account.c.first_name]).select_from(j).where(self.course.c.teacher_id== teacher_id)
    sql = sql.order_by(self.course.c.creation_date.desc())
    with conn.begin():
        rs = conn.execute(sql)
    courses = []
    i=0
    for row in rs:
        i+=1
        name = row[self.account.c.last_name]+", "+row[self.account.c.first_name]
        course_id=row[self.course.c.id]
        c = Course(row[self.course.c.name], row[self.course.c.description],id=course_id , teacher_id=row[self.course.c.teacher_id], teacher_name=name, code=row[self.course.c.code], abbreviation=row[self.course.c.abbreviation])
        courses.append(c)
        
        

        
    self.logger.info("Found %s courses", i)
    return courses



def select_courses_student(self:data, conn: Connection,  student_id:int) -> list:
    """[Returns a list of course objects for the given id (meaning courses the student has signed up for), only simple details are added]
    Arguments:
        student_id {int} -- [student it]

    Returns:
        [list] -- [list of Course objects]
    """

    j = self.course.join(self.course_student).join(self.account, self.account.c.id==self.course.c.teacher_id)
    sql = select([self.course, self.course_student.c.timestamp, self.account.c.last_name, self.account.c.first_name]).select_from(j).where(self.course_student.c.student_id == student_id)
    sql = sql.order_by(self.course_student.c.timestamp.desc())
    self.logger.info("Fetching all courses for user (student) %s", student_id)
    with conn.begin():
        rs = conn.execute(sql)
    courses = []
    i=0
    for row in rs:
        i+=1
        name = row[self.account.c.last_name]+", "+row[self.account.c.first_name]
        
        c = Course(row[self.course.c.name], row[self.course.c.description], id=row[self.course.c.id], teacher_id=row[self.course.c.teacher_id], teacher_name=name, code=row[self.course.c.code], abbreviation=row[self.course.c.abbreviation])
        courses.append(c)
        
        
    rs.close()
    self.logger.info("Found %s courses", i)
    return courses

def enlist_student(self:data, conn: Connection,  code:str , student_id:int):
    """Add student sign up for the given course code

    Arguments:
        code {str} -- [course code]
        student_id {int} -- [id]

    Raises:
        ValueError: [in case of invalid code]
        IntegrityError: [in case of duplicate sign up]
    """    
    code = code.upper()
    sql = select([self.course.c.id]).where(self.course.c.code == code)
    with conn.begin():
        self.logger.info("Attempting enlisting student %s with code", student_id, code)
        rs = conn.execute(sql)
        row = rs.fetchone()
        rs.close()
        
        if row is None:
            self.logger.info("Invalid code")
            raise ValueError("invalid code")
        course_id = row[self.course.c.id]
        self.logger.info("Code %s belongs to %s", code, course_id)
        sql = self.course_student.insert().values(student_id=student_id, course_id=course_id)
        try:
            self.logger.info("Attempting signup")
            conn.execute(sql)
            self.logger.info("Success!")
        except IntegrityError as r:
            self.logger.info("duplicate signup")
            raise r

def select_students(self:data, conn: Connection,  course_id:int, teacher_id:int):
    """Select all students in the given course

    Arguments:
        course_id {int} -- [description]
        teacher_id {int} -- [description]

    Raises:
        ValueError: [in case teacher doesn't own the course he's trying to access]

    Returns:
        [list[Account]] -- [results]
    """
    
    j = self.course.outerjoin(self.course_student).join(self.account)
    sql = select([self.course.c.teacher_id, self.account.c.id, self.account.c.username, self.account.c.first_name, self.account.c.last_name]).select_from(j).where(self.course.c.id == course_id).order_by(self.account.c.first_name, self.account.c.last_name)
    self.logger.info("Selecting all students for course %s, for user %s", course_id, teacher_id)
    with conn.begin():
        results = []
        rs = conn.execute(sql)
        for row in rs:
            if row[self.course.c.teacher_id] != teacher_id:
                self.logger.warning("User %s tried to access a course (id: %s) not belonging to them",teacher_id, course_id)
                raise ValueError("Unauthorized access")
            acc = Account(row[self.account.c.id], row[self.account.c.username],"USER", row[self.account.c.first_name], row[self.account.c.last_name], None, None)
            results.append(acc)
        rs.close()

    return results




