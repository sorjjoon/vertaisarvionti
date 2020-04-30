

import os
import tempfile
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import pytest
from flask import url_for
import io
import datetime
import unittest
import random
from db_fixture import db_test_client, get_random_unicode, random_datetime
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)
from user_test import test_user_insert
from application.domain.course import Course
from application.auth.account import account
def test_course_insert(db_test_client):
    from application import db
    test_user_insert(db_test_client)
    student = db.get_user_by_id(1)
    teacher = db.get_user_by_id(2)
    assert student is not None
    assert teacher is not None
    name = "'öäasöä1ÅÄÖÅÄÅÖÄÅÖö23å231äl23ölasäösä"
    desc = "äöääöäpläplpä21äl.masalöas"
    c = Course(name, desc, datetime.date.today())
    id, code = db.insert_course(c, teacher.id)

    assert id > 0 
    assert code is not None
    with db.engine.connect() as conn:
        sql = select([db.course]).where(db.course.c.teacher_id == teacher.id)
        rs = conn.execute(sql)
        row = rs.first()
        assert row[db.course.c.id] == id
        assert row[db.course.c.description] == desc
        assert row[db.course.c.name] == name

    

    return id, code

def test_large_course_insert(db_test_client):
    from application import db
    teachers = []
    for _ in range(random.randint(18,23)):
        username = get_random_unicode(35)
        password = get_random_unicode(30)
        first = get_random_unicode(15)
        last = get_random_unicode(25)

        db.insert_user(username, password, first, last, role="TEACHER")
        acc = db.get_user(username, password)
        assert acc.name == username
        assert acc.role == "TEACHER"
        teachers.append(acc)
    teach_courses = {}
    for t in teachers:
        teach_courses[t.id]=[]
        for _ in range(random.randint(12,20)):
            course = Course(get_random_unicode(20), get_random_unicode(40), random_datetime())
            id, code = db.insert_course(course, t.id)
            course.id = id
            course.code = code
            teach_courses[t.id].append(course)
    random.shuffle(teachers)
    for t in teachers:
        db_courses = db.select_courses_teacher(t.id)
        assert len(db_courses)>=12
        case = unittest.TestCase()
        case.assertCountEqual(db_courses, teach_courses[t.id])
    return teachers

def test_course_signup(db_test_client):
    from application import db
    id, code = test_course_insert(db_test_client)

    student = db.get_user_by_id(1)
    teacher = db.get_user_by_id(2)
    assert student is not None
    assert teacher is not None

    db.enlist_student(code, student.id)

    with db.engine.connect() as conn:
        sql = select([db.course_student.c.course_id]).where(db.course_student.c.student_id == id)
        rs = conn.execute(sql)
        assert rs.first()[db.course_student.c.course_id] == id

        course = db.select_courses_student(student.id)
        assert len(course) ==1
        assert course[0].name == "'öäasöä1ÅÄÖÅÄÅÖÄÅÖö23å231äl23ölasäösä"
        assert course[0].description == "äöääöäpläplpä21äl.masalöas"
@pytest.mark.large
def test_large_course_signup(db_test_client):
    from application import db
    from user_test import test_weird_chars_large_set
    ids = test_weird_chars_large_set(db_test_client, random_roles=False)
    from db_fixture import get_random_unicode
    import random
    import datetime
    now = datetime.datetime.now()
    courses = []
    teacher_courses = {}
    accs = []
    for id in ids:
        acc = db.get_user_by_id(id)
        assert acc.id == id
        assert acc.role == "TEACHER" or acc.role=="USER"

        accs.append(acc)
        if acc.role == "TEACHER":
            teacher_courses[id] = []
            for _ in range(random.randint(14,16)):
                
                name = get_random_unicode(10)
                description = get_random_unicode(20)
                random_time = now + datetime.timedelta(days=random.randint(0, 30))
                c = Course(name, description, random_time, teacher_id=id)
                course_id, code = db.insert_course(c, id)
                c.id = course_id
                c.code = code
                assert c.teacher_id is not None
                courses.append(c)
                teacher_courses[id].append(c)
    student_enlists = {}
    for acc in accs:
        if acc.role == "USER":
            student_enlists[acc.id]=[]
            enlists = random.sample(courses, k=random.randint( len(courses)//2, len(courses)-1 ))
            for c in enlists:
                student_enlists[acc.id].append(c)
                db.enlist_student(c.code, acc.id)

    for acc in accs:
        if acc.role =="TEACHER":
            courses = db.select_courses_teacher(acc.id)
            real = teacher_courses[acc.id]
            assert len(real) == len(courses)
            assert len(real) > 10
            case = unittest.TestCase()
            case.assertCountEqual(courses, real)
            for c in courses:
                assert c.teacher_id == acc.id
                assert c in real, str(c)+" not found in"+", ".join(str(a) for a in real)
            
            for c in real:
                assert c in courses, str(c)+" not found in"+", ".join(str(c) for c in real)
        else:
            courses = db.select_courses_student(acc.id)
            real = student_enlists[acc.id]

            assert len(real) == len(courses)
            assert len(real) > 6
            case = unittest.TestCase()
            case.assertCountEqual(courses, real)
            for c in courses:
                assert c.teacher_id is not None
                assert c in real, str(c)+"not found in"+", ".join(str(c) for c in real)
            for c in real:
                assert c in courses, str(c)+"not found in"+", ".join(str(c) for c in real)










