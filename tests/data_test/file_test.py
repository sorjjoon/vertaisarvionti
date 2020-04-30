

import os
import tempfile
import random
from sqlalchemy.exc import IntegrityError
import pytest
import pytz
from assignment_test import test_simple_assignment, random_assignment, random_task
from flask import url_for
import io
from werkzeug.datastructures import FileStorage, FileMultiDict
from werkzeug.utils import secure_filename
import datetime
import unittest
from application.domain.assignment import Assignment, Task, File
from db_fixture import db_test_client, get_random_unicode, random_datetime
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)

def file_insert_helper(binary_file=None, task_id=None, submit_id=None, assignment_id=None, answer_id = None, name ="something"):
    from application import db
    sql = db.file.insert().values(binary_file=binary_file, task_id=task_id, submit_id=submit_id, assignment_id=answer_id, answer_id = answer_id, name=name)
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        return id


def test_large_assignment_with_files_insert_with_access_rights(db_test_client):
    from application import db
    from course_test import test_large_course_insert
    teachers = []
    
    assert len(teachers)>10

    students = []
    for _ in range(random.randint(34,38)):
        username = get_random_unicode(20)
        password = get_random_unicode(20)
        first_name = get_random_unicode(15)
        last_name = get_random_unicode(12)

        db.insert_user(username, password, first_name, last_name)
        teach = db.get_user(username, password)
        assert teach
        students.append(teach)
    assert len(students) > 30
    all_courses = []
    for t in teachers:
        t_c = db.select_courses_teacher(t.id)
        assert len(t_c) > 2
        all_courses+=t_c
    assert len(all_courses)
    student_enlists = {}
    for s in students:
        student_enlists[s.id] = []
        courses_to_enlist =random.sample(all_courses, random.randint(4,len(all_courses)-1))
        for c in courses_to_enlist:
            db.enlist_student(c.code, s.id)
            student_enlists[s.id].append(c)
    assert student_enlists
    file_storage = FileMultiDict()
    not_hidden_file_storage = FileMultiDict()
    assert len(teachers) >= 20
    for t in teachers:
        courses = db.select_courses_teacher(teach.id)
        assert len(courses)>=14
        for c in courses:
            for _ in range(1, 3):                
                hidden = bool(random.randint(0,1))
                a_name, a_reveal, a_deadline = random_assignment(c.id, t.id, hidden=hidden)
                
                werk_files = []
                
                for _ in range(random.randint(5,7)):
                    file = generate_random_file(length=10)
                    file_name = secure_filename(get_random_unicode(20))
                    werk_file = FileStorage(file, file_name)
                    werk_files.append(werk_file)
                    


                a_id = db.insert_assignment(t.id, c.id,a_name, a_deadline, a_reveal,werk_files)
                with db.engine.connect() as conn:
                    sql = select([db.assignment]).where(db.assignment.c.id == a_id)
                    rs = conn.execute(sql)
                    row = rs.first()
                    assert row is not None
                    assert row[db.assignment.c.id] == a_id
                    assert row[db.assignment.c.a_name] == a_name
                    


                for file in werk_files:
                    file_storage.add_file("a"+str(a_id), file, file.filename)
                    if not hidden:
                        not_hidden_file_storage.add_file("a"+str(a_id), file, file.filename)

                    file.close()
                assert werk_files[0].filename
                assert len(file_storage.getlist("a"+str(a_id))) >=3
                assert file_storage.getlist("a"+str(a_id))[0].filename == werk_files[0].filename

                for __ in range(random.randint(4,7)):
                    werk_files = []
                
                    for _ in range(random.randint(3,7)):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        werk_files.append(werk_file)

                    task = random_task(a_id, werk_files)
                    db.insert_task(t.id, a_id, task.description, task.points, werk_files)
                    for file in werk_files:
                        file_storage.add_file("t"+str(a_id), file, file.filename)
                        if not hidden:
                            not_hidden_file_storage.add_file("t"+str(a_id), file, file.filename)

                        file.close()
    
    for t in teachers:
        courses = db.select_courses_teacher(t.id)
        for c in courses:
            db.set_assignments(c, for_student=False)
            for a in c.assignments:
                assert isinstance(a, Assignment)
                correct_files = file_storage.getlist("a"+str(a.id))
                assert len(correct_files)>=5
                correct_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]
                case = unittest.TestCase()
                case.assertCountEqual(correct_file_names, db_filenames) 

                for t in a.tasks:
                    assert isinstance(t, Task)
                    correct_files = file_storage.getlist("t"+str(t.id))
                    assert len(correct_files)>=4
                    correct_file_names = [file.filename for file in correct_files]
                    db_filenames = [file.name for file in a.files]
                    case.assertCountEqual(correct_file_names, db_filenames) 

    assert len(students) > 30
    for s in students:
        courses = student_enlists[s.id]
        db_courses = db.select_courses_student(s.id)
        case = unittest.TestCase()
        case.assertCountEqual(courses, db_courses)
        assert db_courses
        for c in db_courses:
            db.set_assignments(c, for_student=True)
            for a in c.assignments:
                assert isinstance(a, Assignment)
                assert a.reveal <= pytz.utc.localize(datetime.datetime.utcnow())
                incorrect_files = file_storage.getlist("a"+str(a.id))
                
                incorrect_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]
                case = unittest.TestCase()
                case.assertCountEqual(incorrect_file_names, db_filenames) 
                assert len(incorrect_files) > len(db_filenames)
                
                



