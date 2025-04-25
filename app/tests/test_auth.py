"""
Tests for the authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_httpx_client():
    """Fixture to mock httpx.AsyncClient."""
    with patch('app.api.auth.httpx.AsyncClient') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value.__aenter__.return_value = mock_instance
        yield mock_instance

def test_register_success(mock_httpx_client):
    """Test successful user registration."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_token",
        "user": {
            "id": "test_id",
            "email": "test@example.com",
            "created_at": "2023-01-01T00:00:00Z"
        }
    }
    mock_httpx_client.post.return_value = mock_response
    
    # Test request
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # Assertions
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["access_token"] == "test_token"
    assert response.json()["user"]["email"] == "test@example.com"

def test_register_failure(mock_httpx_client):
    """Test failed user registration."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Registration failed"
    mock_httpx_client.post.return_value = mock_response
    
    # Test request
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # Assertions
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Registration failed" in response.json()["detail"]

def test_login_success(mock_httpx_client):
    """Test successful user login."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "test_token",
        "user": {
            "id": "test_id",
            "email": "test@example.com",
            "created_at": "2023-01-01T00:00:00Z"
        }
    }
    mock_httpx_client.post.return_value = mock_response
    
    # Test request
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    # Assertions
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["access_token"] == "test_token"
    assert response.json()["user"]["email"] == "test@example.com"

def test_login_failure(mock_httpx_client):
    """Test failed user login."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Invalid credentials"
    mock_httpx_client.post.return_value = mock_response
    
    # Test request
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrong_password"}
    )
    
    # Assertions
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Invalid credentials" in response.json()["detail"]

def test_logout_success(mock_httpx_client):
    """Test successful user logout."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.post.return_value = mock_response
    
    # Mock get_current_user
    with patch('app.api.auth.get_current_user', return_value={"id": "test_id", "email": "test@example.com"}):
        # Test request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert "message" in response.json()
        assert "Successfully logged out" in response.json()["message"]

def test_logout_failure(mock_httpx_client):
    """Test failed user logout."""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Logout failed"
    mock_httpx_client.post.return_value = mock_response
    
    # Mock get_current_user
    with patch('app.api.auth.get_current_user', return_value={"id": "test_id", "email": "test@example.com"}):
        # Test request
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Assertions
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Logout failed" in response.json()["detail"]
