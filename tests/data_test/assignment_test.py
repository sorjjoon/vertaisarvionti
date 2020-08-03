
import datetime
import io
import os
import random
import tempfile
import unittest

import pytest
import pytz
from flask import url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)

from application.domain.assignment import Assignment, Task
from application.domain.course import Course


from .db_fixture import (conn, format_error, get_random_unicode, insert_users,
                         insert_random_courses, random_datetime)


def test_simple_assignment(conn, a_files = [], t_files=[]):
    from database import db
    from .course_test import test_course_insert
    id, code = test_course_insert(conn)
    student = db.get_user(conn, "oppilas", "oppilas")
    teacher = db.get_user(conn, "opettaja", "opettaja")

    assert student is not None
    assert teacher is not None

    db.enlist_student(conn, code, student.id)
    
    visible_a_name = get_random_unicode(30)
    reveal = random_datetime()
    deadline = random_datetime(start=reveal)
    
    

    points = random.randint(5, 20)
    t_desc = get_random_unicode(30)
    tasks =[Task(None, 1, points,t_desc, t_files)]
    
    a_id, _ = db.insert_assignment(conn, teacher.id, id, visible_a_name, deadline,reveal, a_files, tasks=tasks)

    a=db.select_assignment(conn, a_id)
    t_id = a.tasks[0].id

    with db.engine.connect() as conn:
        sql = select([db.assignment]).where(db.assignment.c.id == a_id)
        rs = conn.execute(sql)
        row = rs.first()
        assert row is not None
        assert row[db.assignment.c.id] == a_id
        assert row[db.assignment.c.name] == visible_a_name
        assert pytz.utc.localize(row[db.assignment.c.deadline]) == deadline
        assert pytz.utc.localize(row[db.assignment.c.reveal]) == reveal

        sql = select([db.task]).where(db.task.c.id == t_id)
        rs = conn.execute(sql)
        row = rs.first()

        assert row is not None
        assert row[db.task.c.id] == t_id
        assert row[db.task.c.description] ==t_desc
        assert row[db.task.c.points] == points
        assert row[db.task.c.assignment_id] == a_id

        null = db.select_assignment(conn, 28128218)
        assert null is None

        a = db.select_assignment(conn, a_id)
        assert isinstance(a, Assignment)
        assert len(a.tasks) ==1
        
        assert a.id == a_id
        assert a.name == visible_a_name
        assert a.deadline == deadline
        assert a.reveal == reveal

        t = a.tasks[0]

        assert isinstance(t, Task)
        assert t.id == t_id
        assert t.description ==t_desc
        assert t.points == points
        assert t.assignment_id == a_id

        null = db.select_assignment(conn, a_id, for_student=True)
        assert null is None
    
def test_course_set_assignment_visibility(conn, a_files = [], t_files=[]):
    from database import db
    from .course_test import test_course_insert
    id, _ = test_course_insert(conn)
    teacher = db.get_user(conn, "opettaja", "opettaja")

    visble_a_name = get_random_unicode(30)
    visble_reveal = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(hours=1)
    visble_deadline = random_datetime(start=visble_reveal)
    
    points = random.randint(5, 20)
    t_desc = get_random_unicode(30)
    task1= Task(None, 1, points, t_desc)
    visble_a_id, _ = db.insert_assignment(conn, teacher.id, id, visble_a_name, visble_deadline,visble_reveal, a_files , tasks=[task1])

    a_name2 = get_random_unicode(30)
    reveal2 = pytz.utc.localize(datetime.datetime.utcnow()) + datetime.timedelta(hours=1)
    deadline2 = random_datetime(start=visble_reveal)
    
    

    points = random.randint(5, 20)
    t_desc = get_random_unicode(30)
    task1= Task(None, 1, points, t_desc)
    
    points = random.randint(5, 20)
    t_desc = get_random_unicode(30)
    task2= Task(None, 1, points, t_desc)

    
    tasks=[task1, task2]
    a_id2, _ = db.insert_assignment(conn, teacher.id, id, a_name2, deadline2,reveal2, a_files, tasks=tasks)
    cs = db.select_courses_teacher(conn, teacher.id)
    assert len(cs)==1
    c = cs[0]
    assert isinstance(c, Course)
    db.set_assignments(conn, c, for_student=True)

    assert len(c.assignments)==1, "can't see assignment that should be visible"
    assert isinstance(c.assignments[0], Assignment)
    assert c.assignments[0].id == visble_a_id, "assignment incorrect"
    assert c.assignments[0].name == visble_a_name, "assignment incorrect"
    assert c.assignments[0].reveal == visble_reveal, "assignment incorrect"
    assert c.assignments[0].deadline == visble_deadline, "assignment incorrect"
    assert len(c.assignments[0].tasks)==1


    cs = db.select_courses_teacher(conn, teacher.id)
    assert len(cs)==1
    c = cs[0]
    assert isinstance(c, Course)
    db.set_assignments(conn, c, for_student=False)
    assert len(c.assignments)==2
    first = Assignment(visble_a_id, visble_a_name, visble_reveal.replace(tzinfo=None), visble_deadline.replace(tzinfo=None), [])
    assert first in c.assignments

    second = Assignment(a_id2, a_name2, reveal2.replace(tzinfo=None), deadline2.replace(tzinfo=None), [])
    assert second in c.assignments


