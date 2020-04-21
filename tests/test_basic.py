
import os
import tempfile

import pytest

from application import create_app
from flask import url_for
import io

@pytest.fixture(scope="module")
def test_client():
    
    
    app = create_app("test")
 
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = app.test_client()
 
    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()
 
    yield testing_client  # this is where the testing happens!
    
    ctx.pop()



@pytest.mark.run(order=1)
def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check the response is valid and redirected
    """

    response = test_client.get('/',  follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Kirjaudu" in response.data
    assert b"alasana" in response.data
    assert b"nimi" in response.data

@pytest.mark.run(order=2)
def test_login_logout(test_client): #TODO register
    login_response = test_client.post("auth/login", data=dict(
        username="12345678",
        password="12345678"
    ), follow_redirects=True)
    assert login_response.status_code == 401
    res = test_client.post("auth/register", data=dict(
        username="öylättiöäöl",
        password="öylättiöäöl",
        password2="öylättiöäöl",
        first_name = "Tessa",
        last_name = "Testaaja"
        
    ))
    assert res.status_code == 302

    login_response = test_client.post("auth/login", data=dict(
        username="öylättiöäöl",
        password="öylättiöäöl"
    ), follow_redirects=True)
    assert login_response.status_code == 200
    assert b"Hei Tessa" in login_response.data
    assert b"Kirjaudu Ulos" in login_response.data
    assert b"Uusi Kurssi" in login_response.data
    logout_response = test_client.get("/auth/logout", follow_redirects=True)

    assert b"Kirjaudu" in logout_response.data
    assert b"Kirjaudu Ulos" not in logout_response.data



@pytest.mark.run(order=3)
def test_create_course(test_client):
    res = test_client.post("auth/login", data=dict(
        username="öylättiöäöl",
        password="öylättiöäöl"
    ), follow_redirects=True)
    
    assert res.status_code == 200

    res = test_client.post("/new", data=dict(
        name="Oulun testi kurssi",
        description= "tosi hieno kurssi",
        end_date = "2022-05-07"
    ), follow_redirects=True)

    res = test_client.get("/courses", follow_redirects=True)
    assert res.status_code == 200
    assert b"kurssi" in res.data
    assert b"Oulun testi kurssi" in res.data
    assert b"2022" in res.data and b"05" in res.data and b"07" in res.data
    logout_response = test_client.get("/auth/logout", follow_redirects=True)

@pytest.mark.run(order=4)
def test_task_add(test_client):
    res = test_client.post("auth/login", data=dict(
        username="öylättiöäöl",
        password="öylättiöäöl"
    ), follow_redirects=True)
    
    assert res.status_code == 200
    
    data=dict(
        name="Eka testi",
        description= "tosi turha tehtanto",
        deadline = "2022-04-21T15",
        reveal = "2019-06-21T15"
        
    )
    data["tasks-0-points"] = "12"
    data["tasks-0-brief"] ="huono testi tehtävä"
    data["task-0-files"] = io.BytesIO(b"testi tiedosto")
    res = test_client.post("/view/1/new",content_type='multipart/form-data', data=data, follow_redirects = True)
    assert res.status_code == 200

    res = test_client.get('/view/1?s=1')
    assert res.status_code == 200
    assert b"Eka testi" in res.data
    logout_response = test_client.get("/auth/logout", follow_redirects=True)
    