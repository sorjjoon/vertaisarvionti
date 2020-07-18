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

from application.auth.account import account
from application.domain.course import Course
from .db_fixture import conn, get_random_unicode, random_datetime

from .db_fixture import insert_users

def test_simple_comment(conn):
    from application import db
    teachers, students = insert_users(db)
    t= teachers[0]
    s = students[0]
    c = Course(get_random_unicode(29), get_random_unicode(50), abbreviation=get_random_unicode(3))
    id, _ = db.insert_course(conn, c, t.id)
    text = "eka "+get_random_unicode(200)
    reveal = random_datetime()
    comment_id = db.insert_comment(conn, t.id, text, reveal=reveal, course_id=id)
    assert comment_id is not None
    comments = db.select_comments(conn, t.id, course_id=id)
    assert isinstance(comments, list)
    assert len(comments) ==1
    c = comments[0]
    assert c.text == text
    assert c.reveal == reveal
    
    empty = db.select_comments(conn, s.id, course_id=id)
    assert isinstance(empty, list)
    assert not empty


    text = "toka "+get_random_unicode(200)
    reveal = None
    comment_id = db.insert_comment(conn, t.id, text, reveal=reveal, course_id=id)
    assert comment_id is not None
    comments = db.select_comments(conn, t.id, course_id=id)
    assert isinstance(comments, list)
    assert len(comments) ==2
    c = comments[1]
    assert c.text == text
    assert c.reveal <= pytz.timezone("UTC").localize(datetime.datetime.utcnow())


    comments2 = db.select_comments(conn, s.id, course_id=id)
    assert len(comments2)==1
    visible_comment = comments2[0]
    assert c == visible_comment


def test_raises_error(conn):
    from application import db

    with pytest.raises(ValueError) as r:
        db.insert_comment(conn, 1, "moi")
    assert "all arguments" in str(r.value)

    teachers, _ = insert_users(db)
    t= teachers[0]
    json_dic={}
    json_dic["user_id"]=t.id
    json_dic["text"]="something"
    with pytest.raises(IntegrityError) as r:
        db.insert_comment_dict(conn, json_dic)
    assert "null_comment_foreign_keys" in str(r.value), "null_comment_foreign_keys not found in "+str(r.value)