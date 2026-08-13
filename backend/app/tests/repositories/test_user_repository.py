"""
User repository tests.
"""

import pytest
from app.models import User


@pytest.mark.unit
class TestUserRepository:
    """Tests for UserRepository CRUD operations."""

    def test_create_user(self, user_repo, db_session):
        """Test creating a new user."""
        user = User(
            email="newuser@example.com",
            password_hash="hashed_pwd",
            full_name="New User",
        )
        created = user_repo.create(user)
        assert created.id is not None
        assert created.email == "newuser@example.com"

        # Verify persisted
        retrieved = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_user_by_id(self, user_repo, sample_user):
        """Test retrieving user by ID."""
        retrieved = user_repo.get_by_id(sample_user.id)
        assert retrieved is not None
        assert retrieved.email == sample_user.email

    def test_get_user_by_email(self, user_repo, sample_user):
        """Test retrieving user by email."""
        retrieved = user_repo.get_by_email(sample_user.email)
        assert retrieved is not None
        assert retrieved.id == sample_user.id

    def test_get_nonexistent_user(self, user_repo):
        """Test retrieving non-existent user returns None."""
        retrieved = user_repo.get_by_id("nonexistent_id")
        assert retrieved is None

    def test_update_user(self, user_repo, sample_user):
        """Test updating user fields."""
        updated = user_repo.update(sample_user.id, {"full_name": "Updated Name"})
        assert updated is not None
        assert updated.full_name == "Updated Name"
        assert updated.email == sample_user.email  # unchanged

    def test_update_nonexistent_user(self, user_repo):
        """Test updating non-existent user returns None."""
        result = user_repo.update("nonexistent_id", {"full_name": "New Name"})
        assert result is None

    def test_delete_user(self, user_repo, sample_user):
        """Test deleting a user."""
        result = user_repo.delete(sample_user.id)
        assert result is True

        # Verify deleted
        retrieved = user_repo.get_by_id(sample_user.id)
        assert retrieved is None

    def test_delete_nonexistent_user(self, user_repo):
        """Test deleting non-existent user returns False."""
        result = user_repo.delete("nonexistent_id")
        assert result is False

    def test_list_users(self, user_repo, db_session):
        """Test listing users with pagination."""
        # Create multiple users
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                password_hash=f"pwd{i}",
                full_name=f"User {i}",
            )
            db_session.add(user)
        db_session.commit()

        # List first 3
        users = user_repo.list(skip=0, limit=3)
        assert len(users) == 3

        # List next 2
        users = user_repo.list(skip=3, limit=2)
        assert len(users) == 2

    def test_list_by_filter(self, user_repo, db_session, sample_user):
        """Test listing users by filter."""
        users = user_repo.list_by_filter({"email": sample_user.email})
        assert len(users) == 1
        assert users[0].id == sample_user.id
