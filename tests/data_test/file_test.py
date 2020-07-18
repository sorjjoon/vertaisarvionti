

import datetime
import io
import os
import random
import tempfile
import unittest

import pytest
import pytz
from flask import url_for
from sqlalchemy import func, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from werkzeug.datastructures import FileMultiDict, FileStorage
from werkzeug.utils import secure_filename

from application.domain.assignment import Assignment, File, Task, Answer, Submit
from application.domain.course import Course
from application.database.data import data

from .assignment_test import (random_assignment, random_task,
                              )
from .course_test import insert_courses
from .db_fixture import conn, get_random_unicode, random_datetime
from .user_test import insert_users


def file_insert_helper(db, binary_file=None, task_id=None, submit_id=None, assignment_id=None, answer_id=None, user_id=1, name="something"):

    sql = db.file.insert().values(binary_file=binary_file, owner_id=user_id, task_id=task_id,
                                  submit_id=submit_id, assignment_id=assignment_id, answer_id=answer_id, name=name)
    with db.engine.connect() as conn:
        with conn.begin():
            rs = conn.execute(sql)
            id = rs.inserted_primary_key[0]
        return id


def generate_random_file(length=random.randint(1024, 1*1024*1024), seek=True) -> tempfile.NamedTemporaryFile:
    file = tempfile.NamedTemporaryFile(delete=True)

    rand_bytes = bytearray(random.getrandbits(8) for _ in range(length))
    file.write(rand_bytes)

    if seek:
        file.seek(0)

    return file

def generate_random_werk_file(length=random.randint(1024, 1*1024*1024)):
    file = generate_random_file(length=length)
    file_name = secure_filename(get_random_unicode(20))
    werk_file = FileStorage(file, file_name)
    return werk_file

def create_dummy(db: data, user_id=None, course=None, task=None, assignment=None, submit=None, answer=None, files=True):
    s = "useless"
    d = datetime.datetime.utcnow()
    results = {}
    results["all_files"] = []
    with db.engine.connect() as conn:
        if not user_id:
            username = get_random_unicode(30)
            db.insert_user(conn, username, s, s, s, role="TEACHER")
            user_id = db.get_user(conn, username, s).id
        results["teacher_id"] = user_id
        if not course:
            course, _ = db.insert_course(
                conn, Course(s, s, abbreviation="moi"), user_id)
        results["course_id"] = course
        if not assignment:
            assignment, _ = db.insert_assignment(
                conn, user_id, course, s, d, d, [])
            if files:
                insert_files = []
                n = random.randint(3, 5)
                results["assignment_file_count"] = n
                for _ in range(n):
                    file = generate_random_file(length=10)
                    file_name = secure_filename(get_random_unicode(20))
                    werk_file = FileStorage(file, file_name)
                    insert_files.append(werk_file)
                    results["all_files"].append(file)

                db.insert_files(conn, user_id, insert_files,
                                assignment_id=assignment)

        results["assignment_id"] = assignment

        if not task:
            task_ids = []
            for i in range(random.randint(3, 5)):
                task = db._insert_task(conn, i+1, user_id, assignment, s, 2, [])
                task_ids.append(task)
                if files:
                    insert_files = []
                    n = random.randint(6, 10)
                    results["task"+str(task)+"_file_count"] = n
                    for _ in range(n):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        insert_files.append(werk_file)
                        results["all_files"].append(file)
                    db.insert_files(conn, user_id, insert_files, task_id=task)
            results["task_ids"] = task_ids

        if not answer:
            for task in results["task_ids"]:
                answer = db.update_answer(conn, user_id, task, [], s, d)
                if files:
                    insert_files = []
                    n = random.randint(11, 13)
                    results[str(task)+"answer_file_count"] = n
                    for _ in range(n):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        insert_files.append(werk_file)
                        results["all_files"].append(file)
                    db.insert_files(
                        conn, user_id, insert_files, answer_id=answer)

                results[str(task)+"answer_id"] = answer

        if not submit:
            for task in results["task_ids"]:
                submit = db.update_submit(conn, user_id, task, assignment, [])
                if files:
                    insert_files = []
                    n = random.randint(14, 17)
                    results["submit"+str(submit)+"file_count"] = n
                    for _ in range(n):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        insert_files.append(werk_file)
                        results["all_files"].append(file)
                    db.insert_files(
                        conn, user_id, insert_files, submit_id=submit)

                results[str(task)+"submit_id"] = submit

        return results


