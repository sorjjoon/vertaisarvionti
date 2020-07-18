from __future__ import annotations
import datetime
import io
import os
import random
import tempfile

import pytest
import pytz
from flask import url_for

from application import create_app
from application.domain.assignment import Assignment, Task
from application.domain.course import Course
from application import data

def insert_users(db:data, teacher_count=1, student_count=1):
    with db.engine.connect() as conn:
        teachers = []
        students = []
        for _ in range(teacher_count):
            username = get_random_unicode(40)
            password = get_random_unicode(35)
            first = get_random_unicode(5)
            last = get_random_unicode(15)
            db.insert_user(conn, username, password, first, last, role="TEACHER")
            t = db.get_user(conn, username, password)
            assert t is not None
            teachers.append(t)

        for _ in range(student_count):
            username = get_random_unicode(40)
            password = get_random_unicode(35)
            first = get_random_unicode(5)
            last = get_random_unicode(15)
            db.insert_user(conn, username, password, first, last, role="USER")
            s = db.get_user(conn, username, password)
            assert s is not None
            students.append(s)
    return teachers, students


                
        
    


def format_error(left, right):
    if isinstance(left, Assignment) and isinstance(right, Assignment):
        return ["failed comparing assignments" ,
         "course_id: {left} != {right}".format(left=left.course_id, right=right.course_id),
         "id: {left} != {right}".format(left=left.id, right=right.id),
         "name: {left} != {right}".format(left=left.name, right=right.name),
         "tasks: {left} != {right}".format(left=",".join([str(i) for i in left.tasks]) , right=",".join([str(i) for i in right.tasks]) )
         ]

    try:
        iter(right)
        try:
            iter(left)
            return ["sets are not equal", "left set"]+[str(i) for i in left]+["right set"]+[str(i) for i in right]
        except:
            return ["didn't find object in list","left object", str(left),"---------------------","right list"] + [str(i) for i in right]
    except:
        return []



def random_datetime(start = datetime.datetime.utcnow(), time_zone = "UTC"):
    """Guaranteed to be past start

    Keyword Arguments:
        start {[type]} -- [description] (default: {datetime.date.now()})
        time_zone {str} -- [description] (default: {"UTC"})
    """
    if start.tzinfo:
        start = start.astimezone(pytz.timezone(time_zone))
    else:
        start = pytz.timezone(time_zone).localize(start)
    result = start + datetime.timedelta(days=random.randint(0, 30), hours=random.randint(1, 30), minutes=random.randint(1,70))
    return result
def get_random_unicode(length):

    try:
        get_char = unichr
    except NameError:
        get_char = chr

    # Update this to include code point ranges to be sampled
    include_ranges = [
        ( 0x0021, 0x0021 ),
        ( 0x0023, 0x0026 ),
        ( 0x0028, 0x007E ),
        ( 0x00A1, 0x00AC ),
        ( 0x00AE, 0x00FF ),
        ( 0x0100, 0x017F ),
        ( 0x0180, 0x024F ),
        ( 0x2C60, 0x2C7F ),
        ( 0x16A0, 0x16F0 ),
        ( 0x0370, 0x0377 ),
        ( 0x037A, 0x037E ),
        ( 0x0384, 0x038A ),
        ( 0x038C, 0x038C ),
    ]

    alphabet = [
        get_char(code_point) for current_range in include_ranges
            for code_point in range(current_range[0], current_range[1] + 1)
    ]
    return ''.join(random.choice(alphabet) for i in range(length))


def insert_random_courses(teacher_id, db, n=random.randint(1,5)):
    ids = []
    with db.engine.connect() as conn:
        for _ in range(n):
            name = get_random_unicode(random.randint(12,18))
            desc = get_random_unicode(random.randint(9,18))
            abbr = get_random_unicode(random.randint(3,5))
            c = Course(name, desc, teacher_id=teacher_id, abbreviation=abbr)
            id, _ = db.insert_course(conn, c, teacher_id)
            ids.append(id)
    return ids


@pytest.fixture(scope="function")
def conn():
    app = create_app("DATA_TEST")
 
    _ = app.test_client()
    
    # Establish an application context before running the tests.
    ctx = app.app_context()
    
    ctx.push()
    from application import db
    conn = db.engine.connect()
    yield conn
    conn.close()

    ctx.pop()
    