def test_large_assignment_timezone_helsinki(conn, files = []):
    from database import db
    db.insert_user(conn, "opettaja1", "opettaja", "Who","Cares",role="TEACHER")
    db.insert_user(conn, "opettaja2", "opettaja", "Who","Cares",role="TEACHER")
    db.insert_user(conn, "opettaja3", "opettaja", "Who","Cares",role="TEACHER")
    db.insert_user(conn, "opettaja4", "opettaja", "Who","Cares",role="TEACHER")
    
    teacher1 = db.get_user(conn, "opettaja1", "opettaja")
    teacher2 = db.get_user(conn, "opettaja2","opettaja")
    teacher3 = db.get_user(conn, "opettaja3","opettaja")
    teacher4 = db.get_user(conn, "opettaja4","opettaja")
    teachers = [teacher1, teacher2, teacher3, teacher4]

    assert teacher1 is not None
    assert teacher2 is not None
    assert teacher3 is not None
    assert teacher4 is not None

    teacher_assigments = []
    for teacher in teachers:
        all_assignments = {}
        visible_assignments = {}
        course_ids=insert_random_courses(teacher.id, db)
        assert len(course_ids)>0
        for _ in range(random.randint(15, 21)): #insert assignments
            name = get_random_unicode(15)
            course_id = random.choice(course_ids)
            if random.randint(0,1) or not visible_assignments.get(course_id):
                visible = True
                reveal = pytz.timezone("Europe/Helsinki").localize(datetime.datetime.utcnow()) - datetime.timedelta(minutes=1)
            else:
                visible = False
                reveal = pytz.timezone("Europe/Helsinki").localize(datetime.datetime.utcnow()) + datetime.timedelta(hours=random.randint(3,5), minutes=1)
            deadline = random_datetime(start=reveal, time_zone="Europe/Helsinki")
            
            
            tasks = []
            number = 1
            
            for __ in range(random.randint(2,15)):
                task = random_task(None, files)
                task.number=number
                tasks.append(task)
                number+=1
            assig_id, task_ids = db.insert_assignment(conn, teacher1.id, course_id,name, deadline, reveal, files, tasks=tasks)

            for i in range(len(task_ids)):
                tasks[i].id = task_ids[i]
                tasks[i].assignment_id = assig_id

            result_dict = {"teacher_id":teacher.id, "id":assig_id, "reveal":reveal, "deadline":deadline, "course_id":course_id, "name":name, "files":files, "tasks":tasks}
            if not all_assignments.get(course_id):
                all_assignments[course_id]=[result_dict]
            else:
                all_assignments[course_id].append(result_dict)
            if visible:
                if not visible_assignments.get(course_id):
                    visible_assignments[course_id]=[result_dict]
                else:
                    visible_assignments[course_id].append(result_dict)
                


        temp = (teacher.id, all_assignments, visible_assignments)
        teacher_assigments.append(temp)
    case = unittest.TestCase()
    case.maxDiff = None
    for teacher_id, all_assignments, visible_assignments in teacher_assigments:
        courses = db.select_courses_teacher(conn, teacher_id)
        assert len(courses)
        course_ids = [c.id for c in courses]
        for key in all_assignments.keys():
            assert key in course_ids
        for course in courses:
            correct_assignments = all_assignments.get(course.id, [])
            correct_visible_assignments = visible_assignments.get(course.id)
            
            db.set_assignments(conn, course, for_student=False)
            course.set_timezones("Europe/Helsinki")
            assert len(course.assignments)==len(correct_assignments), "wrong number of assignments"

            for a in course.assignments:
                assert isinstance(a, Assignment)
                assignment_dic = get_correct_assignment(a.id, correct_assignments)
                assert assignment_dic, "\n".join(format_error(a, correct_assignments))
                assert assignment_dic["id"] == a.id
                assert assignment_dic["teacher_id"] == teacher_id
                
                assert assignment_dic["course_id"] == course.id
                assert a.deadline == assignment_dic["deadline"]
                assert a.reveal == assignment_dic["reveal"]
                
                
                assert len(assignment_dic["tasks"])== len(a.tasks)
                case.assertCountEqual(assignment_dic["tasks"],a.tasks)

            db.set_assignments(conn, course, for_student=True)
            for a in course.assignments:
                assert isinstance(a, Assignment)
                assignment_dic = get_correct_assignment(a.id, correct_visible_assignments)
                assert assignment_dic, "\n".join(format_error(a, correct_visible_assignments))
                assert assignment_dic["id"] == a.id
                assert assignment_dic["teacher_id"] == teacher_id
                
                assert assignment_dic["course_id"] == course.id
                assert a.deadline == assignment_dic["deadline"]
                assert a.reveal == assignment_dic["reveal"]
                
                
                assert len(assignment_dic["tasks"])== len(a.tasks)
                case.assertCountEqual(assignment_dic["tasks"],a.tasks)    
    return teachers
            
    

