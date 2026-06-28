import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api import app, get_db
from src.models import User, Product, Order

# Create test client
client = TestClient(app)

class TestHealthEndpoint:
    """Test cases for health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_response(self):
        """Test health check response structure"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_check_db_connection(self):
        """Test health check verifies database connection"""
        response = client.get("/health")
        data = response.json()
        assert "database" in data
        assert data["database"] == "connected"


class TestUserEndpoints:
    """Test cases for user API endpoints"""
    
    @pytest.fixture
    def valid_user_payload(self):
        return {
            "username": "new_user",
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }
    
    def test_create_user(self, valid_user_payload):
        """Test user creation endpoint"""
        response = client.post("/api/users/", json=valid_user_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == valid_user_payload["username"]
        assert "id" in data
    
    def test_create_user_duplicate_username(self, valid_user_payload):
        """Test creating user with existing username"""
        client.post("/api/users/", json=valid_user_payload)
        response = client.post("/api/users/", json=valid_user_payload)
        assert response.status_code == 409
    
    def test_create_user_invalid_email(self):
        """Test creating user with invalid email"""
        payload = {
            "username": "test_user",
            "email": "invalid-email",
            "password": "SecurePass123!"
        }
        response = client.post("/api/users/", json=payload)
        assert response.status_code == 422
    
    def test_create_user_weak_password(self):
        """Test creating user with weak password"""
        payload = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "123"
        }
        response = client.post("/api/users/", json=payload)
        assert response.status_code == 422
    
    def test_get_user(self):
        """Test get user by ID endpoint"""
        # First create a user
        create_response = client.post("/api/users/", json={
            "username": "get_test_user",
            "email": "gettest@example.com",
            "password": "SecurePass123!"
        })
        user_id = create_response.json()["id"]
        
        # Then get the user
        response = client.get(f"/api/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["username"] == "get_test_user"
    
    def test_get_user_not_found(self):
        """Test get non-existent user"""
        response = client.get("/api/users/99999")
        assert response.status_code == 404
    
    def test_update_user(self):
        """Test update user endpoint"""
        # Create user
        create_response = client.post("/api/users/", json={
            "username": "update_test",
            "email": "update@example.com",
            "password": "SecurePass123!"
        })
        user_id = create_response.json()["id"]
        
        # Update user
        response = client.put(f"/api/users/{user_id}", json={
            "email": "updated@example.com"
        })
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"
    
    def test_delete_user(self):
        """Test delete user endpoint"""
        # Create user
        create_response = client.post("/api/users/", json={
            "username": "delete_test",
            "email": "delete@example.com",
            "password": "SecurePass123!"
        })
        user_id = create_response.json()["id"]
        
        # Delete user
        response = client.delete(f"/api/users/{user_id}")
        assert response.status_code == 204
    
    def test_list_users(self):
        """Test list users endpoint"""
        response = client.get("/api/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_users_with_pagination(self):
        """Test list users with pagination"""
        response = client.get("/api/users/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10


class TestProductEndpoints:
    """Test cases for product API endpoints"""
    
    @pytest.fixture
    def valid_product_payload(self):
        return {
            "name": "Test Product",
            "price": 29.99,
            "category": "Electronics",
            "stock": 100,
            "description": "A test product"
        }
    
    def test_create_product(self, valid_product_payload):
        """Test product creation endpoint"""
        response = client.post("/api/products/", json=valid_product_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == valid_product_payload["name"]
    
    def test_create_product_invalid_price(self):
        """Test creating product with negative price"""
        payload = {
            "name": "Test",
            "price": -10.0,
            "category": "Test"
        }
        response = client.post("/api/products/", json=payload)
        assert response.status_code == 422
    
    def test_get_product(self, valid_product_payload):
        """Test get product by ID"""
        create_response = client.post("/api/products/", json=valid_product_payload)
        product_id = create_response.json()["id"]
        
        response = client.get(f"/api/products/{product_id}")
        assert response.status_code == 200
    
    def test_get_product_not_found(self):
        """Test get non-existent product"""
        response = client.get("/api/products/99999")
        assert response.status_code == 404
    
    def test_update_product_stock(self, valid_product_payload):
        """Test updating product stock"""
        create_response = client.post("/api/products/", json=valid_product_payload)
        product_id = create_response.json()["id"]
        
        response = client.patch(f"/api/products/{product_id}/stock", json={"quantity": 50})
        assert response.status_code == 200
        assert response.json()["stock"] == 150
    
    def test_search_products(self):
        """Test product search endpoint"""
        response = client.get("/api/products/search?q=laptop")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_filter_products_by_category(self):
        """Test filtering products by category"""
        response = client.get("/api/products/?category=Electronics")
        assert response.status_code == 200
        for product in response.json():
            assert product["category"] == "Electronics"


class TestOrderEndpoints:
    """Test cases for order API endpoints"""
    
    @pytest.fixture
    def valid_order_payload(self):
        return {
            "user_id": 1,
            "products": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ]
        }
    
    def test_create_order(self, valid_order_payload):
        """Test order creation endpoint"""
        response = client.post("/api/orders/", json=valid_order_payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
    
    def test_create_order_insufficient_stock(self):
        """Test creating order with insufficient stock"""
        payload = {
            "user_id": 1,
            "products": [{"product_id": 1, "quantity": 9999}]
        }
        response = client.post("/api/orders/", json=payload)
        assert response.status_code == 400
    
    def test_get_order(self, valid_order_payload):
        """Test get order by ID"""
        create_response = client.post("/api/orders/", json=valid_order_payload)
        order_id = create_response.json()["id"]
        
        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
    
    def test_get_order_not_found(self):
        """Test get non-existent order"""
        response = client.get("/api/orders/99999")
        assert response.status_code == 404
    
    def test_update_order_status(self, valid_order_payload):
        """Test updating order status"""
        create_response = client.post("/api/orders/", json=valid_order_payload)
        order_id = create_response.json()["id"]
        
        response = client.patch(f"/api/orders/{order_id}/status", json={"status": "confirmed"})
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
    
    def test_cancel_order(self, valid_order_payload):
        """Test cancelling an order"""
        create_response = client.post("/api/orders/", json=valid_order_payload)
        order_id = create_response.json()["id"]
        
        response = client.post(f"/api/orders/{order_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_get_user_orders(self):
        """Test getting orders for a specific user"""
        response = client.get("/api/users/1/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAuthentication:
    """Test cases for authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post("/api/auth/login", json={
            "username": "wronguser",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_register_user(self):
        """Test user registration"""
        response = client.post("/api/auth/register", json={
            "username": "newregister",
            "email": "register@example.com",
            "password": "SecurePass123!"
        })
        assert response.status_code == 201
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/protected/users")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/api/protected/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
    
    def test_refresh_token(self):
        """Test token refresh"""
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        response = client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestErrorHandling:
    """Test cases for API error handling"""
    
    def test_404_error(self):
        """Test 404 error response"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_422_validation_error(self):
        """Test validation error response"""
        response = client.post("/api/users/", json={"invalid": "data"})
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_500_internal_error(self):
        """Test internal server error handling"""
        with patch("src.api.get_db", side_effect=Exception("DB Error")):
            response = client.get("/api/users/")
            assert response.status_code == 500
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        for _ in range(100):
            client.get("/health")
        
        response = client.get("/health")
        assert response.status_code == 429