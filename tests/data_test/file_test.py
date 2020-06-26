

import datetime
import io
import os
import random
import tempfile
import unittest

import pytest
import pytz
from flask import url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from werkzeug.datastructures import FileMultiDict, FileStorage
from werkzeug.utils import secure_filename

from application.domain.assignment import Assignment, File, Task
from application.domain.course import Course
from application.database.data import data

from .assignment_test import (random_assignment, random_task,
                              )
from .course_test import insert_courses
from .db_fixture import db_test_client, get_random_unicode, random_datetime
from .user_test import insert_users


def file_insert_helper(db, binary_file=None, task_id=None, submit_id=None, assignment_id=None, answer_id = None, user_id=1, name ="something"):
    
    sql = db.file.insert().values(binary_file=binary_file, owner_id=user_id, task_id=task_id, submit_id=submit_id, assignment_id=assignment_id, answer_id = answer_id, name=name)
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        return id
def create_dummy(db:data, user_id=None, course=None, task=None, assignment=None, submit=None, answer=None):
    s = "useless"
    d = datetime.datetime.now()
    results = {}
    if not user_id:
        username = get_random_unicode(30)
        db.insert_user(username, s,s,s,role="TEACHER")
        user_id = db.get_user(username,s)
        results["teacher_id"]=user_id
    if not course:
        course, _ = db.insert_course(Course(s,s,d),user_id)
        results["course_id"]=course
    if not assignment:
        assignment = db.insert_assignment(user_id, course, s, d, d, [])
        results["assignment_id"]=assignment
    if not task:
        task = db.insert_task(user_id, assignment, s , 2, [])
        results["task_id"]=task
    if not answer:
        answer = db.update_answer(user_id, task, [], s, d)
        results["answer_id"]=answer
    if not submit:
        submit = db.update_submit(user_id, task, assignment, [])
        results["submit_id"]=submit

    return results