def generate_random_file(length=random.randint(1024, 1*1024*1024) , seek=True) -> tempfile.NamedTemporaryFile:
    file = tempfile.NamedTemporaryFile()
    rand_bytes = bytearray(random.getrandbits(8) for _ in range(length))
    file.write(rand_bytes)
    
    if seek:
        file.seek(0)

    return file

def test_simple_file_assignment_task(db_test_client):
    from application import db
    
    with generate_random_file() as temp, generate_random_file() as task_temp:
        file_name = get_random_unicode(10)
        task_file_name = get_random_unicode(10)
        
        werk_file = FileStorage(temp, file_name)
        werk_task_file = FileStorage(task_temp, task_file_name)


        test_simple_assignment(db_test_client)
        teach = db.get_user("opettaja", "opettaja")
        c = db.select_courses_teacher(teach.id)[0]
        name = get_random_unicode(10)
        reveal = pytz.utc.localize(datetime.datetime.now())
        deadline = random_datetime()


        a_id = db.insert_assignment(teach.id, c.id, name, deadline, reveal, [werk_file])
        
        task_name = get_random_unicode(10)
        points = random.randint(5,100)

        t_id = db.insert_task(teach.id, a_id, task_name, points, [werk_task_file])
        

        files = db.select_file_details(assignment_id=a_id)
        assert len(files)==1
        file = files[0]
        assert file.name == secure_filename(file_name)
        assert file.date.date() == datetime.date.today()
        
        temp.seek(0)
        bin_data = temp.read()
        db_bin_data, name=db.get_file(file.id)
        assert name == file.name

        assert len(bin_data) > 1000
        assert len(bin_data)==len(db_bin_data)
        assert type(bin_data)==type(db_bin_data), "Wrong types (can't compare) "+str(type(bin_data))+" vs "+str(type(db_bin_data))
        assert bin_data==db_bin_data

        task_files = db.select_file_details(task_id=t_id)

        assert len(task_files)==1
        file = task_files[0]
        task_temp.seek(0)
        real_task_bin_data = task_temp.read()
        db_bin_task_data, name = db.get_file(file.id)
        assert name == secure_filename(task_file_name)
        assert real_task_bin_data == db_bin_task_data

def test_file_update(db_test_client):
    from application import db

def test_db_file_insert_constraint(db_test_client):
    from application import db
    with pytest.raises(IntegrityError):
        file_insert_helper(binary_file=io.BytesIO(b"helvetin turhia bitteja").read())

    sql = Select([db.file])
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        assert row is None
        



        
