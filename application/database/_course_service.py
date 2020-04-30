from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.exc import IntegrityError
from string import ascii_uppercase
from random import choice
from application.domain.course import Course
from application.domain.assignment import Assignment, Task
from datetime import datetime

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

def set_assignments(self, course: Course, for_student = True):
    """Set Assignment fields for the given course. If for:student is provided, only assignment where reveal date is past will be added

    Arguments:
        course {Course} -- [course object to modify. Needs to have id field set]

    Keyword Arguments:
        for_student {bool} -- [wheather query is for student or teacher, students can't see assignment before their reveal date] (default: {True})
    """
    print("Seting assignments for course: "+str(course.id))
    if course is None:
        return
    j = self.assignment.join(self.task)
    sql = select([self.assignment, self.task]).select_from(j).where(self.assignment.c.course_id == course.id).order_by(self.assignment.c.deadline, self.task.c.id) 
    if for_student:
        sql = sql.where(self.assignment.c.reveal < func.now())
        
    with self.engine.connect() as conn:
        
        rs = conn.execute(sql)
        
        a = {}
        
        for row in rs:
            

            if row is None:
                print("found no assignments matching parameters")
                continue
            assig_id = row[self.assignment.c.id]
            
            if a.get(assig_id) is None:
                assig = Assignment(row[self.assignment.c.id],row[self.assignment.c.name], row[self.assignment.c.reveal], row[self.assignment.c.deadline], [Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id])])
                a[assig_id] = assig
            else:
                a[assig_id].tasks.append(Task(row[self.task.c.id], row[self.task.c.points], row[self.task.c.description], assignment_id=row[self.assignment.c.id]))
    
    course.assignments = list(a.values())
        



def select_course_details(self, course_id:int, user_id:int, is_student:bool = True) -> Course:
    """Return the course object for the given id. For student must be set accuratelly, as this function checks if the user has rights to see the course or not
    For teachers they can see only courses they own, for student only courses they have signed up for

    Arguments:
        course_id {int} -- [description]
        user_id {int} -- [description]

    Keyword Arguments:
        is_student {bool} -- [description] (default: {True})

    Returns:
        Course -- [course object with all simple fields set, including teacher id Assignments not set]
    """
    j = self.course.join(self.course_student)
    if is_student:
        sql = select([self.course]).select_from(j).where( (self.course_student.c.student_id == user_id) & (self.course.c.id == course_id))
    else:
        sql = select([self.course]).where( (self.course.c.teacher_id == user_id) & (self.course.c.id == course_id))

    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        if row is None:
            rs.close()
            return None     
        c = Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], id=row[self.course.c.id], code = row[self.course.c.code], teacher_id = row[self.course.c.teacher_id] )
        rs.close()
    return c



def insert_course(self, course:Course, teacher_id:int) -> tuple:
    """Insert the given course object to the database
        returns generated pk, code
    Arguments:
        course {Course} -- [description]
        teacher_id {int} -- [description]

    Returns:
        tuple -- [id, code]
    """
    code = random_string(8)
    sql = select([self.course.c.code]).where(self.course.c.code==code)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        while row is not None:
            
            print("duplicate code")
            code = random_string(8)
            rs = conn.execute(sql)
            row = rs.first()
        
        sql =self.course.insert().values(teacher_id=teacher_id, name=course.name, description=course.description, code=code, end_date = course.end_date)
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        rs.close()
        return id, code

def select_courses_teacher(self, teacher_id:int) -> list:
    """Returns a list of course objects for the given id (meaning courses the teacher owns), only simple details are added

    Arguments:
        teacher_id {int} -- [description]

    Returns:
        list -- [list of Course objects]
    """

    sql = select([self.course]).where(self.course.c.teacher_id== teacher_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        courses = []
        for row in rs:
            
            courses.append(Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], code=row[self.course.c.code], id = row[self.course.c.id], teacher_id=row[self.course.c.teacher_id]))
            j = self.assignment.outerjoin(self.course)
            sql = select([func.min(self.assignment.c.deadline)]).select_from(j).where((self.course.c.id == row[self.course.c.id]) & (self.assignment.c.deadline > func.now()))
            rs = conn.execute(sql)
            min = rs.first()[0] 
            courses[len(courses)-1].min = min

    return courses


def select_courses_student(self, student_id:int) -> list:
    """[Returns a list of course objects for the given id (meaning courses the student has signed up for), only simple details are added
]

    Arguments:
        student_id {int} -- [student it]

    Returns:
        [list] -- [list of Course objects]
    """

    j = self.course.join(self.course_student)
    sql = select([self.course]).select_from(j).where(self.course_student.c.student_id == student_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        courses = []
        for row in rs:
            courses.append(Course(row[self.course.c.name], row[self.course.c.description], row[self.course.c.end_date], id=row[self.course.c.id], teacher_id=row[self.course.c.teacher_id]))
        rs.close()
    return courses

def enlist_student(self, code:str , student_id:int):
    """Add student sign up for the given course code

    Arguments:
        code {str} -- [course code]
        student_id {int} -- [id]

    Raises:
        ValueError: [in case of invalid code]
        IntegrityError: [in case of duplicate sign up]
    """    
    sql = select([self.course.c.id]).where(self.course.c.code == code)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        rs.close()
        if row is None:
            raise ValueError("invalid code")
        course_id = row[self.course.c.id]
        
        sql = self.course_student.insert().values(student_id=student_id, course_id=course_id)
        try:
            conn.execute(sql)
        except IntegrityError as r:
            raise r

def select_students(self, course_id:int, teacher_id:int):
    """Select all students in the given course, temp fix

    Arguments:
        course_id {int} -- [description]
        teacher_id {int} -- [description]

    Raises:
        ValueError: [in case teacher doesn't own the course he's trying to access]

    Returns:
        [type] -- [description]
    """

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




