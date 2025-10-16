"""
Additional edge case tests for the activities API.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import activities


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_signup_with_url_encoded_activity_name(self, client: TestClient, reset_activities):
        """Test signup with URL-encoded activity name."""
        email = "test@mergington.edu"
        # "Chess Club" URL encoded
        activity_name_encoded = "Chess%20Club"
        
        response = client.post(f"/activities/{activity_name_encoded}/signup?email={email}")
        
        assert response.status_code == 200
        
        # Verify participant was added to correct activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data["Chess Club"]["participants"]

    def test_unregister_with_url_encoded_activity_name(self, client: TestClient, reset_activities):
        """Test unregister with URL-encoded activity name."""
        email = "michael@mergington.edu"  # Already in Chess Club
        # "Chess Club" URL encoded
        activity_name_encoded = "Chess%20Club"
        
        response = client.delete(f"/activities/{activity_name_encoded}/unregister?email={email}")
        
        assert response.status_code == 200
        
        # Verify participant was removed from correct activity
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]

    def test_signup_with_special_characters_in_email(self, client: TestClient, reset_activities):
        """Test signup with special characters in email."""
        # Email with special characters (but valid) - avoiding + which gets URL decoded
        email = "test.user-tag@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]

    def test_empty_email_parameter(self, client: TestClient, reset_activities):
        """Test signup with empty email parameter."""
        response = client.post("/activities/Chess Club/signup?email=")
        
        # Should handle empty email gracefully
        # The exact behavior depends on FastAPI validation, but it shouldn't crash
        assert response.status_code in [200, 400, 422]

    def test_missing_email_parameter(self, client: TestClient, reset_activities):
        """Test signup without email parameter."""
        response = client.post("/activities/Chess Club/signup")
        
        # Should return 422 for missing required parameter
        assert response.status_code == 422

    def test_activity_name_case_sensitivity(self, client: TestClient, reset_activities):
        """Test that activity names are case-sensitive."""
        email = "test@mergington.edu"
        
        # Try with different case
        response = client.post("/activities/chess club/signup?email={email}")
        
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"

    def test_multiple_signups_and_unregisters(self, client: TestClient, reset_activities):
        """Test multiple signup and unregister operations."""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu", 
            "student3@mergington.edu"
        ]
        activity_name = "Programming Class"
        
        # Get initial participant count
        activities_response = client.get("/activities")
        initial_count = len(activities_response.json()[activity_name]["participants"])
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        current_participants = activities_response.json()[activity_name]["participants"]
        assert len(current_participants) == initial_count + len(emails)
        
        for email in emails:
            assert email in current_participants
        
        # Unregister all
        for email in emails:
            response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify all were removed
        activities_response = client.get("/activities")
        final_participants = activities_response.json()[activity_name]["participants"]
        assert len(final_participants) == initial_count
        
        for email in emails:
            assert email not in final_participants

    def test_activities_data_persistence_across_requests(self, client: TestClient, reset_activities):
        """Test that activity data persists across multiple requests."""
        email = "persistent@mergington.edu"
        activity_name = "Chess Club"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Make multiple GET requests to ensure data persists
        for _ in range(3):
            activities_response = client.get("/activities")
            activities_data = activities_response.json()
            assert email in activities_data[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Make multiple GET requests to ensure removal persists
        for _ in range(3):
            activities_response = client.get("/activities")
            activities_data = activities_response.json()
            assert email not in activities_data[activity_name]["participants"]

    def test_concurrent_operations_same_activity(self, client: TestClient, reset_activities):
        """Test operations on the same activity."""
        activity_name = "Programming Class"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Sign up two different students to same activity
        response1 = client.post(f"/activities/{activity_name}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are registered
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants
        
        # Unregister one
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email1}")
        assert unregister_response.status_code == 200
        
        # Verify only one was removed
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 not in participants
        assert email2 in participants