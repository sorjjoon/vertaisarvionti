

import io
import os
import random
import tempfile
from random import choice
import pytz
from datetime import datetime, timedelta
import pytest
from flask import url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)

from application.domain.account import Account
from .db_fixture import conn, get_random_unicode
from application.database.exceptions import AccountLockedError, AuthError

def insert_users(db, n, roles=["USER", "TEACHER"]):
    accs = []
    with db.engine.connect() as conn:
        for _ in range(n):
            username = get_random_unicode(20)
            password = get_random_unicode(25)
            first = get_random_unicode(13)
            last = get_random_unicode(15)
            role = random.choice(roles)
            db.insert_user(conn, username, password, first, last, role = role)
            a = db.get_user(conn, username, password)
            assert isinstance(a, Account)
            assert a.name == username
            assert a.first_name == first
            assert a.last_name == last
            assert a.role == role
            accs.append(a)
        return accs

    
def test_user_insert(conn):
    from database import db
    db.insert_user(conn, "oppilas", "oppilas", "Tessa", "Testaaja")
    with pytest.raises(IntegrityError):
        db.insert_user(conn, "oppilas", "oppilas", "Tessa", "Testaaja")
    j = db.account.join(db.role)
    sql = Select([func.count(db.account.c.username).label("acc_count"), db.role.c.name ]).select_from(j).where(db.role.c.name == "USER").group_by(db.role.c.name)
    
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        count = row [0]
        role = row[1]
        assert 1==count
        assert "USER" == role
        db.insert_user(conn, "opettaja", "opettaja", "Essi", "Esimerkki", role="TEACHER")
    sql = Select([func.count(db.account.c.username) , db.role.c.name]).select_from(j).where(db.role.c.name == "TEACHER").group_by(db.role.c.name)
    with db.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        count = row [0]
        role = row[1]
        assert 1==count
        assert "TEACHER" == role
    
        student = db.get_user(conn, "oppilas", "oppilas")
        teacher = db.get_user(conn, "opettaja", "opettaja")
        null = db.get_user(conn, "jotain", "opettaja")
    assert student.name == "oppilas"
    assert teacher.name == "opettaja"
    assert student.is_authenticated()
    assert teacher.is_authenticated()
    assert null == None


def test_weird_chars_large_set(conn, random_roles = True):
    from database import db
    username = "*ÄÖpÖÄPäöLÄ"
    password = "äåäÖÅÄÖÄL=(!=!?)"
    first = "ääöäöpöpäÖPLÄPLÄ"
    last = "ÄÅÄÖÖÖÄÅ,.1,.,ösa"
    db.insert_user(conn, username, password, first, last)
    a1= db.get_user(conn, username, password)
    assert a1.first_name == first
    assert a1.last_name == last
    null = db.get_user(conn, "something", "something")
    assert null == None

    
    usernames = []
    passwords = []
    firsts = []
    lasts = []
    roles = []
    for i in range(100):
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

        db.insert_user(conn, username, password, first, last, role=role)

    ids = []
    seen = []
    for username, password, first, last, role in zip(usernames, passwords, firsts, lasts, roles):
        assert username not in seen
        seen.append(username)

        acc = db.get_user(conn, username, password)
        assert acc is not None

        assert acc.last_name == last
        assert acc.first_name == first
        assert acc.role == role
        assert acc.is_authenticated()

        
        n= random.randint(0,5)
        for _ in range(n):
            db.get_user(conn, username, password+"jaslj")
        acc2 = db.get_user_by_id(conn, acc.id)
        assert acc2.failed_attempts==n
        if n==5:
            assert acc2.locked_until is not None
            assert not acc2.is_authenticated()
        else:
            assert acc2.locked_until is None
            assert acc2.is_authenticated()
        acc2.locked_until = None
        acc2.failed_attempts=0

        assert acc2 == acc

        ids.append(acc.id)
    return ids


def test_account_locking(conn):
    from database import db
    username1 = get_random_unicode(20)
    password1 = get_random_unicode(40)
    name1="somthing"
    last1 ="something"

    username2 = get_random_unicode(20)
    password2 = get_random_unicode(40)
    name2="something else"
    last2 ="something else"

    db.insert_user(conn, username1, password1, name1, last1)
    db.insert_user(conn, username2, password2, name2, last2)

    user1=db.get_user(conn, username1, password1)
    user2=db.get_user(conn, username2, password2)
    
    id1=user1.id
    id2=user2.id

    assert user1
    assert user2

    assert isinstance(user1, Account)
    assert isinstance(user2, Account)

    assert user1.name == username1
    assert user2.name == username2

    assert user1.failed_attempts == user2.failed_attempts == 0
    assert user1.locked_until == user2.locked_until == None

    assert user1.is_authenticated() and user2.is_authenticated()

    for _ in range(4):
        null = db.get_user(conn, username1, get_random_unicode(39))
        assert null is None

    user1=db.get_user_by_id(conn, id1)
    user2=db.get_user_by_id(conn, id2)

    assert user1.name == username1
    assert user2.name == username2

    assert user1.failed_attempts == 4
    assert user1.is_authenticated()

    assert user2.failed_attempts == 0

    assert user1.locked_until == user2.locked_until == None

    user1 = db.get_user(conn, username1, password1)
    assert user1
    assert user1.is_authenticated()

    assert isinstance(user1, Account)

    assert user1.name == username1

    assert user1.failed_attempts == user2.failed_attempts == 0
    assert user1.locked_until == user2.locked_until == None

    for _ in range(5):
        null = db.get_user(conn, username1, get_random_unicode(39))
        assert null is None 
    with pytest.raises(AccountLockedError):
        db.get_user(conn, username1, get_random_unicode(23))
    with pytest.raises(AccountLockedError):
        db.get_user(conn, username1, password1)

    locked_user1 = db.get_user_by_id(conn, id1)
    assert locked_user1.first_name == user1.first_name
    assert locked_user1.failed_attempts==5
    assert locked_user1.locked_until is not None
    assert locked_user1.locked_until.tzinfo is not None
    assert locked_user1.locked_until > (pytz.timezone("utc").localize(datetime.utcnow())+timedelta(minutes=58))
    assert not locked_user1.is_authenticated()
    same_user2 = db.get_user(conn, username2, password2)

    

    for _ in range(20):
        with pytest.raises(AccountLockedError):
            db.get_user(conn, username1, password1)
    

        same_locked_user1 = db.get_user_by_id(conn, id1)
        assert not same_locked_user1.is_authenticated()
        assert locked_user1 == same_locked_user1
        assert locked_user1.failed_attempts==5
        assert locked_user1.locked_until is not None
        assert locked_user1.locked_until == same_locked_user1.locked_until

    same_user2 = db.get_user(conn, username2, password2)

    assert same_user2 == user2

    assert user2.failed_attempts == 0
    assert user2.locked_until == None

    sql = db.account.update().values(locked_until = datetime.utcnow()-timedelta(minutes=1)).where(db.account.c.id == id1)
    with conn.begin():
        conn.execute(sql)
    
    for _ in range(4):
        null = db.get_user(conn, username1, "something")
        assert null is None

    user1 = db.get_user_by_id(conn, id1)
    assert user1 is not None

    assert user1.failed_attempts==9
    
    
    user2 = db.get_user_by_id(conn, id2)

    assert user2.locked_until is None
    assert user2.is_authenticated()
    assert user2.failed_attempts ==0
    
    non_locked_user = db.get_user(conn, username1, password1)

    assert non_locked_user.failed_attempts==0
    assert non_locked_user.locked_until is None

