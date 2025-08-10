# tests/test_smoke.py
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_signup_and_me(client, token):
    r = client.get("/auth/me", headers=auth_header(token))
    assert r.status_code == 200
    assert r.get_json()["email"] == "test@example.com"


def test_login_returns_token(client):
    r = client.post(
        "/auth/login", json={"email": "test@example.com", "password": "pass123"}
    )
    assert r.status_code == 200
    assert "access_token" in r.get_json()


def test_create_and_list_workout(client, token):
    payload = {
        "title": "Leg Day",
        "exercises": [{"exercise_id": 1, "sets": 4, "reps": 10, "weight": 135}],
    }
    r = client.post("/workouts", json=payload, headers=auth_header(token))
    assert r.status_code == 201, r.get_data(as_text=True)
    wid = r.get_json()["id"]

    r = client.get("/workouts", headers=auth_header(token))
    assert r.status_code == 200
    ids = [w["id"] for w in r.get_json()]
    assert wid in ids


def test_delete_workout(client, token):
    # create one to delete
    r = client.post(
        "/workouts",
        json={
            "title": "Temp",
            "exercises": [{"exercise_id": 1, "sets": 3, "reps": 8, "weight": 95}],
        },
        headers=auth_header(token),
    )
    wid = r.get_json()["id"]

    r = client.delete(f"/workouts/{wid}", headers=auth_header(token))
    assert r.status_code == 200

    r = client.get(f"/workouts/{wid}", headers=auth_header(token))
    assert r.status_code == 404
