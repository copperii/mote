import os
import pytest
from flask import current_app
from mote.app import create_app


@pytest.fixture
def app():
    app = create_app("development")
    yield app


@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app("production")

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!


def test_home_page_get_with_fixture(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    # Note, do not use "møte" as it breaks the test, bug in testing software for "foreign" letters
    assert b"allows the Fedora community to search and explore IRC meetings." in response.data
    assert b"Latest Meetings" in response.data
    assert b"meeting wrangler" in response.data


def test_home_page_post_with_fixture(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is is posted to (POST)
    THEN check that a '405' status code is returned
    """
    response = test_client.post('/')
    assert response.status_code == 405
    assert b"meeting wrangler" not in response.data


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


def test_client_get(client):
    """Starts a client."""
    assert client is not None
