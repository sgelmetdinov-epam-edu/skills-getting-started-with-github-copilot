import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def activities(monkeypatch):
    activity_data = {
        "Chess Club": {
            "description": "Strategy club",
            "schedule": "Mondays",
            "max_participants": 2,
            "participants": ["student@example.com"],
        },
        "Full Club": {
            "description": "At capacity",
            "schedule": "Tuesdays",
            "max_participants": 1,
            "participants": ["full@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", activity_data)
    return activity_data


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, activities):
    # Arrange
    expected_activities = activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activities):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert activities["Chess Club"]["participants"] == [
        "student@example.com",
        email,
    ]


def test_signup_rejects_duplicate_participant(client, activities):
    # Arrange
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities["Chess Club"]["participants"] == [email]


def test_signup_rejects_unknown_activity(client, activities):
    # Arrange
    email = "new@example.com"

    # Act
    response = client.post("/activities/Unknown%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_full_activity_without_mutating_participants(client, activities):
    # Arrange
    email = "new@example.com"
    original_participants = activities["Full Club"]["participants"].copy()

    # Act
    response = client.post("/activities/Full%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 409
    assert response.json() == {"detail": "Activity is full"}
    assert activities["Full Club"]["participants"] == original_participants


def test_signup_accepts_last_available_seat(client, activities):
    # Arrange
    email = "last-seat@example.com"

    # Act
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert activities["Chess Club"]["participants"] == [
        "student@example.com",
        email,
    ]


def test_unregister_removes_participant(client, activities):
    # Arrange
    email = activities["Chess Club"]["participants"][0]

    # Act
    response = client.delete(
        "/activities/Chess%20Club/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert activities["Chess Club"]["participants"] == []


def test_unregister_rejects_unknown_activity(client, activities):
    # Arrange
    email = "student@example.com"

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unregistered_email(client, activities):
    # Arrange
    email = "unregistered@example.com"

    # Act
    response = client.delete(
        "/activities/Chess%20Club/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities["Chess Club"]["participants"] == ["student@example.com"]