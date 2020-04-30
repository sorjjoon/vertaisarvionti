

import os
import tempfile
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import pytest
from flask import url_for
import io
from db_fixture import db_test_client
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, outerjoin)
from application.auth.account import account
def insert_users(db, n, roles=["USER", "TEACHER"]):
    for _ in range(n):
        acc = account()

        db.insert_user
    
def test_user_insert(db_test_client):
    from application import db
    db.insert_user("oppilas", "oppilas", "Tessa", "Testaaja")
    with pytest.raises(IntegrityError):
        db.insert_user("oppilas", "oppilas", "Tessa", "Testaaja")
    j = db.account.join(db.role)
    sql = Select([func.count(db.account.c.username) , db.role.c.name]).select_from(j)
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        count = row [0]
        role = row[1]
        assert 1==count
        assert "USER" == role
    db.insert_user("opettaja", "opettaja", "Essi", "Esimerkki", role="TEACHER")
    sql = Select([func.count(db.account.c.username) , db.role.c.name]).select_from(j).where(db.role.c.name == "TEACHER")
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        count = row [0]
        role = row[1]
        assert 1==count
        assert "TEACHER" == role
    
    student = db.get_user_by_id(1)
    teacher = db.get_user_by_id(2)
    null = db.get_user_by_id(3)
    assert student.name == "oppilas"
    assert teacher.name == "opettaja"
    assert null == None

from random import choice

def test_weird_chars_large_set(db_test_client, random_roles = True):
    from application import db
    username = "*ÄÖpÖÄPäöLÄ"
    password = "äåäÖÅÄÖÄL=(!=!?)"
    first = "ääöäöpöpäÖPLÄPLÄ"
    last = "ÄÅÄÖÖÖÄÅ,.1,.,ösa"
    db.insert_user(username, password, first, last)
    a1= db.get_user(username, password)
    assert a1.first_name == first
    assert a1.last_name == last
    null = db.get_user("something", "something")
    assert null == None

    from db_fixture import get_random_unicode
    usernames = []
    passwords = []
    firsts = []
    lasts = []
    roles = []
    for i in range(20):
        username = get_random_unicode(30)
        password = get_random_unicode(30)
        
        first = get_random_unicode(20)
        last = get_random_unicode(35)

        usernames.append(username)
        passwords.append(password)
        firsts.append(first)
        lasts.append(last)
        if random_roles:
            role = choice(["USER", "TEACHER"])
        else:
            a = ["TEACHER", "USER"]
            role = a[i%2]
        roles.append(role)

        db.insert_user(username, password, first, last, role=role)

    ids = []
    for username, password, first, last, role in zip(usernames, passwords, firsts, lasts, roles):
        acc = db.get_user(username, password)
        assert acc is not None

        assert acc.last_name == last
        assert acc.first_name == first
        assert acc.role == role

        acc2 = db.get_user_by_id(acc.id)
        

        assert acc2.id == acc.id
        assert acc.id not in ids

        assert acc.last_name == acc2.last_name
        assert acc.first_name == acc2.first_name
        assert acc.role == acc2.role
        assert acc.name == acc2.name

        ids.append(acc.id)
    return ids
    