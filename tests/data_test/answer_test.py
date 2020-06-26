
import datetime
import io
import os
import random
import unittest

from werkzeug.datastructures import FileMultiDict, FileStorage
from werkzeug.utils import secure_filename

import pytest
import pytz
from flask import url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)

from application.domain.assignment import Assignment, Task, Answer, File
from application.domain.course import Course

from .user_test import  insert_users
from .file_test import generate_random_file

from .db_fixture import (db_test_client, format_error, get_random_unicode,
                         insert_random_courses, random_datetime)


def test_simple_answer(db_test_client):
    from application import db
    
    reveal = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(minutes=1)
    teacher = insert_users(db, 1, roles=["TEACHER"])[0]
    student = insert_users(db, 1, roles=["USER"])[0]
    c_id, code = db.insert_course(Course("something", "something",reveal), teacher.id )
    db.enlist_student(code, student.id)
    f = generate_random_file()
    file_name = secure_filename(get_random_unicode(30))
    werk_file = FileStorage(f, file_name)
    a_id = db.insert_assignment(teacher.id, c_id, "ksakas", reveal, reveal, [werk_file])
    t_id = db.insert_task(teacher.id, a_id, "something", 3, [werk_file])
    werk_file.close()
    files = []
    correct_files = FileMultiDict()
    for _ in range(5):
        f = generate_random_file()
        file_name = secure_filename(get_random_unicode(30))
        werk_file = FileStorage(f, file_name)
        files.append(werk_file)
        correct_files.add_file(file_name, werk_file)
    
    description = get_random_unicode(100)
    db.update_answer(teacher.id, t_id, files, description, reveal=random_datetime())

    assignment = db.select_assignment(a_id, task_id=t_id)

    assert assignment.name =="ksakas"

    assert len(assignment.tasks) == 1
    t = assignment.tasks[0]
    assert isinstance(t, Task)
    db.set_task_answer(assignment.tasks[0], for_student=False)

    assert t.answer is not None
    assert isinstance(t.answer, Answer)
    assert t.answer.description == description

    assert len(t.answer.files) ==5

    for db_f in t.answer.files:
        assert isinstance(db_f, File)
        c_f = correct_files.get(db_f.name)
        
        bin_file, name = db.get_file(db_f.id)
        assert name == db_f.name, "shouldn't fail... "+str(type(name))+"  "+str(type(db_f.name))
        c_f.seek(0)
        assert bin_file == c_f.read()
        c_f.close()

    db.set_task_answer(t, for_student=True)
    assert t.answer is None


def test_large_answer_insert_and_update(db_test_client):
    from application import db
    visible_reveal = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(minutes=1)
    teacher = insert_users(db, 1, roles=["TEACHER"])[0]
    course_id, _ = db.insert_course(Course("something", "somthing", visible_reveal, visible_reveal), teacher.id)
    f = generate_random_file()
    file_name = secure_filename(get_random_unicode(30))
    werk_file = FileStorage(f, file_name)
    assignment_id = db.insert_assignment(teacher.id, course_id, "somthing", random_datetime(),visible_reveal, [werk_file])
    werk_file.close()
    all_answers = []
    visible_answers = []
    visible_tasks = []
    correct_files = FileMultiDict()
    for _ in range(100):
        task_id = db.insert_task(teacher.id, assignment_id, get_random_unicode(20), 20, [])
        hidden = random.randint(0,1)
        if not hidden:
            visible_tasks.append(task_id)
            reveal = visible_reveal
        else:
            reveal = random_datetime()
        files = []
        for i in range(3):
            f = generate_random_file(length=10)
            file_name = str(task_id)+"t"+str(i)
            werk_file = FileStorage(f, file_name)
            files.append(werk_file)
            correct_files.add_file(task_id, werk_file, werk_file.filename)
        desc = get_random_unicode(30)
        id =db.update_answer(teacher.id, task_id, files, desc, reveal=reveal)
        
        
        
        answer = Answer(id, desc, reveal.replace(tzinfo=None), db.select_file_details(answer_id=id))
        all_answers.append(answer)
        if not hidden:
            visible_answers.append(answer)

    for f in files:
        f.close()
    assignment = db.select_assignment(assignment_id, for_student=False)
    all_db_answers = []
    case = unittest.TestCase()
    assert len(assignment.tasks) == 100
    for t in assignment.tasks:
        assert isinstance(t, Task)
        db.set_task_answer(t, for_student=False)
        assert t.answer is not None
        a = t.answer
        assert isinstance(a, Answer)
        assert len(a.files) == 3
        correct_filenames = [file.filename for file in correct_files.getlist(t.id)]
        assert len(correct_filenames) == 3
        db_filenames = [file.name for file in a.files]
        
        case.assertCountEqual(db_filenames, correct_filenames)
        all_db_answers.append(a)


    assert len(all_answers) == len(all_db_answers)
    case.maxDiff = None
    case.assertCountEqual(all_answers, all_db_answers)
    assignment = db.select_assignment(assignment_id, for_student=True)
    assert len(assignment.tasks) == 100

    db_visibles = []
    for t in assignment.tasks:
        assert isinstance(t, Task)
        db.set_task_answer(t, for_student=True)
        if t.id not in visible_tasks:
            assert t.answer is None
            continue
        assert t.answer is not None
        db_visibles.append(t.answer)
        a = t.answer
        assert isinstance(a, Answer)
        assert len(a.files) == 3
        correct_filenames = [file.filename for file in correct_files.getlist(t.id)]
        assert len(correct_filenames) == 3
        db_filenames = [file.name for file in a.files]
        
        case.assertCountEqual(db_filenames, correct_filenames)

    case.assertCountEqual(db_visibles, visible_answers)
        
            

            

        



