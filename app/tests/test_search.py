"""
Tests for the search API endpoints.
"""
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_get_current_user():
    """Fixture to mock the get_current_user dependency."""
    with patch('app.api.search.get_current_user', return_value={"id": "test_id", "email": "test@example.com"}):
        yield

@pytest.fixture
def mock_clinical_trials_data():
    """Fixture to mock the clinical trials data."""
    mock_data = pd.DataFrame({
        'nctId': ['NCT01234567', 'NCT89012345'],
        'briefTitle': ['Test Trial 1', 'Test Trial 2'],
        'organization': ['Test Org 1', 'Test Org 2'],
        'overallStatus': ['COMPLETED', 'RECRUITING'],
        'conditions': ['Test Condition 1', 'Test Condition 2'],
        'interventionDrug': ['Test Drug 1', 'Test Drug 2'],
        'eligibilityCriteria': ['Test Criteria 1', 'Test Criteria 2'],
        'primaryOutcomes': ['Test Outcome 1', 'Test Outcome 2'],
        'secondaryOutcomes': ['Test Secondary 1', 'Test Secondary 2']
    })
    return mock_data

@pytest.fixture
def mock_fda_data():
    """Fixture to mock the FDA data."""
    mock_data = pd.DataFrame({
        'brand_name': ['Test Brand 1', 'Test Brand 2'],
        'generic_name': ['Test Generic 1', 'Test Generic 2'],
        'manufacturer_name': ['Test Manufacturer 1', 'Test Manufacturer 2'],
        'application_number': ['Test App 1', 'Test App 2'],
        'indications_and_usage': ['Test Indications 1', 'Test Indications 2'],
        'dosage_and_administration': ['Test Dosage 1', 'Test Dosage 2'],
        'warnings_and_cautions': ['Test Warnings 1', 'Test Warnings 2'],
        'adverse_reactions': ['Test Reactions 1', 'Test Reactions 2']
    })
    return mock_data

def test_search_success(mock_get_current_user, mock_clinical_trials_data, mock_fda_data):
    """Test successful search."""
    # Mock the data fetching functions
    with patch('app.api.search.get_clinical_trials_data', return_value=mock_clinical_trials_data), \
         patch('app.api.search.Open_FDA.open_fda_main', return_value=mock_fda_data):
        
        # Test request
        response = client.post(
            "/api/search",
            headers={"Authorization": "Bearer test_token"},
            json={"keyword": "test", "domain": "disease"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert "clinical_trials" in response.json()
        assert "fda_data" in response.json()
        assert len(response.json()["clinical_trials"]) == 2
        assert len(response.json()["fda_data"]) == 2
        assert response.json()["total_clinical_trials"] == 2
        assert response.json()["total_fda_data"] == 2

def test_search_no_results(mock_get_current_user):
    """Test search with no results."""
    # Mock the data fetching functions to return empty DataFrames
    with patch('app.api.search.get_clinical_trials_data', return_value=pd.DataFrame()), \
         patch('app.api.search.Open_FDA.open_fda_main', return_value=pd.DataFrame()):
        
        # Test request
        response = client.post(
            "/api/search",
            headers={"Authorization": "Bearer test_token"},
            json={"keyword": "nonexistent", "domain": "disease"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert "clinical_trials" in response.json()
        assert "fda_data" in response.json()
        assert len(response.json()["clinical_trials"]) == 0
        assert len(response.json()["fda_data"]) == 0
        assert response.json()["total_clinical_trials"] == 0
        assert response.json()["total_fda_data"] == 0

def test_search_error(mock_get_current_user):
    """Test search with an error."""
    # Mock the data fetching function to raise an exception
    with patch('app.api.search.get_clinical_trials_data', side_effect=Exception("Test error")):
        
        # Test request
        response = client.post(
            "/api/search",
            headers={"Authorization": "Bearer test_token"},
            json={"keyword": "test", "domain": "disease"}
        )
        
        # Assertions
        assert response.status_code == 500
        assert "detail" in response.json()
        assert "Test error" in response.json()["detail"]

def test_search_unauthorized():
    """Test search without authentication."""
    # Test request without auth header
    response = client.post(
        "/api/search",
        json={"keyword": "test", "domain": "disease"}
    )
    
    # Assertions
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Not authenticated" in response.json()["detail"]
