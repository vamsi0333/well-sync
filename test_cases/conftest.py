import pytest
from app import app as flask_app
from database_helper import DatabaseHelper
import os
import tempfile

@pytest.fixture
def app():
    db_fd, flask_app.config['DATABASE'] = tempfile.mkstemp()
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False

    yield flask_app

    os.close(db_fd)
    os.unlink(flask_app.config['DATABASE'])

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db():
    db = DatabaseHelper()
    return db
