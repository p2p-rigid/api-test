import pytest
from pydantic import ValidationError
from app.api.v1.schemas.user_schemas import UserCreate, UserUpdate


class TestUsernameValidation:
    """Tests for username validation"""

    def test_valid_username_letters_only(self):
        """Username with only letters should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="JohnDoe",
            first_name="John",
            last_name="Doe",
            password="SecurePass1!"
        )
        assert user.username == "JohnDoe"

    def test_valid_username_with_numbers(self):
        """Username with letters and numbers should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="john123",
            first_name="John",
            last_name="Doe",
            password="SecurePass1!"
        )
        assert user.username == "john123"

    def test_valid_username_with_underscore(self):
        """Username with letters, numbers, and underscore should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="john_doe_123",
            first_name="John",
            last_name="Doe",
            password="SecurePass1!"
        )
        assert user.username == "john_doe_123"

    def test_invalid_username_starts_with_number(self):
        """Username starting with a number should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="1john",
                first_name="John",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "Username must start with a letter" in str(exc_info.value)

    def test_invalid_username_with_spaces(self):
        """Username with spaces should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="john doe",
                first_name="John",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "Username must start with a letter" in str(exc_info.value)

    def test_invalid_username_with_special_chars(self):
        """Username with special characters should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="john@doe",
                first_name="John",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "Username must start with a letter" in str(exc_info.value)

    def test_invalid_username_too_short(self):
        """Username that is too short should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="ab",
                first_name="John",
                last_name="Doe",
                password="SecurePass1!"
            )
        # Pydantic min_length validation will catch this
        assert "username" in str(exc_info.value).lower()

    def test_invalid_username_too_long(self):
        """Username that is too long should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="a" * 31,
                first_name="John",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "username" in str(exc_info.value).lower()


class TestPasswordValidation:
    """Tests for password validation"""

    def test_valid_password(self):
        """Password meeting all requirements should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="johndoe",
            first_name="John",
            last_name="Doe",
            password="SecurePass1!"
        )
        assert user.password == "SecurePass1!"

    def test_invalid_password_too_short(self):
        """Password shorter than 8 characters should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John",
                last_name="Doe",
                password="Pass1!"
            )
        assert "8 characters" in str(exc_info.value)

    def test_invalid_password_no_uppercase(self):
        """Password without uppercase letter should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John",
                last_name="Doe",
                password="securepass1!"
            )
        assert "uppercase" in str(exc_info.value)

    def test_invalid_password_no_lowercase(self):
        """Password without lowercase letter should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John",
                last_name="Doe",
                password="SECUREPASS1!"
            )
        assert "lowercase" in str(exc_info.value)

    def test_invalid_password_no_digit(self):
        """Password without digit should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John",
                last_name="Doe",
                password="SecurePass!"
            )
        assert "digit" in str(exc_info.value)

    def test_invalid_password_no_special_char(self):
        """Password without special character should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John",
                last_name="Doe",
                password="SecurePass1"
            )
        assert "special character" in str(exc_info.value)


class TestNameValidation:
    """Tests for first name and last name validation"""

    def test_valid_simple_name(self):
        """Simple name with only letters should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="johndoe",
            first_name="John",
            last_name="Doe",
            password="SecurePass1!"
        )
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_valid_name_with_hyphen(self):
        """Name with hyphen should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="johndoe",
            first_name="Mary-Jane",
            last_name="O'Connor",
            password="SecurePass1!"
        )
        assert user.first_name == "Mary-Jane"
        assert user.last_name == "O'Connor"

    def test_valid_name_with_apostrophe(self):
        """Name with apostrophe should be valid"""
        user = UserCreate(
            email="test@example.com",
            username="johndoe",
            first_name="Patrick",
            last_name="O'Brien",
            password="SecurePass1!"
        )
        assert user.last_name == "O'Brien"

    def test_name_strips_whitespace(self):
        """Name with leading/trailing spaces should be stripped"""
        user = UserCreate(
            email="test@example.com",
            username="johndoe",
            first_name="  John  ",
            last_name="  Doe  ",
            password="SecurePass1!"
        )
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_invalid_name_with_numbers(self):
        """Name with numbers should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John123",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "letters, hyphens, and apostrophes" in str(exc_info.value)

    def test_invalid_name_with_special_chars(self):
        """Name with special characters (other than hyphen/apostrophe) should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="John@Doe",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "letters, hyphens, and apostrophes" in str(exc_info.value)

    def test_invalid_name_empty(self):
        """Empty name should be invalid"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                username="johndoe",
                first_name="",
                last_name="Doe",
                password="SecurePass1!"
            )
        assert "first_name" in str(exc_info.value).lower()


class TestUserUpdateValidation:
    """Tests for UserUpdate schema validation"""

    def test_update_username_valid(self):
        """Valid username update should work"""
        update = UserUpdate(username="newusername")
        assert update.username == "newusername"

    def test_update_username_invalid(self):
        """Invalid username update should fail"""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(username="123invalid")
        assert "Username must start with a letter" in str(exc_info.value)

    def test_update_password_valid(self):
        """Valid password update should work"""
        update = UserUpdate(password="NewSecure1!")
        assert update.password == "NewSecure1!"

    def test_update_password_invalid(self):
        """Invalid password update should fail"""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(password="weak")
        assert "password" in str(exc_info.value).lower()

    def test_update_name_valid(self):
        """Valid name update should work"""
        update = UserUpdate(first_name="Jane", last_name="Smith")
        assert update.first_name == "Jane"
        assert update.last_name == "Smith"

    def test_update_name_invalid(self):
        """Invalid name update should fail"""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdate(first_name="Jane123")
        assert "letters, hyphens, and apostrophes" in str(exc_info.value)

    def test_update_none_values_allowed(self):
        """None values should be allowed for optional fields"""
        update = UserUpdate()
        assert update.username is None
        assert update.password is None
        assert update.first_name is None
        assert update.last_name is None
