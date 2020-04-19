import os
import tempfile

import pytest

from application import app

@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            print("moi")
        yield client

    os.close(db_fd)


