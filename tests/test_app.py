import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

# preserve the original dictionary so tests can reset state
ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)

@pytest.fixture(autouse=True)
def reset_activities():
    """Clear and restore activities before each test."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))


def test_root_redirect():
    # disable automatic redirects so we can inspect the response
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302, 307)  # FastAPI typically uses 307
    assert resp.headers.get("location", "").endswith("/static/index.html")


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # check presence of a known activity and structure
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_success():
    email = "newstudent@mergington.edu"
    resp = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 200
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate():
    email = "michael@mergington.edu"
    # first signup should already be present in original data
    resp = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )
    assert resp.status_code == 400
    assert "already signed up" in resp.json().get("detail", "")


def test_signup_nonexistent():
    email = "foo@bar.com"
    resp = client.post(
        "/activities/NoSuch/signup", params={"email": email}
    )
    assert resp.status_code == 404


def test_unsubscribe_success():
    email = "michael@mergington.edu"
    assert email in app_module.activities["Chess Club"]["participants"]
    resp = client.post(
        "/activities/Chess Club/unsubscribe", params={"email": email}
    )
    assert resp.status_code == 200
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unsubscribe_not_signed():
    email = "nonexistent@mergington.edu"
    resp = client.post(
        "/activities/Chess Club/unsubscribe", params={"email": email}
    )
    assert resp.status_code == 400
    assert "not signed up" in resp.json().get("detail", "")


def test_unsubscribe_nonexistent_activity():
    resp = client.post(
        "/activities/NoActivity/unsubscribe", params={"email": "a@b.com"}
    )
    assert resp.status_code == 404
