import pytest
import os
import sys
from datetime import datetime, date
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import (
    User,
    Product,
    Order,
    DatabaseModel,
    ValidationError
)

class TestUser:
    """Test cases for User model"""
    
    @pytest.fixture
    def valid_user_data(self):
        return {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securePassword123!",
            "created_at": "2024-01-15T10:30:00Z"
        }
    
    def test_user_creation(self, valid_user_data):
        """Test user creation with valid data"""
        user = User(**valid_user_data)
        assert user.id == 1
        assert user.username == "john_doe"
        assert user.email == "john@example.com"
    
    def test_user_default_values(self):
        """Test user creation with default values"""
        user = User(username="test_user", email="test@example.com")
        assert user.is_active == True
        assert user.role == "user"
        assert user.created_at is not None
    
    def test_user_password_hashing(self, valid_user_data):
        """Test password hashing on creation"""
        user = User(**valid_user_data)
        assert user.password != "securePassword123!"
        assert user.password.startswith("$2b$")  # bcrypt hash prefix
    
    def test_user_verify_password(self, valid_user_data):
        """Test password verification"""
        user = User(**valid_user_data)
        assert user.verify_password("securePassword123!") == True
        assert user.verify_password("wrong_password") == False
    
    def test_user_invalid_email(self):
        """Test user creation with invalid email"""
        with pytest.raises(ValidationError):
            User(username="test", email="invalid-email")
    
    def test_user_short_username(self):
        """Test user creation with too short username"""
        with pytest.raises(ValidationError):
            User(username="ab", email="test@example.com")
    
    def test_user_to_dict(self, valid_user_data):
        """Test user serialization to dictionary"""
        user = User(**valid_user_data)
        user_dict = user.to_dict()
        assert user_dict["username"] == "john_doe"
        assert "password" not in user_dict  # Password should be excluded
    
    def test_user_string_representation(self, valid_user_data):
        """Test user string representation"""
        user = User(**valid_user_data)
        assert str(user) == "User(john_doe)"
        assert repr(user) == f"User(id=1, username='john_doe')"
    
    def test_user_update_profile(self, valid_user_data):
        """Test user profile update"""
        user = User(**valid_user_data)
        user.update_profile(email="newemail@example.com")
        assert user.email == "newemail@example.com"
    
    def test_user_deactivate(self, valid_user_data):
        """Test user deactivation"""
        user = User(**valid_user_data)
        user.deactivate()
        assert user.is_active == False
    
    def test_user_equality(self, valid_user_data):
        """Test user equality comparison"""
        user1 = User(**valid_user_data)
        user2 = User(**valid_user_data)
        user3 = User(id=2, username="jane_doe", email="jane@example.com")
        assert user1 == user2
        assert user1 != user3


class TestProduct:
    """Test cases for Product model"""
    
    @pytest.fixture
    def valid_product_data(self):
        return {
            "id": 1,
            "name": "Laptop",
            "price": 999.99,
            "category": "Electronics",
            "stock": 10,
            "description": "High-performance laptop"
        }
    
    def test_product_creation(self, valid_product_data):
        """Test product creation with valid data"""
        product = Product(**valid_product_data)
        assert product.name == "Laptop"
        assert product.price == 999.99
        assert product.stock == 10
    
    def test_product_negative_price(self):
        """Test product creation with negative price"""
        with pytest.raises(ValidationError):
            Product(name="Test", price=-10.0, category="Test")
    
    def test_product_zero_stock(self):
        """Test product creation with zero stock"""
        product = Product(name="Test", price=10.0, category="Test", stock=0)
        assert product.stock == 0
        assert product.is_available == False
    
    def test_product_negative_stock(self):
        """Test product creation with negative stock"""
        with pytest.raises(ValidationError):
            Product(name="Test", price=10.0, category="Test", stock=-5)
    
    def test_product_update_stock(self, valid_product_data):
        """Test product stock update"""
        product = Product(**valid_product_data)
        product.update_stock(5)
        assert product.stock == 15
    
    def test_product_insufficient_stock(self, valid_product_data):
        """Test product stock check"""
        product = Product(**valid_product_data)
        assert product.has_stock(5) == True
        assert product.has_stock(15) == False
    
    def test_product_apply_discount(self, valid_product_data):
        """Test product discount application"""
        product = Product(**valid_product_data)
        discounted_price = product.apply_discount(10)  # 10% discount
        assert discounted_price == 899.99
    
    def test_product_invalid_discount(self, valid_product_data):
        """Test product with invalid discount percentage"""
        product = Product(**valid_product_data)
        with pytest.raises(ValueError):
            product.apply_discount(-10)
        with pytest.raises(ValueError):
            product.apply_discount(110)
    
    def test_product_category_validation(self):
        """Test product category validation"""
        with pytest.raises(ValidationError):
            Product(name="Test", price=10.0, category="")
    
    def test_product_to_dict(self, valid_product_data):
        """Test product serialization"""
        product = Product(**valid_product_data)
        product_dict = product.to_dict()
        assert product_dict["name"] == "Laptop"
        assert "id" in product_dict


