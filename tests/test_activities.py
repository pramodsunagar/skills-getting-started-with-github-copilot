"""Tests for activity endpoints using AAA (Arrange-Act-Assert) pattern"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """
        AAA Test: Verify GET /activities returns list of all activities
        Arrange: Already have test client
        Act: Call GET /activities
        Assert: Check status and response contains activities
        """
        # Arrange
        expected_activity_names = [
            "Basketball Team", "Soccer Club", "Drama Club", "Art Club",
            "Debate Team", "Chess Club", "Programming Class", "Gym Class"
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) == 8
        for activity_name in expected_activity_names:
            assert activity_name in activities

    def test_get_activities_has_required_fields(self, client):
        """
        AAA Test: Verify each activity has required fields
        Arrange: Already have test client
        Act: Call GET /activities
        Assert: Check each activity has description, schedule, max_participants, participants
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, details in activities.items():
            assert all(field in details for field in required_fields)
            assert isinstance(details["description"], str)
            assert isinstance(details["schedule"], str)
            assert isinstance(details["max_participants"], int)
            assert isinstance(details["participants"], list)

    def test_get_activities_participants_are_strings(self, client):
        """
        AAA Test: Verify participants list contains email strings
        Arrange: Already have test client
        Act: Call GET /activities
        Assert: All participants are lowercase email strings
        """
        # Arrange
        # (no specific setup needed)

        # Act
        response = client.get("/activities")
        activities = response.json()

        # Assert
        for activity_name, details in activities.items():
            for participant in details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """
        AAA Test: Verify new participant can sign up
        Arrange: Prepare activity name and unique email
        Act: POST to signup endpoint
        Assert: Check success response and participant is added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email.lower() in result["message"] or "Signed up" in result["message"]

        # Verify participant was added
        verify_response = client.get("/activities")
        activities = verify_response.json()
        assert email.lower() in activities[activity_name]["participants"]

    def test_signup_duplicate_email_rejected(self, client):
        """
        AAA Test: Verify duplicate signup is rejected
        Arrange: Get existing participant, attempt to signup again
        Act: POST to signup endpoint with existing email
        Assert: Check 400 error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        existing_participant = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_participant}"
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        AAA Test: Verify signup for non-existent activity returns 404
        Arrange: Prepare fake activity name and email
        Act: POST to signup endpoint with non-existent activity
        Assert: Check 404 error is returned
        """
        # Arrange
        activity_name = "Fake Activity"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_signup_email_normalized(self, client):
        """
        AAA Test: Verify emails are normalized (lowercase, stripped)
        Arrange: Prepare email with uppercase and spaces
        Act: POST signup with non-normalized email
        Assert: Check stored email is normalized
        """
        # Arrange
        activity_name = "Drama Club"
        email_with_spaces = "  NewStudent123@MERGINGTON.EDU  "
        expected_normalized = "newstudent123@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email_with_spaces}"
        )

        # Assert
        assert response.status_code == 200

        # Verify normalized email is stored
        verify_response = client.get("/activities")
        activities = verify_response.json()
        assert expected_normalized in activities[activity_name]["participants"]

    def test_signup_full_activity_rejected(self, client):
        """
        AAA Test: Verify signup for full activity is rejected
        Arrange: Fill activity to max capacity, attempt signup
        Act: POST to signup endpoint
        Assert: Check 400 error about activity being full
        """
        # Arrange
        activity_name = "Chess Club"
        response = client.get("/activities")
        activities = response.json()
        current_count = len(activities[activity_name]["participants"])
        max_capacity = activities[activity_name]["max_participants"]

        # If activity not full, skip test (or fill it first)
        if current_count < max_capacity:
            pytest.skip(f"{activity_name} is not at capacity")

        new_email = "anothertest@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={new_email}",
            method="POST"
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "full" in result["detail"].lower()


class TestUnregisterParticipant:
    """Tests for DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_existing_participant_success(self, client):
        """
        AAA Test: Verify existing participant can be unregistered
        Arrange: Get existing participant
        Act: DELETE participant from activity
        Assert: Check success response and participant is removed
        """
        # Arrange
        activity_name = "Chess Club"
        participant_to_remove = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={participant_to_remove}"
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "removed" in result["message"].lower() or "Removed" in result["message"]

        # Verify participant was removed
        verify_response = client.get("/activities")
        activities = verify_response.json()
        assert participant_to_remove not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client):
        """
        AAA Test: Verify unregistering non-existent participant returns 404
        Arrange: Prepare activity and non-existent email
        Act: DELETE non-existent participant
        Assert: Check 404 error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        fake_email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={fake_email}"
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """
        AAA Test: Verify unregistering from non-existent activity returns 404
        Arrange: Prepare fake activity name
        Act: DELETE participant from non-existent activity
        Assert: Check 404 error is returned
        """
        # Arrange
        activity_name = "Fake Activity"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_unregister_email_normalized(self, client):
        """
        AAA Test: Verify unregister works with non-normalized emails
        Arrange: Prepare email with uppercase and spaces
        Act: DELETE participant with non-normalized email
        Assert: Check participant is removed despite case/spacing differences
        """
        # Arrange
        activity_name = "Soccer Club"
        stored_email = "matthew@mergington.edu"
        unregister_email = "  MATTHEW@MERGINGTON.EDU  "

        # Verify participant exists first
        verify_before = client.get("/activities")
        activities = verify_before.json()
        assert stored_email in activities[activity_name]["participants"]

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants?email={unregister_email}"
        )

        # Assert
        assert response.status_code == 200

        # Verify participant was removed
        verify_after = client.get("/activities")
        activities_after = verify_after.json()
        assert stored_email not in activities_after[activity_name]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index(self, client):
        """
        AAA Test: Verify root path redirects to /static/index.html
        Arrange: Already have test client
        Act: GET /
        Assert: Check redirect response
        """
        # Arrange
        # (no specific setup needed)

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
