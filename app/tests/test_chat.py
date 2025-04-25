"""
Tests for the chat API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_get_current_user():
    """Fixture to mock the get_current_user dependency."""
    with patch('app.api.chat.get_current_user', return_value={"id": "test_id", "email": "test@example.com"}):
        yield

@pytest.fixture
def sample_clinical_trials_data():
    """Sample clinical trials data for testing."""
    return [
        {
            "nctId": "NCT01234567",
            "briefTitle": "Test Trial 1",
            "organization": "Test Org 1",
            "overallStatus": "COMPLETED",
            "conditions": "Test Condition 1",
            "interventionDrug": "Test Drug 1",
            "eligibilityCriteria": "Test Criteria 1",
            "primaryOutcomes": "Test Outcome 1",
            "secondaryOutcomes": "Test Secondary 1"
        },
        {
            "nctId": "NCT89012345",
            "briefTitle": "Test Trial 2",
            "organization": "Test Org 2",
            "overallStatus": "RECRUITING",
            "conditions": "Test Condition 2",
            "interventionDrug": "Test Drug 2",
            "eligibilityCriteria": "Test Criteria 2",
            "primaryOutcomes": "Test Outcome 2",
            "secondaryOutcomes": "Test Secondary 2"
        }
    ]

@pytest.fixture
def sample_fda_data():
    """Sample FDA data for testing."""
    return [
        {
            "brand_name": "Test Brand 1",
            "generic_name": "Test Generic 1",
            "manufacturer_name": "Test Manufacturer 1",
            "application_number": "Test App 1",
            "indications_and_usage": "Test Indications 1",
            "dosage_and_administration": "Test Dosage 1",
            "warnings_and_cautions": "Test Warnings 1",
            "adverse_reactions": "Test Reactions 1"
        },
        {
            "brand_name": "Test Brand 2",
            "generic_name": "Test Generic 2",
            "manufacturer_name": "Test Manufacturer 2",
            "application_number": "Test App 2",
            "indications_and_usage": "Test Indications 2",
            "dosage_and_administration": "Test Dosage 2",
            "warnings_and_cautions": "Test Warnings 2",
            "adverse_reactions": "Test Reactions 2"
        }
    ]

def test_chat_success(mock_get_current_user, sample_clinical_trials_data, sample_fda_data):
    """Test successful chat request."""
    # Mock the process_chat_query function
    with patch('app.api.chat.process_chat_query', return_value=("Test response", [{"type": "clinical_trial", "id": "NCT01234567", "title": "Test Trial 1"}])):
        
        # Test request
        response = client.post(
            "/api/chat",
            headers={"Authorization": "Bearer test_token"},
            json={
                "query": "What trials are available?",
                "clinical_trials_data": sample_clinical_trials_data,
                "fda_data": sample_fda_data,
                "chat_history": []
            }
        )
        
        # Assertions
        assert response.status_code == 200
        assert "response" in response.json()
        assert "sources" in response.json()
        assert response.json()["response"] == "Test response"
        assert len(response.json()["sources"]) == 1
        assert response.json()["sources"][0]["id"] == "NCT01234567"

def test_chat_no_data(mock_get_current_user):
    """Test chat request with no data."""
    # Mock the process_chat_query function
    with patch('app.api.chat.process_chat_query', return_value=("No data available to answer your question.", [])):
        
        # Test request
        response = client.post(
            "/api/chat",
            headers={"Authorization": "Bearer test_token"},
            json={
                "query": "What trials are available?",
                "clinical_trials_data": [],
                "fda_data": [],
                "chat_history": []
            }
        )
        
        # Assertions
        assert response.status_code == 200
        assert "response" in response.json()
        assert "sources" in response.json()
        assert response.json()["response"] == "No data available to answer your question."
        assert len(response.json()["sources"]) == 0

def test_chat_error(mock_get_current_user, sample_clinical_trials_data, sample_fda_data):
    """Test chat request with an error."""
    # Mock the process_chat_query function to raise an exception
    with patch('app.api.chat.process_chat_query', side_effect=Exception("Test error")):
        
        # Test request
        response = client.post(
            "/api/chat",
            headers={"Authorization": "Bearer test_token"},
            json={
                "query": "What trials are available?",
                "clinical_trials_data": sample_clinical_trials_data,
                "fda_data": sample_fda_data,
                "chat_history": []
            }
        )
        
        # Assertions
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Test error" in response.json()["detail"]

def test_chat_unauthorized():
    """Test chat request without authentication."""
    # Test request without auth header
    response = client.post(
        "/api/chat",
        json={
            "query": "What trials are available?",
            "clinical_trials_data": [],
            "fda_data": [],
            "chat_history": []
        }
    )
    
    # Assertions
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Not authenticated" in response.json()["detail"]