def test_select_file_details_multiple(db_test_client):
    from application import db
    db.insert_user("turha", "turha", "turha", "turha", role="TEACHER")
    user_id = db.get_user("turha","turha").id
    case = unittest.TestCase()
    case.maxDiff = None
    c_id, _ =db.insert_course(Course("something","somthing", datetime.datetime.now()),user_id)
    for _ in range(20):

        id_dic = create_dummy(db, user_id=user_id, course=c_id)
        correct_files= []
        for i in range(20):
            rand_bytes= os.urandom(20)
            name = "task"+str(id_dic["task_id"])+str(i)
            id = file_insert_helper(db,binary_file=rand_bytes, task_id=id_dic["task_id"], name=name, user_id=user_id)
            correct_files.append(File(id, name, datetime.datetime.now()))
        files = db.select_file_details(task_id=id_dic["task_id"])
        assert len(files) == 20
        
        case.assertCountEqual(files, correct_files)
        
        correct_bytes, _ = db.get_file(id)
        assert rand_bytes == correct_bytes

        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,submit_id=id_dic["submit_id"], name="submit_id"+str(id_dic["submit_id"]), user_id=user_id)
        sub_id = id_dic["submit_id"]
        files = db.select_file_details(submit_id=sub_id)
        assert len(files) == 1
        assert files[0].name == "submit_id"+str(id_dic["submit_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(id)
        assert rand_bytes == correct_bytes


        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,assignment_id=id_dic["assignment_id"], name="assignment_id"+str(id_dic["task_id"]), user_id=user_id)
        files = db.select_file_details(assignment_id=id_dic["assignment_id"])
        assert len(files) == 1
        assert files[0].name == "assignment_id"+str(id_dic["assignment_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(id)
        assert rand_bytes == correct_bytes

        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,answer_id=id_dic["answer_id"], name="answer_id"+str(id_dic["task_id"]), user_id=user_id)
        files = db.select_file_details(answer_id=id_dic["answer_id"])
        assert len(files) == 1
        assert files[0].name == "answer_id"+str(id_dic["answer_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(id)
        assert rand_bytes == correct_bytes



def test_select_file_details_single(db_test_client):
    from application import db
    db.insert_user("turha", "turha", "turha", "turha", role="TEACHER")
    user_id = db.get_user("turha","turha").id
    c_id, _ =db.insert_course(Course("something","somthing", datetime.datetime.now()),user_id)
    for _ in range(20):

        id_dic = create_dummy(db, user_id=user_id, course=c_id)
        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes, task_id=id_dic["task_id"], name="task"+str(id_dic["task_id"]), user_id=user_id)
        files = db.select_file_details(task_id=id_dic["task_id"])
        assert len(files) == 1
        assert files[0].name == "task"+str(id_dic["task_id"])
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(id)

        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,submit_id=id_dic["submit_id"], name="submit_id"+str(id_dic["submit_id"]), user_id=user_id)
        sub_id = id_dic["submit_id"]
        files = db.select_file_details(submit_id=sub_id)
        assert len(files) == 1
        assert files[0].name == "submit_id"+str(id_dic["submit_id"])
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(id)


        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,assignment_id=id_dic["assignment_id"], name="assignment_id"+str(id_dic["task_id"]), user_id=user_id)
        files = db.select_file_details(assignment_id=id_dic["assignment_id"])
        assert len(files) == 1
        assert files[0].name == "assignment_id"+str(id_dic["assignment_id"])
        assert files[0].id == id
        db_bytes, name = db.get_file(id)
        
        assert rand_bytes == db_bytes

        rand_bytes= os.urandom(20)
        id = file_insert_helper(db,binary_file=rand_bytes,answer_id=id_dic["answer_id"], name="answer_id"+str(id_dic["task_id"]), user_id=user_id)
        files = db.select_file_details(answer_id=id_dic["answer_id"])
        assert len(files) == 1
        assert files[0].name == "answer_id"+str(id_dic["answer_id"])
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(id)



def test_large_assignment_with_files_insert_with_access_rights(db_test_client):
    from application import db

    teachers = insert_users(db, 8, roles=["TEACHER"])
    
    assert len(teachers)>=8

    students = insert_users(db, 50, roles=["USER"])
    assert len(students) > 49


    all_courses = []
    for t in teachers:
        insert_courses(db, t.id, 6)
        t_c = db.select_courses_teacher(t.id)
        assert len(t_c) ==6
        all_courses+=t_c
    assert len(all_courses)
    student_enlists = {}
    for s in students:
        student_enlists[s.id] = []
        courses_to_enlist =random.sample(all_courses, random.randint(4,8))
        for c in courses_to_enlist:
            db.enlist_student(c.code, s.id)
            student_enlists[s.id].append(c)
    assert student_enlists
    file_storage = FileMultiDict()
    not_hidden_file_storage = FileMultiDict()
    assert len(teachers) == 8
    for t in teachers:
        courses = db.select_courses_teacher(t.id)
        assert len(courses) == 6
        for c in courses:
            for _ in range(5):                
                hidden = bool(random.randint(0,1))
                a_name, a_reveal, a_deadline = random_assignment(c.id, t.id, hidden=hidden)
                
                werk_files = []
                
                for _ in range(random.randint(2,4)):
                    file = generate_random_file(length=10)
                    file_name = secure_filename(get_random_unicode(20))
                    werk_file = FileStorage(file, file_name)
                    werk_files.append(werk_file)
                    


                a_id = db.insert_assignment(t.id, c.id, a_name, a_deadline, a_reveal,werk_files)
                with db.engine.connect() as conn:
                    sql = select([db.assignment]).where(db.assignment.c.id == a_id)
                    rs = conn.execute(sql)
                    row = rs.first()
                    assert row is not None
                    assert row[db.assignment.c.id] == a_id
                    assert row[db.assignment.c.name] == a_name
                    


                for file in werk_files:
                    file_storage.add_file("a"+str(a_id), file, file.filename)
                    if not hidden:
                        not_hidden_file_storage.add_file("a"+str(a_id), file, file.filename)

                    file.close()
                assert werk_files[0].filename
                assert len(file_storage.getlist("a"+str(a_id))) >=2
                assert file_storage.getlist("a"+str(a_id))[0].filename == werk_files[0].filename

                for __ in range(random.randint(3,5)):
                    werk_files = []
                    n = random.randint(1,3)
                    for _ in range(n):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        werk_files.append(werk_file)

                    task = random_task(a_id, werk_files)
                    task.id = db.insert_task(t.id, a_id, task.description, task.points, werk_files)
                    
                    for file in werk_files:
                        file_storage.add_file("t"+str(task.id), file, file.filename)
                        if not hidden:
                            not_hidden_file_storage.add_file("t"+str(task.id), file, file.filename)

                        file.close()

                    assert len(file_storage.getlist("t"+str(task.id))) == n
    
    for t in teachers:
        courses = db.select_courses_teacher(t.id)
        for c in courses:
            db.set_assignments(c, for_student=False)
            for a in c.assignments:
                assert isinstance(a, Assignment)
                assert not a.files
                a.files = db.select_file_details(assignment_id=a.id)

                correct_files = file_storage.getlist("a"+str(a.id))
                assert len(correct_files)>=2
                correct_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]
                case = unittest.TestCase()
                case.assertCountEqual(correct_file_names, db_filenames), "incorrect filenames in db filename for assign "+str(a.id) 
                for file in a.files:
                        db_files = db.select_file_details(file_id =file.id)
                        assert len(db_files)==1
                        assert db_files[0] == file
                for t in a.tasks:
                    assert isinstance(t, Task)
                    t_id = t.id
                    correct_files = file_storage.getlist("t"+str(t_id))
                    t.files = db.select_file_details(task_id=t_id)
                    assert len(correct_files)>=1
                    correct_file_names = [file.filename for file in correct_files]
                    db_filenames = [file.name for file in t.files]
                    case.assertCountEqual(correct_file_names, db_filenames), "incorrect filenames in db filename for task "+str(t.id)

                    for file in t.files:
                        db_files = db.select_file_details(file_id = file.id)
                        assert len(db_files)==1
                        assert db_files[0] == file

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
                a.files=db.select_file_details(assignment_id=a.id)
                correct_files = not_hidden_file_storage.getlist("a"+str(a.id))
                
                correct_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]
                case = unittest.TestCase()
                case.assertCountEqual(correct_file_names, db_filenames) 
                
                
                



def generate_random_file(length=random.randint(1024, 1*1024*1024) , seek=True) -> tempfile.NamedTemporaryFile:
    file = tempfile.NamedTemporaryFile()
    rand_bytes = bytearray(random.getrandbits(8) for _ in range(length))
    file.write(rand_bytes)
    
    if seek:
        file.seek(0)

    return file

def test_simple_file_assignment_task(db_test_client):
    from application import db
    from .assignment_test import test_simple_assignment
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
    s="nothing"
    db.insert_user(s,s,s,s,role="TEACHER")
    user_id = db.get_user(s,s).get_id()

    with pytest.raises(IntegrityError):
        file_insert_helper(db, user_id=user_id, binary_file=io.BytesIO(b"helvetin turhia bitteja").read())

    sql = Select([db.file])
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        assert row is None