def test_select_file_details_multiple(conn):
    from application import db
    db.insert_user(conn, "turha", "turha", "turha", "turha", role="TEACHER")
    user_id = db.get_user(conn, "turha", "turha").id
    case = unittest.TestCase()
    case.maxDiff = None
    case.maxDiff = None
    c_id, _ = db.insert_course(conn, Course(
        "something", "somthing", abbreviation="moi"), user_id)
    for _ in range(20):

        id_dic = create_dummy(db, user_id=user_id, course=c_id, files=False)
        correct_files = []
        task_id =random.choice(id_dic["task_ids"])
        for i in range(20):
            rand_bytes = os.urandom(20)
            
            name = "task"+str(task_id)+str(i)
            id = file_insert_helper(
                db, binary_file=rand_bytes, task_id=task_id, name=name, user_id=user_id)
            correct_files.append(File(id, name, datetime.datetime.utcnow()))

        files = db.select_file_details(conn, task_id=task_id)
        assert len(files) == 20

        case.assertCountEqual(files, correct_files)

        correct_bytes, _ = db.get_file(conn, id)
        assert rand_bytes == correct_bytes

        rand_bytes = os.urandom(20)
        
        id = file_insert_helper(
            db, binary_file=rand_bytes, submit_id=id_dic[str(task_id)+"submit_id"], name="submit_id"+str(id_dic[str(task_id)+"submit_id"]), user_id=user_id)
        sub_id = id_dic[str(task_id)+"submit_id"]
        files = db.select_file_details(conn, submit_id=sub_id)
        assert len(files) == 1
        assert files[0].name == "submit_id"+str(id_dic[str(task_id)+"submit_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(conn, id)
        assert rand_bytes == correct_bytes

        rand_bytes = os.urandom(20)
        id = file_insert_helper(
            db, binary_file=rand_bytes, assignment_id=id_dic["assignment_id"], name="assignment_id"+str(id_dic["assignment_id"]), user_id=user_id)
        files = db.select_file_details(
            conn, assignment_id=id_dic["assignment_id"])
        assert len(files) == 1
        assert files[0].name == "assignment_id"+str(id_dic["assignment_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(conn, id)
        assert rand_bytes == correct_bytes

        rand_bytes = os.urandom(20)
        id = file_insert_helper(
            db, binary_file=rand_bytes, answer_id=id_dic[str(task_id)+"answer_id"], name="answer_id"+str(task_id), user_id=user_id)
        files = db.select_file_details(conn, answer_id=id_dic[str(task_id)+"answer_id"])
        assert len(files) == 1
        assert files[0].name == "answer_id"+str(id_dic[str(task_id)+"answer_id"])
        assert files[0].id == id
        correct_bytes, _ = db.get_file(conn, id)
        assert rand_bytes == correct_bytes


def test_select_file_details_single(conn):
    from application import db
    db.insert_user(conn, "turha", "turha", "turha", "turha", role="TEACHER")
    user_id = db.get_user(conn, "turha", "turha").id
    c_id, _ = db.insert_course(conn, Course(
        "something", "somthing", abbreviation="some"), user_id)
    for _ in range(20):
        
        id_dic = create_dummy(db, user_id=user_id, course=c_id, files=False)
        task_id = random.choice(id_dic["task_ids"])
        rand_bytes = os.urandom(20)
        id = file_insert_helper(
            db, binary_file=rand_bytes, task_id=task_id, name="task"+str(task_id), user_id=user_id)
        files = db.select_file_details(conn, task_id=task_id)
        assert len(files) == 1
        assert files[0].name == "task"+str(task_id)
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(conn, id)

        rand_bytes = os.urandom(20)
        name = "submit_id"+str(id_dic[str(task_id)+"submit_id"])
        id = file_insert_helper(
            db, binary_file=rand_bytes, submit_id=id_dic[str(task_id)+"submit_id"], name=name, user_id=user_id)
        sub_id = id_dic[str(task_id)+"submit_id"]
        files = db.select_file_details(conn, submit_id=sub_id)
        assert len(files) == 1
        assert files[0].name == "submit_id"+str(id_dic[str(task_id)+"submit_id"])
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(conn, id)

        rand_bytes = os.urandom(20)
        id = file_insert_helper(
            db, binary_file=rand_bytes, assignment_id=id_dic["assignment_id"], name="assignment_id"+str(id_dic["assignment_id"]), user_id=user_id)
        files = db.select_file_details(
            conn, assignment_id=id_dic["assignment_id"])
        assert len(files) == 1
        assert files[0].name == "assignment_id"+str(id_dic["assignment_id"])
        assert files[0].id == id
        db_bytes, _ = db.get_file(conn, id)

        assert rand_bytes == db_bytes

        rand_bytes = os.urandom(20)
        id = file_insert_helper(
            db, binary_file=rand_bytes, answer_id=id_dic[str(task_id)+"answer_id"], name="answer_id"+str(task_id), user_id=user_id)
        files = db.select_file_details(conn, answer_id=id_dic[str(task_id)+"answer_id"])
        assert len(files) == 1
        assert files[0].name == "answer_id"+str(id_dic[str(task_id)+"answer_id"])
        assert files[0].id == id
        assert rand_bytes, _ == db.get_file(conn, id)


def test_large_assignment_with_files_insert_with_access_rights(conn):
    from application import db

    teachers = insert_users(db, 8, roles=["TEACHER"])

    assert len(teachers) >= 8

    students = insert_users(db, 50, roles=["USER"])
    assert len(students) > 49

    all_courses = []
    for t in teachers:
        insert_courses(db, t.id, 6)
        t_c = db.select_courses_teacher(conn, t.id)
        assert len(t_c) == 6
        all_courses += t_c
    assert len(all_courses)
    student_enlists = {}
    for s in students:
        student_enlists[s.id] = []
        courses_to_enlist = random.sample(all_courses, random.randint(4, 8))
        for c in courses_to_enlist:
            db.enlist_student(conn, c.code, s.id)
            student_enlists[s.id].append(c)
    assert student_enlists
    file_storage = FileMultiDict()
    not_hidden_file_storage = FileMultiDict()
    assert len(teachers) == 8
    for t in teachers:
        courses = db.select_courses_teacher(conn, t.id)
        assert len(courses) == 6
        for c in courses:
            for _ in range(5):
                hidden = bool(random.randint(0, 1))
                a_name, a_reveal, a_deadline = random_assignment(
                    c.id, t.id, hidden=hidden)

                werk_files = []

                for _ in range(random.randint(2, 4)):
                    file = generate_random_file(length=10)
                    file_name = secure_filename(get_random_unicode(20))
                    werk_file = FileStorage(file, file_name)
                    werk_files.append(werk_file)

                a_id, _ = db.insert_assignment(
                    conn, t.id, c.id, a_name, a_deadline, a_reveal, werk_files)

                sql = select([db.assignment]).where(db.assignment.c.id == a_id)
                rs = conn.execute(sql)
                row = rs.first()
                assert row is not None
                assert row[db.assignment.c.id] == a_id
                assert row[db.assignment.c.name] == a_name

                for file in werk_files:
                    file_storage.add_file("a"+str(a_id), file, file.filename)
                    if not hidden:
                        not_hidden_file_storage.add_file(
                            "a"+str(a_id), file, file.filename)

                    file.close()
                assert werk_files[0].filename
                assert len(file_storage.getlist("a"+str(a_id))) >= 2
                assert file_storage.getlist(
                    "a"+str(a_id))[0].filename == werk_files[0].filename

                for i in range(random.randint(3, 5)):
                    werk_files = []
                    n = random.randint(1, 3)
                    for _ in range(n):
                        file = generate_random_file(length=10)
                        file_name = secure_filename(get_random_unicode(20))
                        werk_file = FileStorage(file, file_name)
                        werk_files.append(werk_file)

                    task = random_task(a_id, werk_files)
                    task.id = db._insert_task(
                        conn, t.id, i+1, a_id, task.description, task.points, werk_files)

                    for file in werk_files:
                        file_storage.add_file(
                            "t"+str(task.id), file, file.filename)
                        if not hidden:
                            not_hidden_file_storage.add_file(
                                "t"+str(task.id), file, file.filename)

                        file.close()

                    assert len(file_storage.getlist("t"+str(task.id))) == n
    case = unittest.TestCase()
    case.maxDiff = None
    for t in teachers:
        courses = db.select_courses_teacher(conn, t.id)
        for c in courses:
            db.set_assignments(conn, c, for_student=False)
            for a in c.assignments:
                assert isinstance(a, Assignment)
                assert not a.files
                a.files = db.select_file_details(conn, assignment_id=a.id)

                correct_files = file_storage.getlist("a"+str(a.id))
                assert len(correct_files) >= 2
                correct_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]

                case.assertCountEqual(
                    correct_file_names, db_filenames), "incorrect filenames in db filename for assign "+str(a.id)
                for file in a.files:
                    db_files = db.select_file_details(conn, file_id=file.id)
                    assert len(db_files) == 1
                    assert db_files[0] == file
                for t in a.tasks:
                    assert isinstance(t, Task)
                    t_id = t.id
                    correct_files = file_storage.getlist("t"+str(t_id))
                    t.files = db.select_file_details(conn, task_id=t_id)
                    assert len(correct_files) >= 1
                    correct_file_names = [
                        file.filename for file in correct_files]
                    db_filenames = [file.name for file in t.files]
                    case.assertCountEqual(
                        correct_file_names, db_filenames), "incorrect filenames in db filename for task "+str(t.id)

                    for file in t.files:
                        db_files = db.select_file_details(
                            conn, file_id=file.id)
                        assert len(db_files) == 1
                        assert db_files[0] == file

    assert len(students) > 30
    for s in students:
        courses = student_enlists[s.id]
        db_courses = db.select_courses_student(conn, s.id)
        case = unittest.TestCase()
        case.maxDiff = None

        case.assertCountEqual(courses, db_courses)
        assert db_courses
        for c in db_courses:
            db.set_assignments(conn, c, for_student=True)
            for a in c.assignments:
                assert isinstance(a, Assignment)
                assert a.reveal <= pytz.utc.localize(
                    datetime.datetime.utcnow())
                a.files = db.select_file_details(conn, assignment_id=a.id)
                correct_files = not_hidden_file_storage.getlist("a"+str(a.id))

                correct_file_names = [file.filename for file in correct_files]
                db_filenames = [file.name for file in a.files]

                case.assertCountEqual(correct_file_names, db_filenames)


def test_simple_file_assignment_task(conn):
    from application import db
    from .assignment_test import test_simple_assignment
    with generate_random_file() as temp, generate_random_file() as task_temp:
        file_name = get_random_unicode(10)
        task_file_name = get_random_unicode(10)

        werk_file = FileStorage(temp, file_name)
        werk_task_file = FileStorage(task_temp, task_file_name)

        test_simple_assignment(conn)
        teach = db.get_user(conn, "opettaja", "opettaja")
        c = db.select_courses_teacher(conn, teach.id)[0]
        name = get_random_unicode(10)
        reveal = pytz.utc.localize(datetime.datetime.utcnow())
        deadline = random_datetime()

        a_id, _ = db.insert_assignment(
            conn, teach.id, c.id, name, deadline, reveal, [werk_file])

        task_name = get_random_unicode(10)
        points = random.randint(5, 100)

        t_id = db._insert_task(conn, teach.id, 1, a_id,
                              task_name, points, [werk_task_file])

        files = db.select_file_details(conn, assignment_id=a_id)
        assert len(files) == 1
        file = files[0]
        assert file.name == secure_filename(file_name)
        now = datetime.datetime.utcnow()
        assert abs(now - file.date.replace(tzinfo=None)
                   ) < datetime.timedelta(seconds=1)

        temp.seek(0)
        bin_data = temp.read()
        db_bin_data, name = db.get_file(conn, file.id)
        assert name == file.name

        assert len(bin_data) > 1000
        assert len(bin_data) == len(db_bin_data)
        assert type(bin_data) == type(db_bin_data), "Wrong types (can't compare) " + \
            str(type(bin_data))+" vs "+str(type(db_bin_data))
        assert bin_data == db_bin_data

        task_files = db.select_file_details(conn, task_id=t_id)

        assert len(task_files) == 1
        file = task_files[0]
        task_temp.seek(0)
        real_task_bin_data = task_temp.read()
        db_bin_task_data, name = db.get_file(conn, file.id)
        assert name == secure_filename(task_file_name)
        assert real_task_bin_data == db_bin_task_data


def test_file_update(conn):
    from application import db
    results1 = create_dummy(db)
    results2 = create_dummy(db)
    try:
        user1 = db.get_user_by_id(conn, results1["teacher_id"])
        user2 = db.get_user_by_id(conn, results2["teacher_id"])

        course1 = db.select_courses_teacher(conn, user1.get_id())[0]
        course2 = db.select_courses_teacher(conn, user2.get_id())[0]

        assert isinstance(course1, Course)
        assert isinstance(course2, Course)

        db.set_assignments(conn, course1, for_student=False)
        db.set_assignments(conn, course2, for_student=False)
        assignments1 = []
        assignments2 = []
        for a in course1.assignments:
            assignments1.append(db.select_assignment(
                conn, a.id, set_task_files=True))

        for a in course2.assignments:
            assignments2.append(db.select_assignment(
                conn, a.id, set_task_files=True))

        task_dict1 = db.select_submits(
            conn, [user1.get_id()]).get(user1.get_id())
        task_dict2 = db.select_submits(
            conn, [user2.get_id()]).get(user2.get_id())

        assert task_dict1
        assert task_dict2
        all_assignment1_files = []
        for a in assignments1:
            assert a.files
            assert len(a.files) == results1["assignment_file_count"]
            all_assignment1_files += a.files
            for t in a.tasks:
                all_assignment1_files += t.files
                assert isinstance(t, Task)

                assert len(t.files) == results1["task"+str(t.id)+"_file_count"]

                db.set_task_answer(conn, t, for_student=False)
                assert t.answer is not None
                assert isinstance(t.answer, Answer)

                correct_answer_id = results1[str(t.id)+"answer_id"]
                assert t.id == correct_answer_id

                assert len(t.answer.files) == results1[str(
                    t.id)+"answer_file_count"]

                submit = task_dict1[t.id]
                assert isinstance(submit, Submit)
                assert submit.id==results1[str(t.id)+"submit_id"]
                
                assert submit.files
                assert len(submit.files)==results1["submit"+str(submit.id)+"file_count"]
                all_assignment1_files += submit.files

        assert len(all_assignment1_files) > 20
        for f in all_assignment1_files:
            assert isinstance(f, File)

        all_assignment1_files_ids = [str(f.id) for f in all_assignment1_files]
        for i in all_assignment1_files_ids:
            assert isinstance(i, str)
            
        for f in all_assignment1_files:
            assert str(f.id) in all_assignment1_files_ids

        assert len(all_assignment1_files_ids) == len(all_assignment1_files)

        all_assignment2_files = []
        for a in assignments2:
            assert a.files
            assert len(a.files) == results2["assignment_file_count"]
            all_assignment2_files += a.files
            for t in a.tasks:
                assert isinstance(t, Task)
                assert t.files
                assert len(t.files) == results2["task"+str(t.id)+"_file_count"]
                all_assignment2_files += t.files

                db.set_task_answer(conn, t, for_student=False)
                assert t.answer is not None
                assert isinstance(t.answer, Answer)
                correct_answer_id = results2[str(t.id)+"answer_id"]
                assert t.id == correct_answer_id
                assert len(t.answer.files) == results2[str(
                    t.id)+"answer_file_count"]
                all_assignment2_files += t.answer.files

                submit = task_dict2[t.id]
                assert isinstance(submit, Submit)
                assert submit.id==results2[str(t.id)+"submit_id"]
                
                assert submit.files
                assert len(submit.files)==results2["submit"+str(submit.id)+"file_count"]
                

                all_assignment2_files += submit.files

    
        for f in all_assignment2_files:
            assert f not in all_assignment1_files
            assert str(f.id) not in all_assignment1_files_ids
        
        #modify a1
        all_deleted_files = {}
        new_files = {}
        new_file_count= 0
        for a in assignments1:
            a_file_ids = [f.id for f in a.files]
            a_deleted = random.sample(a_file_ids, len(a_file_ids)-1) 
            insert_files = []
            for _ in range(3):
                werk_file= generate_random_werk_file(length=10)
                insert_files.append(werk_file)
                results1["all_files"].append(werk_file)
            db.update_file(conn, user1.id, insert_files, assignment_id=a.id, files_to_delete=a_deleted)
            all_deleted_files["assignment"+str(a.id)]=a_deleted

            new_files["assignment"+str(a.id)]=insert_files
            new_file_count+=len(insert_files)
            for t in a.tasks:
                t_file_ids = [f.id for f in t.files]
                t_deleted = random.sample(t_file_ids, len(t_file_ids)-1)
                insert_files = []
                for _ in range(3):
                    werk_file= generate_random_werk_file(length=10)
                    insert_files.append(werk_file)
                    results1["all_files"].append(werk_file)

                new_files["task"+str(t.id)]=insert_files
                db.update_file(conn, user1.id, insert_files, task_id=t.id, files_to_delete=t_deleted)
                all_deleted_files["task"+str(t.id)]=t_deleted
                new_file_count+=len(insert_files)

                a_file_ids = [f.id for f in t.answer.files]
                deleted = random.sample(a_file_ids, len(a_file_ids)-3)
                insert_files = []
                for _ in range(3):
                    werk_file= generate_random_werk_file(length=10)
                    insert_files.append(werk_file)
                    results1["all_files"].append(werk_file)

                new_files["answer"+str(t.id)]=insert_files
                db.update_file(conn, user1.id, insert_files, answer_id=t.answer.id, files_to_delete=deleted)
                all_deleted_files["answer"+str(t.answer.id)]=t_deleted
                new_file_count+=len(insert_files)

                submit = task_dict1[t.id]
                s_file_ids = [f.id for f in submit.files]
                deleted = random.sample(s_file_ids, len(s_file_ids)-5)
                insert_files = []
                for _ in range(3):
                    werk_file= generate_random_werk_file(length=10)
                    insert_files.append(werk_file)
                    results1["all_files"].append(werk_file)

                new_files["submit"+str(t.id)]=insert_files
                db.update_file(conn, user1.id, insert_files, submit_id=submit.id, files_to_delete=deleted)
                all_deleted_files["submit"+str(t.answer.id)]=deleted
                new_file_count+=len(insert_files)

        sql = Select([db.file.c.id])
        rs = conn.execute(sql)
        all_ids = []
        for row in rs:
            all_ids.append(int(row[db.file.c.id]))
        assert len(all_ids) >120

        
        
        x=len(all_assignment2_files)+new_file_count
        deleted_ids = []
        for i in all_deleted_files.values():
            deleted_ids+=i
        for i in deleted_ids:
            assert isinstance(i, int)

        for i in deleted_ids:
            assert int(i) not in all_ids

        for i in all_ids:
            assert isinstance(i, int)


        for i in all_assignment1_files_ids:
            if int(i) not in deleted_ids:
                x+=1
                assert int(i) in all_ids
                
        correct_count = len(all_assignment1_files_ids)+len(all_assignment2_files)-len(deleted_ids)+new_file_count
        # assert x==correct_count

        # assert len(all_ids)==x

        #Test a2 stays the same, when a1 is modified
        
        for a in assignments2:
            assert a.files
            assert len(a.files) == results2["assignment_file_count"]
            for f in a.files:
                assert f in all_assignment2_files
            for t in a.tasks:

                for f in t.files:
                    assert f in all_assignment2_files
                assert isinstance(t, Task)
                assert t.files
                assert len(t.files) == results2["task"+str(t.id)+"_file_count"]
                

                db.set_task_answer(conn, t, for_student=False)
                assert t.answer is not None
                assert isinstance(t.answer, Answer)
                correct_answer_id = results2[str(t.id)+"answer_id"]
                assert t.id == correct_answer_id
                assert len(t.answer.files) == results2[str(
                    t.id)+"answer_file_count"]

                for f in t.answer.files:
                    assert f in all_assignment2_files

                submit = task_dict2[t.id]
                assert isinstance(submit, Submit)
                assert submit.id==results2[str(t.id)+"submit_id"]
                
                assert submit.files
                assert len(submit.files)==results2["submit"+str(submit.id)+"file_count"]
                for f in submit.files:
                    assert f in all_assignment2_files

                

    finally:
        for file in results1["all_files"]:
            file.close()

        for file in results2["all_files"]:
            file.close()


def test_file_log(conn):
    from application import db

def test_file_update_throws(conn):
    from application import db
    with pytest.raises(ValueError):
        db.update_file(conn, 2, [1,2,3], files_to_delete=[1,2,3,6])

    sql = Select([db.file])
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        assert row is None

def test_db_file_insert_constraint(conn):
    from application import db
    s = "nothing"
    db.insert_user(conn, s, s, s, s, role="TEACHER")
    user_id = db.get_user(conn, s, s).get_id()

    with pytest.raises(IntegrityError):
        file_insert_helper(db, user_id=user_id, binary_file=io.BytesIO(
            b"useless bytes").read())

    sql = Select([db.file])
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        assert row is None