def get_correct_assignment(a_id, assig_dics):
    for dic in assig_dics:
        if dic["id"] == a_id:
            return dic
    return None

def test_simple_assignment_in_time(conn):
    from database import db
    teachers, students = insert_users(db, teacher_count=1, student_count=1)
    t = teachers[0]
    s= students[0]

    assert t
    assert s
    insert_random_courses(t.id, db, n=1)
    course = db.select_courses_teacher(conn, teacher_id=t.id)[0]
    assert course
    name, deadline, reveal = random_assignment(course.id, t.id, hidden=False)
    tasks =[random_task(0, []) for _ in range(4)]

    assignment_id,_ = db.insert_assignment(conn, t.id, course.id, name, deadline, reveal, [], tasks=tasks)
    
    name2=name+"something"
    deadline2 = random_datetime(start=datetime.datetime.utcnow()+datetime.timedelta(days=7))

    _ = db.insert_assignment(conn, t.id, course.id, name2, deadline2, reveal,files=[], tasks=tasks)

    assigment_ids = db.get_assignments_in_time(conn, t.id, [course.id], only_ids=True)

    assert assigment_ids
    assert len(assigment_ids)==1
    assert assigment_ids[0] ==assignment_id
    a = db.select_assignment(conn, assigment_ids[0])
    assert a.name == name

    assignments = db.get_assignments_in_time(conn, t.id, [course.id])

    assert assignments
    assert len(assignments)==1
    assig = assignments[0]
    assert a.id == assigment_ids[0]
    assert assig==a

def random_assignment(course_id, teacher_id, hidden=False):
    if hidden:
        reveal = random_datetime()
    else:
        reveal = pytz.utc.localize(datetime.datetime.utcnow())
    deadline = random_datetime(start = reveal)
    name = get_random_unicode(20)
    return name, deadline, reveal

        
def random_task(a_id, files):
    t = Task(0,random.randint(1,20), random.randint(5,8), get_random_unicode(random.randint(10,20)), assignment_id=a_id, files=files)
    return t
