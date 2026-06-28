import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the source directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the module to test
from src.utils import (
    format_date,
    validate_email,
    calculate_hash,
    sanitize_input,
    parse_config
)

class TestFormatDate:
    """Test cases for format_date function"""
    
    def test_format_date_standard(self):
        """Test standard date formatting"""
        result = format_date("2024-01-15")
        assert result == "January 15, 2024"
    
    def test_format_date_with_time(self):
        """Test date formatting with time component"""
        result = format_date("2024-01-15 14:30:00")
        assert result == "January 15, 2024"
    
    def test_format_date_invalid_input(self):
        """Test date formatting with invalid input"""
        with pytest.raises(ValueError):
            format_date("not-a-date")
    
    def test_format_date_empty_string(self):
        """Test date formatting with empty string"""
        with pytest.raises(ValueError):
            format_date("")
    
    def test_format_date_none_input(self):
        """Test date formatting with None input"""
        with pytest.raises(TypeError):
            format_date(None)
    
    def test_format_date_leap_year(self):
        """Test date formatting for leap year date"""
        result = format_date("2024-02-29")
        assert result == "February 29, 2024"
    
    def test_format_date_edge_case_january(self):
        """Test date formatting for first month"""
        result = format_date("2024-01-01")
        assert result == "January 1, 2024"
    
    def test_format_date_edge_case_december(self):
        """Test date formatting for last month"""
        result = format_date("2024-12-31")
        assert result == "December 31, 2024"


class TestValidateEmail:
    """Test cases for validate_email function"""
    
    def test_validate_email_valid(self):
        """Test valid email address"""
        assert validate_email("user@example.com") == True
    
    def test_validate_email_with_plus(self):
        """Test email with plus addressing"""
        assert validate_email("user+tag@example.com") == True
    
    def test_validate_email_with_dots(self):
        """Test email with dots in local part"""
        assert validate_email("first.last@example.com") == True
    
    def test_validate_email_subdomain(self):
        """Test email with subdomain"""
        assert validate_email("user@sub.example.com") == True
    
    def test_validate_email_no_at_symbol(self):
        """Test email without @ symbol"""
        assert validate_email("userexample.com") == False
    
    def test_validate_email_empty_string(self):
        """Test email validation with empty string"""
        assert validate_email("") == False
    
    def test_validate_email_no_domain(self):
        """Test email without domain"""
        assert validate_email("user@") == False
    
    def test_validate_email_no_local_part(self):
        """Test email without local part"""
        assert validate_email("@example.com") == False
    
    def test_validate_email_special_chars(self):
        """Test email with special characters"""
        assert validate_email("user.name+tag@example.co.uk") == True
    
    def test_validate_email_invalid_chars(self):
        """Test email with invalid characters"""
        assert validate_email("user name@example.com") == False


class TestCalculateHash:
    """Test cases for calculate_hash function"""
    
    def test_calculate_hash_string(self):
        """Test hash calculation for string input"""
        result = calculate_hash("hello")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hash length
    
    def test_calculate_hash_consistency(self):
        """Test that same input produces same hash"""
        input_data = "test_data"
        hash1 = calculate_hash(input_data)
        hash2 = calculate_hash(input_data)
        assert hash1 == hash2
    
    def test_calculate_hash_different_inputs(self):
        """Test that different inputs produce different hashes"""
        hash1 = calculate_hash("input1")
        hash2 = calculate_hash("input2")
        assert hash1 != hash2
    
    def test_calculate_hash_empty_string(self):
        """Test hash calculation for empty string"""
        result = calculate_hash("")
        assert isinstance(result, str)
        assert len(result) == 64
    
    def test_calculate_hash_none_input(self):
        """Test hash calculation with None input"""
        with pytest.raises(TypeError):
            calculate_hash(None)
    
    def test_calculate_hash_unicode(self):
        """Test hash calculation for unicode string"""
        result = calculate_hash("héllo wörld")
        assert isinstance(result, str)
        assert len(result) == 64
    
    def test_calculate_hash_numeric_input(self):
        """Test hash calculation for numeric input"""
        result = calculate_hash("12345")
        assert isinstance(result, str)
        assert len(result) == 64


class TestSanitizeInput:
    """Test cases for sanitize_input function"""
    
    def test_sanitize_input_remove_html_tags(self):
        """Test removal of HTML tags"""
        result = sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert('xss')" not in result
    
    def test_sanitize_input_escape_special_chars(self):
        """Test escaping of special characters"""
        result = sanitize_input("hello & world")
        assert "&amp;" in result or "&" not in result
    
    def test_sanitize_input_normal_text(self):
        """Test sanitization of normal text"""
        text = "Hello, World!"
        result = sanitize_input(text)
        assert result == text
    
    def test_sanitize_input_empty_string(self):
        """Test sanitization of empty string"""
        assert sanitize_input("") == ""
    
    def test_sanitize_input_none(self):
        """Test sanitization of None"""
        with pytest.raises(TypeError):
            sanitize_input(None)
    
    def test_sanitize_input_sql_injection_attempt(self):
        """Test sanitization of SQL injection attempt"""
        result = sanitize_input("'; DROP TABLE users; --")
        assert "'" not in result or result != "'; DROP TABLE users; --"
    
    def test_sanitize_input_unicode_chars(self):
        """Test sanitization of unicode characters"""
        result = sanitize_input("héllo wörld")
        assert result is not None
        assert isinstance(result, str)


class TestParseConfig:
    """Test cases for parse_config function"""
    
    def test_parse_config_valid_json(self):
        """Test parsing valid JSON config"""
        config_str = '{"key": "value", "number": 42}'
        result = parse_config(config_str)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_parse_config_valid_yaml(self):
        """Test parsing valid YAML config"""
        config_str = "key: value\nnumber: 42"
        result = parse_config(config_str)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_parse_config_empty_string(self):
        """Test parsing empty config string"""
        with pytest.raises(ValueError):
            parse_config("")
    
    def test_parse_config_invalid_format(self):
        """Test parsing invalid config format"""
        with pytest.raises(ValueError):
            parse_config("invalid config content")
    
    def test_parse_config_none_input(self):
        """Test parsing None config"""
        with pytest.raises(TypeError):
            parse_config(None)
    
    def test_parse_config_nested_structure(self):
        """Test parsing nested config structure"""
        config_str = '{"database": {"host": "localhost", "port": 5432}}'
        result = parse_config(config_str)
        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
    
    def test_parse_config_with_comments(self):
        """Test parsing config with comments"""
        config_str = "# This is a comment\nkey: value"
        result = parse_config(config_str)
        assert "key" in result