"""
Tests for the activities API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestActivitiesEndpoints:
    """Test class for activities API endpoints."""

    def test_get_activities_returns_all_activities(self, client: TestClient, reset_activities):
        """Test that GET /activities returns all activities with correct structure."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        
        # Check that we have the expected activities
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
        
        # Check structure of an activity
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        # Check data types
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["max_participants"], int)
        assert isinstance(chess_club["participants"], list)
        
        # Check initial participants
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

    def test_get_activities_returns_proper_json_structure(self, client: TestClient, reset_activities):
        """Test that GET /activities returns properly formatted JSON."""
        response = client.get("/activities")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        activities = response.json()
        assert isinstance(activities, dict)
        
        # Each activity should have all required fields
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data

    def test_signup_for_activity_success(self, client: TestClient, reset_activities):
        """Test successful signup for an activity."""
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]
        
        # Verify the participant was actually added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_for_nonexistent_activity(self, client: TestClient, reset_activities):
        """Test signup for an activity that doesn't exist."""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert result["detail"] == "Activity not found"

    def test_signup_duplicate_prevention(self, client: TestClient, reset_activities):
        """Test that a student cannot sign up for multiple activities."""
        email = "student@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup for different activity should fail
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 400
        result = response2.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]

    def test_signup_already_registered_student(self, client: TestClient, reset_activities):
        """Test signup for a student already registered in any activity."""
        # michael@mergington.edu is already in Chess Club
        email = "michael@mergington.edu"
        
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"]

    def test_unregister_from_activity_success(self, client: TestClient, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Already registered in Chess Club
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity_name in result["message"]
        
        # Verify the participant was actually removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_from_nonexistent_activity(self, client: TestClient, reset_activities):
        """Test unregistration from an activity that doesn't exist."""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert result["detail"] == "Activity not found"

    def test_unregister_non_participant(self, client: TestClient, reset_activities):
        """Test unregistration of someone not registered for the activity."""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "not registered" in result["detail"]

    def test_complete_signup_unregister_workflow(self, client: TestClient, reset_activities):
        """Test complete workflow of signup and then unregister."""
        email = "workflow@mergington.edu"
        activity_name = "Programming Class"
        
        # Initial check - user not registered
        activities_response = client.get("/activities")
        activities = activities_response.json()
        initial_count = len(activities[activity_name]["participants"])
        assert email not in activities[activity_name]["participants"]
        
        # Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count

    def test_root_redirect(self, client: TestClient):
        """Test that root path redirects to static files."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"