class TestOrder:
    """Test cases for Order model"""
    
    @pytest.fixture
    def valid_order_data(self):
        return {
            "id": 1,
            "user_id": 1,
            "products": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1}
            ],
            "status": "pending",
            "total_amount": 149.97
        }
    
    def test_order_creation(self, valid_order_data):
        """Test order creation with valid data"""
        order = Order(**valid_order_data)
        assert order.status == "pending"
        assert len(order.products) == 2
    
    def test_order_default_status(self):
        """Test order default status"""
        order = Order(user_id=1, products=[{"product_id": 1, "quantity": 1}])
        assert order.status == "pending"
    
    def test_order_status_transitions(self, valid_order_data):
        """Test order status transitions"""
        order = Order(**valid_order_data)
        
        assert order.update_status("confirmed") == True
        assert order.status == "confirmed"
        
        assert order.update_status("shipped") == True
        assert order.status == "shipped"
        
        assert order.update_status("delivered") == True
        assert order.status == "delivered"
    
    def test_order_invalid_status_transition(self, valid_order_data):
        """Test invalid order status transition"""
        order = Order(**valid_order_data)
        with pytest.raises(ValueError):
            order.update_status("delivered")  # Can't go from pending to delivered
    
    def test_order_calculation(self, valid_order_data):
        """Test order total calculation"""
        order = Order(**valid_order_data)
        calculated_total = order.calculate_total()
        assert calculated_total == valid_order_data["total_amount"]
    
    def test_order_empty_products(self):
        """Test order with no products"""
        with pytest.raises(ValidationError):
            Order(user_id=1, products=[])
    
    def test_order_cancel(self, valid_order_data):
        """Test order cancellation"""
        order = Order(**valid_order_data)
        assert order.cancel() == True
        assert order.status == "cancelled"
    
    def test_order_cancel_after_shipped(self, valid_order_data):
        """Test cancellation of shipped order"""
        order = Order(**valid_order_data)
        order.update_status("shipped")
        with pytest.raises(ValueError):
            order.cancel()
    
    def test_order_to_dict(self, valid_order_data):
        """Test order serialization"""
        order = Order(**valid_order_data)
        order_dict = order.to_dict()
        assert "user_id" in order_dict
        assert "products" in order_dict


class TestDatabaseModel:
    """Test cases for DatabaseModel base class"""
    
    def test_save_new_record(self):
        """Test saving a new record to database"""
        model = DatabaseModel()
        model.save()
        assert model.id is not None
    
    def test_update_existing_record(self):
        """Test updating an existing record"""
        model = DatabaseModel(id=1)
        model.save()
        assert model.id == 1
    
    def test_delete_record(self):
        """Test deleting a record"""
        model = DatabaseModel(id=1)
        assert model.delete() == True
    
    def test_find_by_id(self):
        """Test finding record by ID"""
        result = DatabaseModel.find_by_id(1)
        assert result is not None
        assert result.id == 1
    
    def test_find_by_id_not_found(self):
        """Test finding non-existent record"""
        result = DatabaseModel.find_by_id(999)
        assert result is None
    
    def test_find_all(self):
        """Test finding all records"""
        results = DatabaseModel.find_all()
        assert isinstance(results, list)
    
    def test_find_with_filters(self):
        """Test finding records with filters"""
        filters = {"status": "active"}
        results = DatabaseModel.find_with_filters(filters)
        assert isinstance(results, list)
    
    def test_count_records(self):
        """Test counting records"""
        count = DatabaseModel.count()
        assert isinstance(count, int)
        assert count >= 0
    
    def test_bulk_save(self):
        """Test bulk saving records"""
        models = [DatabaseModel(), DatabaseModel(), DatabaseModel()]
        result = DatabaseModel.bulk_save(models)
        assert result == True