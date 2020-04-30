import os
import tempfile

import pytest

from application import create_app
from flask import url_for
import io

@pytest.fixture(scope="module")
def test_client():
    
    
    app = create_app("NET_TEST")
 
    # Flask provides a way to test your application by exposing the Werkzeug test Client
    # and handling the context locals for you.
    testing_client = app.test_client()
 
    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()
 
    yield testing_client  
    
    ctx.pop()