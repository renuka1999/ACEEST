"""
ACEest Fitness & Gym - Pytest Test Suite
Tests all core Flask API endpoints and application logic.
"""

import pytest
import json
import os
import tempfile
from app import app, init_db, PROGRAMS


# ---------- FIXTURES ----------

@pytest.fixture
def client():
    """
    Create a test Flask client with a temporary database.
    Each test gets a fresh, isolated database.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app.config["TESTING"] = True
    os.environ["DB_NAME"] = db_path

    # Re-init db for test isolation
    import app as app_module
    app_module.DB_NAME = db_path
    init_db()

    with app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    os.unlink(db_path)


# ---------- HOME & HEALTH ----------

class TestHomeAndHealth:
    def test_home_returns_200(self, client):
        """GET / should return 200 — dashboard HTML page."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client):
        """GET / should return HTML content (the dashboard), not JSON."""
        response = client.get("/")
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_home_contains_aceest_branding(self, client):
        """Dashboard HTML should contain the ACEest brand name."""
        response = client.get("/")
        assert b"ACEest" in response.data

    def test_health_returns_200(self, client):
        """GET /health should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, client):
        """GET /health should return JSON with status: healthy."""
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "healthy"

    def test_health_returns_json(self, client):
        """GET /health should return valid JSON."""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_stats_endpoint(self, client):
        """GET /api/stats should return dashboard statistics."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_clients" in data
        assert "active_clients" in data
        assert "total_workouts" in data
        assert "avg_adherence" in data


# ---------- PROGRAMS ----------

class TestPrograms:
    def test_get_programs_returns_200(self, client):
        """GET /programs should return 200."""
        response = client.get("/api/programs")
        assert response.status_code == 200

    def test_get_programs_contains_keys(self, client):
        """Programs response must include Fat Loss, Muscle Gain, Beginner."""
        response = client.get("/api/programs")
        data = json.loads(response.data)
        assert "Fat Loss" in data["programs"]
        assert "Muscle Gain" in data["programs"]
        assert "Beginner" in data["programs"]

    def test_get_specific_program_fat_loss(self, client):
        """GET /programs/Fat Loss should return details."""
        response = client.get("/api/programs/Fat Loss")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["program"] == "Fat Loss"
        assert "workout" in data["details"]
        assert "diet" in data["details"]

    def test_get_specific_program_muscle_gain(self, client):
        """GET /programs/Muscle Gain should return correct calories."""
        response = client.get("/api/programs/Muscle Gain")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["details"]["calories"] == 3200

    def test_get_invalid_program_returns_404(self, client):
        """GET /programs/NonExistent should return 404."""
        response = client.get("/api/programs/NonExistent")
        assert response.status_code == 404

    def test_programs_data_integrity(self):
        """All programs in PROGRAMS dict must have workout, diet, calories."""
        for name, details in PROGRAMS.items():
            assert "workout" in details, f"'{name}' missing workout"
            assert "diet" in details, f"'{name}' missing diet"
            assert "calories" in details, f"'{name}' missing calories"
            assert isinstance(details["calories"], int)


# ---------- CLIENTS ----------

class TestClients:
    def _add_client(self, client, name="TestUser", program="Beginner", weight=70.0, age=25):
        return client.post("/api/clients", json={
            "name": name,
            "age": age,
            "weight": weight,
            "program": program
        })

    def test_get_clients_empty(self, client):
        """GET /clients on empty DB should return empty list."""
        response = client.get("/api/clients")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["clients"] == []

    def test_add_client_success(self, client):
        """POST /clients should create a client and return 201."""
        response = self._add_client(client)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["client"]["name"] == "TestUser"

    def test_add_client_missing_name(self, client):
        """POST /clients without name should return 400."""
        response = client.post("/api/clients", json={"age": 25})
        assert response.status_code == 400

    def test_add_duplicate_client(self, client):
        """Adding same client twice should return 409."""
        self._add_client(client, name="DupeUser")
        response = self._add_client(client, name="DupeUser")
        assert response.status_code == 409

    def test_add_client_invalid_program(self, client):
        """POST /clients with invalid program should return 400."""
        response = client.post("/api/clients", json={"name": "BadUser", "program": "Yoga Nidra"})
        assert response.status_code == 400

    def test_get_client_by_name(self, client):
        """GET /clients/<name> should return the correct client."""
        self._add_client(client, name="Arjun")
        response = client.get("/api/clients/Arjun")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["client"]["name"] == "Arjun"

    def test_get_nonexistent_client(self, client):
        """GET /clients/<name> for missing client should return 404."""
        response = client.get("/api/clients/Ghost")
        assert response.status_code == 404

    def test_delete_client(self, client):
        """DELETE /clients/<name> should remove the client."""
        self._add_client(client, name="DeleteMe")
        response = client.delete("/api/clients/DeleteMe")
        assert response.status_code == 200
        # Verify client is gone
        check = client.get("/api/clients/DeleteMe")
        assert check.status_code == 404

    def test_delete_nonexistent_client(self, client):
        """DELETE on non-existent client should return 404."""
        response = client.delete("/api/clients/NoOne")
        assert response.status_code == 404

    def test_client_calories_set_by_program(self, client):
        """Client calories should match the selected program's calorie target."""
        self._add_client(client, name="FatLossUser", program="Fat Loss")
        response = client.get("/api/clients/FatLossUser")
        data = json.loads(response.data)
        assert data["client"]["calories"] == PROGRAMS["Fat Loss"]["calories"]


