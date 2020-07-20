

import datetime
import io
import os
import random
import tempfile
import unittest
from .user_test import insert_users
import pytest
import pytz
from flask import url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)

from application.auth.account import Account
from application.domain.course import Course
from .db_fixture import conn, get_random_unicode, random_datetime




def insert_courses(db, teacher_id, n):
    with db.engine.connect() as conn:
        for _ in range(n):
            name = get_random_unicode(45)
            desc = get_random_unicode(23)
            abbr = get_random_unicode(4)
            c = Course(name, desc, abbreviation=abbr)
            id, code = db.insert_course(conn, c, teacher_id)


def test_course_insert(conn):
    from application import db
    from .user_test import test_user_insert
    test_user_insert(conn)
    student = db.get_user(conn, "oppilas", "oppilas")
    teacher = db.get_user(conn, "opettaja", "opettaja")
    assert student is not None
    assert teacher is not None
    name = "'öäasöä1ÅÄÖÅÄÅÖÄÅÖö23å231äl23ölasäösä"
    desc = "äöääöäpläplpä21äl.masalöas"
    abbr = "ASKF"
    c = Course(name, desc, abbreviation=abbr, teacher_name=teacher.last_name+", "+teacher.first_name, teacher_id=teacher.id)
    id, code = db.insert_course(conn, c, teacher.id)
    c.code = code
    assert id > 0 
    assert code is not None
    with db.engine.connect() as conn:
        sql = select([db.course]).where(db.course.c.teacher_id == teacher.id)
        rs = conn.execute(sql)
        row = rs.first()
        assert row[db.course.c.id] == id
        assert row[db.course.c.description] == desc
        assert row[db.course.c.name] == name
        assert row[db.course.c.abbreviation] == abbr
        assert row[db.course.c.code] == code
        assert c == Course(row[db.course.c.name],row[db.course.c.description], code=row[db.course.c.code], teacher_id=teacher.id, teacher_name=teacher.last_name+", "+teacher.first_name, abbreviation=row[db.course.c.abbreviation])
    return id, code

def test_large_course_insert(conn):
    from application import db
    teachers = []
    for _ in range(random.randint(18,23)):
        username = get_random_unicode(35)
        password = get_random_unicode(30)
        first = get_random_unicode(15)
        last = get_random_unicode(25)

        db.insert_user(conn, username, password, first, last, role="TEACHER")
        acc = db.get_user(conn, username, password)
        assert acc.name == username
        assert acc.role == "TEACHER"
        teachers.append(acc)
    teach_courses = {}
    for t in teachers:
        teach_courses[t.id]=[]
        for _ in range(random.randint(12,20)):
            course = Course(get_random_unicode(20), get_random_unicode(40), abbreviation=get_random_unicode(3), teacher_id=t.id, teacher_name=t.last_name+", "+t.first_name)
            id, code = db.insert_course(conn, course, t.id)
            course.id = id
            course.code = code
            course.teacher_name = t.last_name +", "+t.first_name
            assert course.code is not None
            teach_courses[t.id].append(course)
    random.shuffle(teachers)
    all_courses = []
    case = unittest.TestCase()
    case.maxDiff=None
    for t in teachers:
        db_courses = db.select_courses_teacher(conn, t.id)
        assert len(db_courses)>=12
        
        case.assertCountEqual(db_courses, teach_courses[t.id])
        all_courses+=db_courses
    db.insert_user(conn, "something","something" ,"something" ,"something")
    student = db.get_user(conn, "something", "something")

    for c in all_courses:
        db.enlist_student(conn, c.code, student.id)
    
    student_db_courses = db.select_courses_student(conn, student.id)
    case.assertCountEqual(student_db_courses, all_courses)
    return teachers

def test_course_signup(conn):
    from application import db
    
    id, code = test_course_insert(conn)

    student = db.get_user(conn, "oppilas", "oppilas")
    teacher = db.get_user(conn, "opettaja", "opettaja")
    assert student is not None
    assert teacher is not None

    db.enlist_student(conn, code, student.id)

    with db.engine.connect() as conn:
        sql = select([db.course_student.c.course_id]).where(db.course_student.c.student_id == id)
        rs = conn.execute(sql)
        assert rs.first()[db.course_student.c.course_id] == id

        course = db.select_courses_student(conn, student.id)
        assert len(course) ==1
        assert course[0].name == "'öäasöä1ÅÄÖÅÄÅÖÄÅÖö23å231äl23ölasäösä"
        assert course[0].description == "äöääöäpläplpä21äl.masalöas"

def test_invalid_signup(conn):
    from application import db
    
    description = get_random_unicode(100)
    reveal = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(minutes=1)
    teacher = insert_users(db, 1, roles=["TEACHER"])[0]
    student = insert_users(db, 1, roles=["USER"])[0]
    id, code = db.insert_course(conn, Course(description, "something", abbreviation="som", teacher_name=teacher.last_name+", "+teacher.first_name), teacher.id)
    db.enlist_student(conn, code, student.id)
    with pytest.raises(IntegrityError):
        db.enlist_student(conn, code, student.id)
    
    with pytest.raises(ValueError):
        db.enlist_student(conn, "something", student.id)



def test_large_course_signup(conn):
    from application import db
    from .user_test import test_weird_chars_large_set
    ids = test_weird_chars_large_set(conn, random_roles=False)
    
    
    
    courses = []
    teacher_courses = {}
    accs = []
    for id in ids:
        acc = db.get_user_by_id(conn, id)
        assert acc.id == id
        assert acc.role == "TEACHER" or acc.role=="USER"

        accs.append(acc)
        if acc.role == "TEACHER":
            teacher_courses[id] = []
            for _ in range(random.randint(14,16)):
                
                name = get_random_unicode(10)
                description = get_random_unicode(20)
               
                c = Course(name, description, teacher_id=id, abbreviation=get_random_unicode(3), teacher_name=acc.last_name+", "+acc.first_name)
                course_id, code = db.insert_course(conn, c, id)
                c.id = course_id
                c.code = code
                assert c.teacher_id is not None
                assert c.teacher_name is not None
                courses.append(c)
                teacher_courses[id].append(c)
    student_enlists = {}
    for acc in accs:
        if acc.role == "USER":
            student_enlists[acc.id]=[]
            enlists = random.sample(courses, k=random.randint( len(courses)//2, len(courses)-1 ))
            for c in enlists:
                student_enlists[acc.id].append(c)
                db.enlist_student(conn, c.code, acc.id)
    case = unittest.TestCase()
    case.maxDiff=None
    for acc in accs:
        if acc.role =="TEACHER":
            courses = db.select_courses_teacher(conn, acc.id)
            real = teacher_courses[acc.id]
            assert len(real) == len(courses)
            assert len(real) > 10
            
            case.assertCountEqual(courses, real)
            for c in courses:
                assert c.teacher_id == acc.id
                assert c in real, str(c)+" not found in"+", ".join(str(a) for a in real)
            
            
        else:
            courses = db.select_courses_student(conn, acc.id)
            real = student_enlists[acc.id]

            assert len(real) == len(courses)
            assert len(real) > 6
            
            case.assertCountEqual(courses, real)
            for c in courses:
                assert c.teacher_id is not None
                
            

