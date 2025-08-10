# tests/conftest.py
import os
import pytest
from src.app import create_app
from src.model import db, Exercise


@pytest.fixture(scope="session")
def app():
    # Use in-memory DB for tests; set a test JWT secret
    os.environ["DATABASE_URL"] = "sqlite://"
    os.environ["JWT_SECRET"] = "test-secret"

    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.create_all()
        # seed one exercise (id will be 1)
        db.session.add(
            Exercise(
                name="Squat",
                description="test",
                category="strength",
                muscle_group="legs",
            )
        )
        db.session.commit()
    yield app

    # teardown
    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


# tests/conftest.py (only the token fixture shown)
@pytest.fixture()
def token(client):
    email = "test@example.com"
    password = "pass123"

    r = client.post("/auth/signup", json={"email": email, "password": password})
    if r.status_code == 409:  # already exists
        r = client.post("/auth/login", json={"email": email, "password": password})

    assert r.status_code in (200, 201), r.get_data(as_text=True)
    return r.get_json()["access_token"]