# ---------- WORKOUTS ----------

class TestWorkouts:
    def _setup_client(self, client):
        client.post("/api/clients", json={"name": "WorkoutUser", "age": 28, "weight": 75.0, "program": "Muscle Gain"})

    def test_add_workout_success(self, client):
        """POST /clients/<name>/workout should return 201."""
        self._setup_client(client)
        response = client.post("/api/clients/WorkoutUser/workout", json={
            "workout_type": "Strength",
            "duration_min": 60,
            "notes": "Felt strong today"
        })
        assert response.status_code == 201

    def test_add_workout_unknown_client(self, client):
        """POST workout for unknown client should return 404."""
        response = client.post("/api/clients/NoClient/workout", json={"workout_type": "Cardio"})
        assert response.status_code == 404

    def test_get_workouts_empty(self, client):
        """GET workouts for client with no workouts returns empty list."""
        self._setup_client(client)
        response = client.get("/api/clients/WorkoutUser/workouts")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["workouts"] == []

    def test_get_workouts_after_add(self, client):
        """GET workouts should return added workout."""
        self._setup_client(client)
        client.post("/api/clients/WorkoutUser/workout", json={
            "workout_type": "Hypertrophy",
            "duration_min": 75,
            "date": "2025-01-15"
        })
        response = client.get("/api/clients/WorkoutUser/workouts")
        data = json.loads(response.data)
        assert len(data["workouts"]) == 1
        assert data["workouts"][0]["workout_type"] == "Hypertrophy"


# ---------- PROGRESS ----------

class TestProgress:
    def _setup_client(self, client):
        client.post("/api/clients", json={"name": "ProgressUser", "age": 30, "weight": 80.0, "program": "Fat Loss"})

    def test_log_progress_success(self, client):
        """POST /clients/<name>/progress with valid adherence returns 201."""
        self._setup_client(client)
        response = client.post("/api/clients/ProgressUser/progress", json={
            "adherence": 85,
            "week": "2025-W10"
        })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["adherence"] == 85

    def test_log_progress_invalid_adherence_over_100(self, client):
        """Adherence > 100 should return 400."""
        self._setup_client(client)
        response = client.post("/api/clients/ProgressUser/progress", json={"adherence": 110})
        assert response.status_code == 400

    def test_log_progress_invalid_adherence_negative(self, client):
        """Negative adherence should return 400."""
        self._setup_client(client)
        response = client.post("/api/clients/ProgressUser/progress", json={"adherence": -5})
        assert response.status_code == 400

    def test_log_progress_boundary_zero(self, client):
        """Adherence of 0 should be valid."""
        self._setup_client(client)
        response = client.post("/api/clients/ProgressUser/progress", json={"adherence": 0})
        assert response.status_code == 201

    def test_log_progress_boundary_hundred(self, client):
        """Adherence of 100 should be valid."""
        self._setup_client(client)
        response = client.post("/api/clients/ProgressUser/progress", json={"adherence": 100})
        assert response.status_code == 201

    def test_log_progress_unknown_client(self, client):
        """Progress for unknown client should return 404."""
        response = client.post("/api/clients/Ghost/progress", json={"adherence": 50})
        assert response.status_code == 404


# ---------- BMI ----------

class TestBMI:
    def _setup_client(self, client):
        client.post("/api/clients", json={"name": "BMIUser", "age": 25, "weight": 70.0, "program": "Beginner"})

    def test_calculate_bmi_success(self, client):
        """GET /clients/<name>/bmi with valid params should return BMI."""
        self._setup_client(client)
        response = client.get("/api/clients/BMIUser/bmi?height_cm=175")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "bmi" in data
        assert "category" in data

    def test_bmi_correct_value(self, client):
        """BMI for 70kg / 175cm should be approximately 22.86."""
        self._setup_client(client)
        response = client.get("/api/clients/BMIUser/bmi?height_cm=175")
        data = json.loads(response.data)
        assert abs(data["bmi"] - 22.86) < 0.1

    def test_bmi_normal_weight_category(self, client):
        """70kg / 175cm should classify as Normal weight."""
        self._setup_client(client)
        response = client.get("/api/clients/BMIUser/bmi?height_cm=175")
        data = json.loads(response.data)
        assert data["category"] == "Normal weight"

    def test_bmi_no_height_returns_400(self, client):
        """BMI without height_cm param should return 400."""
        self._setup_client(client)
        response = client.get("/api/clients/BMIUser/bmi")
        assert response.status_code == 400

    def test_bmi_unknown_client_returns_404(self, client):
        """BMI for unknown client should return 404."""
        response = client.get("/api/clients/Nobody/bmi?height_cm=170")
        assert response.status_code == 404

    def test_bmi_categories(self):
        """BMI category thresholds should be logically correct."""
        # Simulate category logic
        def get_category(bmi):
            if bmi < 18.5:
                return "Underweight"
            elif bmi < 25:
                return "Normal weight"
            elif bmi < 30:
                return "Overweight"
            else:
                return "Obese"

        assert get_category(17.0) == "Underweight"
        assert get_category(22.0) == "Normal weight"
        assert get_category(27.5) == "Overweight"
        assert get_category(32.0) == "Obese"